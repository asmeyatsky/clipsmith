import os
import pathlib
import ffmpeg
from uuid import uuid4

from backend.infrastructure.repositories.database import get_session
from backend.infrastructure.repositories.sqlite_video_repo import SQLiteVideoRepository
from backend.infrastructure.adapters.file_storage_adapter import FileSystemStorageAdapter
from backend.domain.entities.video import VideoStatus
from backend.domain.entities.video import Video
# from backend.application.dtos.video_dto import VideoCreateDTO # Assuming this exists or can be created

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
        video = video.mark_as_ready(url=processed_video_url, thumbnail_url=thumbnail_url)
        video_repo.update(video)
        session.commit() # Commit final status and URLs

        print(f"Video {video_id} processed successfully. URL: {processed_video_url}, Thumbnail: {thumbnail_url}")

        # Optionally, delete the original uploaded file to save space
        # os.remove(input_path)
        # print(f"Original uploaded file {input_path} deleted.")

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