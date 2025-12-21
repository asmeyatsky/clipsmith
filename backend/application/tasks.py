import os
import pathlib
import ffmpeg
from uuid import uuid4
import requests # For downloading video

from backend.infrastructure.repositories.database import get_session
from backend.infrastructure.repositories.sqlite_video_repo import SQLiteVideoRepository
from backend.infrastructure.adapters.file_storage_adapter import FileSystemStorageAdapter
from backend.domain.entities.video import VideoStatus
from backend.domain.entities.video import Video

# Define the upload directory. This should ideally come from a settings module.
# For now, we'll hardcode it based on the project structure.
UPLOAD_DIR = pathlib.Path(__file__).parent.parent.parent / "uploads"
THUMBNAIL_DIR = UPLOAD_DIR / "thumbnails"
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

def process_video_task(video_id: str, uploaded_file_path: str):
    """
    RQ task to process an uploaded video: transcode, generate thumbnail, and update status.
    """
    print(f"Starting video processing for video_id: {video_id} from {uploaded_file_path}")
    
    video_repo = None # Initialize to None for finally block
    try:
        # Repositories and adapters should be instantiated within the task
        # or passed as arguments if using a dependency injection system.
        # For RQ, instantiating inside the task is common.
        session_generator = get_session()
        session = next(session_generator) # Get the session
        video_repo = SQLiteVideoRepository(session)
        file_storage_adapter = FileSystemStorageAdapter(base_url="/uploads") # Use relative URL base

        video = video_repo.get_by_id(video_id)
        if not video:
            print(f"Video with id {video_id} not found. Exiting processing.")
            return

        # Mark video as PROCESSING
        video = video.mark_as_processing()
        video_repo.update(video)
        session.commit() # Commit status change

        # --- Video Transcoding ---
        input_path = UPLOAD_DIR / uploaded_file_path # Original uploaded file
        if not input_path.exists():
            raise FileNotFoundError(f"Uploaded file not found at {input_path}")

        # Define output paths for processed video and thumbnail
        file_stem = input_path.stem
        processed_video_filename = f"{file_stem}_processed.mp4"
        thumbnail_filename = f"{file_stem}_thumbnail.jpg"

        processed_video_path = UPLOAD_DIR / processed_video_filename
        thumbnail_path = THUMBNAIL_DIR / thumbnail_filename

        # Get video duration using ffprobe
        print(f"Probing {input_path} for metadata...")
        probe = ffmpeg.probe(str(input_path))
        duration = float(probe['format']['duration'])
        print(f"Video duration: {duration} seconds")
        
        # Ffmpeg command to transcode video and generate thumbnail
        print(f"Transcoding {input_path} to {processed_video_path}")
        # -y to overwrite output files without asking
        # -preset veryfast for quicker processing (can be adjusted)
        # -vf scale=640:-1 sets video width to 640px, maintaining aspect ratio
        # -ss 00:00:01 to grab thumbnail at 1 second mark
        # -vframes 1 to grab only one frame for thumbnail
        (
            ffmpeg
            .input(str(input_path))
            .output(str(processed_video_path), vcodec='libx264', acodec='aac', preset='veryfast', vf='scale=640:-1', y=None)
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True) # Run to transcode
        )
        print(f"Generated thumbnail for {input_path} at {thumbnail_path}")
        (
            ffmpeg
            .input(str(input_path), ss='00:00:01') # Grab frame at 1 second
            .output(str(thumbnail_path), vframes=1, y=None)
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True) # Run to generate thumbnail
        )
        
        # Store the paths/URLs relative to the /uploads mount point
        processed_video_url = f"/uploads/{processed_video_filename}"
        thumbnail_url = f"/uploads/thumbnails/{thumbnail_filename}"

        # Update video status and URLs
        video = video.mark_as_ready(url=processed_video_url, thumbnail_url=thumbnail_url, duration=duration)
        video_repo.update(video)
        session.commit() # Commit final status and URLs

        print(f"Video {video_id} processed successfully. URL: {processed_video_url}, Thumbnail: {thumbnail_url}")

        # Optionally, delete the original uploaded file to save space
        os.remove(input_path)
        print(f"Original uploaded file {input_path} deleted.")

    except FileNotFoundError as e:
        print(f"Error processing video {video_id}: {e}")
        if video_repo and video:
            video = video.mark_as_failed()
            video_repo.update(video)
            session.commit()
    except ffmpeg.Error as e:
        print(f"FFmpeg error processing video {video_id}: stdout={e.stdout}, stderr={e.stderr}")
        if video_repo and video:
            video = video.mark_as_failed()
            video_repo.update(video)
            session.commit()
    except Exception as e:
        print(f"An unexpected error occurred during video processing for {video_id}: {e}")
        if video_repo and video:
            video = video.mark_as_failed()
            video_repo.update(video)
            session.commit()
    finally:
        # Ensure session is closed if it was opened
        if 'session_generator' in locals():
            try:
                next(session_generator) # Advance generator to close session
            except StopIteration:
                pass # Generator is exhausted, session was closed.

