import os
import pathlib
import ffmpeg
from uuid import uuid4
import requests # For downloading video

from backend.infrastructure.repositories.database import get_task_session
from backend.infrastructure.repositories.sqlite_video_repo import SQLiteVideoRepository
from backend.infrastructure.repositories.sqlite_caption_repo import SQLiteCaptionRepository
from backend.infrastructure.adapters.file_storage_adapter import FileSystemStorageAdapter
from backend.application.use_cases.generate_captions import GenerateCaptionsUseCase
from backend.domain.entities.video import VideoStatus, Video

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

    with get_task_session() as session:
        video_repo = SQLiteVideoRepository(session)
        video = None

        try:
            video = video_repo.get_by_id(video_id)
            if not video:
                print(f"Video with id {video_id} not found. Exiting processing.")
                return

            # Mark video as PROCESSING
            video = video.mark_as_processing()
            video_repo.update(video)
            session.commit()

            # --- Video Transcoding ---
            input_path = UPLOAD_DIR / uploaded_file_path
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

            # Transcode video
            print(f"Transcoding {input_path} to {processed_video_path}")
            (
                ffmpeg
                .input(str(input_path))
                .output(str(processed_video_path), vcodec='libx264', acodec='aac', preset='veryfast', vf='scale=640:-1', y=None)
                .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
            )

            # Generate thumbnail
            print(f"Generating thumbnail at {thumbnail_path}")
            (
                ffmpeg
                .input(str(input_path), ss='00:00:01')
                .output(str(thumbnail_path), vframes=1, y=None)
                .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
            )

            # Store the paths/URLs relative to the /uploads mount point
            processed_video_url = f"/uploads/{processed_video_filename}"
            thumbnail_url = f"/uploads/thumbnails/{thumbnail_filename}"

            # Update video status and URLs
            video = video.mark_as_ready(url=processed_video_url, thumbnail_url=thumbnail_url, duration=duration)
            video_repo.update(video)
            session.commit()

            print(f"Video {video_id} processed successfully. URL: {processed_video_url}, Thumbnail: {thumbnail_url}")

            # Delete the original uploaded file to save space
            os.remove(input_path)
            print(f"Original uploaded file {input_path} deleted.")

        except FileNotFoundError as e:
            print(f"Error processing video {video_id}: {e}")
            if video:
                video = video.mark_as_failed()
                video_repo.update(video)
                session.commit()
        except ffmpeg.Error as e:
            print(f"FFmpeg error processing video {video_id}: stdout={e.stdout}, stderr={e.stderr}")
            if video:
                video = video.mark_as_failed()
                video_repo.update(video)
                session.commit()
        except Exception as e:
            print(f"An unexpected error occurred during video processing for {video_id}: {e}")
            if video:
                video = video.mark_as_failed()
                video_repo.update(video)
                session.commit()

def generate_captions_task(video_id: str):
    """
    RQ task to generate captions for a given video.
    Downloads the processed video, extracts audio, transcribes, and saves captions.
    """
    print(f"Starting caption generation for video_id: {video_id}")

    downloaded_video_path = None
    audio_file_path = None

    with get_task_session() as session:
        video_repo = SQLiteVideoRepository(session)
        caption_repo = SQLiteCaptionRepository(session)

        try:
            video = video_repo.get_by_id(video_id)
            if not video or not video.url:
                print(f"Video {video_id} not found or has no URL. Exiting caption generation.")
                return

            # 1. Download the processed video locally
            backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
            video_url_full = f"{backend_url}{video.url}"
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
            generated_captions = generate_captions_use_case.execute(video_id, str(audio_file_path))

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