from backend.infrastructure.repositories.sqlite_caption_repo import SQLiteCaptionRepository
from backend.application.use_cases.generate_captions import GenerateCaptionsUseCase
from backend.domain.entities.video import Video # Import Video entity if not already

# Modify this task to download video, extract audio, and then generate captions
def generate_captions_task(video_id: str): # Modified signature
    """
    RQ task to generate captions for a given video.
    Downloads the processed video, extracts audio, transcribes, and saves captions.
    """
    print(f"Starting caption generation for video_id: {video_id}")

    video_repo = None
    caption_repo = None
    downloaded_video_path = None
    audio_file_path = None

    try:
        session_generator = get_session()
        session = next(session_generator)
        video_repo = SQLiteVideoRepository(session)
        caption_repo = SQLiteCaptionRepository(session)

        video = video_repo.get_by_id(video_id)
        if not video or not video.url:
            print(f"Video {video_id} not found or has no URL. Exiting caption generation.")
            return
        
        # 1. Download the processed video locally
        # NOTE: This assumes the backend server is accessible from where the RQ worker is running
        #       For Docker setups, this might need to be 'http://backend:8000' or similar
        video_url_full = f"http://localhost:8000{video.url}"
        downloaded_video_path = UPLOAD_DIR / f"{uuid4()}_downloaded_for_caption.mp4"
        print(f"Downloading video from {video_url_full} to {downloaded_video_path}")
        response = requests.get(video_url_full, stream=True)
        response.raise_for_status()
        with open(downloaded_video_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Video downloaded to {downloaded_video_path}")

        # 2. Extract audio from the downloaded video
        audio_file_path = UPLOAD_DIR / f"{uuid4()}_extracted_audio.mp3"
        print(f"Extracting audio to {audio_file_path}")
        (
            ffmpeg
            .input(str(downloaded_video_path))
            .output(str(audio_file_path), acodec='mp3', y=None)
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
        print(f"Audio extracted to {audio_file_path}")

        # 3. Generate captions using the use case
        generate_captions_use_case = GenerateCaptionsUseCase(video_repo, caption_repo)
        generated_captions = generate_captions_use_case.execute(video_id, str(audio_file_path)) # Pass audio path to use case
        
        print(f"Captions generated for video {video_id}: {len(generated_captions)} captions.")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading video for caption generation {video_id}: {e}")
    except FileNotFoundError as e:
        print(f"File not found during caption generation for {video_id}: {e}")
    except ffmpeg.Error as e:
        print(f"FFmpeg error during audio extraction for caption generation {video_id}: stdout={e.stdout}, stderr={e.stderr}")
    except Exception as e:
        print(f"An unexpected error occurred during caption generation for {video_id}: {e}")
    finally:
        # Clean up temporary files
        if downloaded_video_path and downloaded_video_path.exists():
            os.remove(downloaded_video_path)
            print(f"Cleaned up downloaded video: {downloaded_video_path}")
        if audio_file_path and audio_file_path.exists():
            os.remove(audio_file_path)
            print(f"Cleaned up extracted audio: {audio_file_path}")
        
        # Ensure session is closed
        if 'session_generator' in locals():
            try:
                next(session_generator)
            except StopIteration:
                pass