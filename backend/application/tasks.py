import os
import pathlib
import ffmpeg
from uuid import uuid4
import requests
import json
import logging
from typing import Dict, List, Optional, Tuple

from ..infrastructure.repositories.database import get_task_session
from ..infrastructure.repositories.sqlite_video_repo import SQLiteVideoRepository
from ..infrastructure.repositories.sqlite_caption_repo import SQLiteCaptionRepository
from ..infrastructure.adapters.storage_factory import get_storage_adapter
from ..application.use_cases.generate_captions import GenerateCaptionsUseCase
from ..domain.entities.video import VideoStatus, Video


def _safe_parse_frame_rate(rate_str: str) -> float:
    """Safely parse ffprobe frame rate strings like '30/1' or '29.97'."""
    try:
        if '/' in rate_str:
            num, den = rate_str.split('/', 1)
            denominator = float(den)
            if denominator == 0:
                return 0.0
            return float(num) / denominator
        return float(rate_str)
    except (ValueError, ZeroDivisionError):
        return 0.0


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define upload directory for local processing.
# For S3, files are processed locally first then uploaded.
UPLOAD_DIR = pathlib.Path(__file__).parent.parent.parent / "uploads"
THUMBNAIL_DIR = UPLOAD_DIR / "thumbnails"
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

# Get storage adapter for cloud storage operations
storage_adapter = get_storage_adapter()

# Video processing configurations
VIDEO_RESOLUTIONS = {
    "360p": {"width": 640, "height": 360, "bitrate": "500k"},
    "720p": {"width": 1280, "height": 720, "bitrate": "1500k"},
    "1080p": {"width": 1920, "height": 1080, "bitrate": "3000k"},
}


def get_video_metadata(file_path: str) -> Dict:
    """Extract comprehensive video metadata using ffprobe."""
    try:
        probe = ffmpeg.probe(file_path)
        format_info = probe.get("format", {})
        video_stream = next(
            (
                stream
                for stream in probe.get("streams", [])
                if stream.get("codec_type") == "video"
            ),
            None,
        )
        audio_stream = next(
            (
                stream
                for stream in probe.get("streams", [])
                if stream.get("codec_type") == "audio"
            ),
            None,
        )

        metadata = {
            "duration": float(format_info.get("duration", 0)),
            "size": int(format_info.get("size", 0)),
            "format": format_info.get("format_name", ""),
            "video_codec": video_stream.get("codec_name", "") if video_stream else "",
            "audio_codec": audio_stream.get("codec_name", "") if audio_stream else "",
            "width": int(video_stream.get("width", 0)) if video_stream else 0,
            "height": int(video_stream.get("height", 0)) if video_stream else 0,
            "fps": _safe_parse_frame_rate(video_stream.get("r_frame_rate", "0/1")) if video_stream else 0,
            "bitrate": int(format_info.get("bit_rate", 0))
            if format_info.get("bit_rate")
            else 0,
        }

        return metadata
    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
        return {}


def generate_thumbnail_at_time(
    input_path: str, output_path: str, timestamp: str = "00:00:01"
) -> bool:
    """Generate thumbnail at specific timestamp."""
    try:
        (
            ffmpeg.input(input_path, ss=timestamp)
            .output(output_path, vframes=1, format="image2", vcodec="mjpeg")
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return True
    except ffmpeg.Error as e:
        logger.error(f"Error generating thumbnail: {e.stderr.decode()}")
        return False


def transcode_video(input_path: str, output_path: str, resolution: Dict) -> bool:
    """Transcode video to specific resolution."""
    try:
        input_stream = ffmpeg.input(input_path)
        bitrate_num = int(resolution["bitrate"][:-1])
        output_stream = ffmpeg.output(
            input_stream,
            output_path,
            vcodec="libx264",
            acodec="aac",
            preset="veryfast",
            vf=f"scale={resolution['width']}:{resolution['height']}",
            b_v=resolution["bitrate"],
            maxrate=f"{bitrate_num * 1.5}k",
            bufsize=f"{bitrate_num * 3}k",
            movflags="faststart",
        )
        ffmpeg.run(
            output_stream,
            overwrite_output=True,
            capture_stdout=True,
            capture_stderr=True,
        )
        return True
    except ffmpeg.Error as e:
        logger.error(f"Error transcoding video: {e.stderr.decode()}")
        return False


def upload_to_storage(local_path: str, remote_key: str) -> bool:
    """Upload processed file to cloud storage."""
    try:
        with open(local_path, "rb") as file_data:
            storage_adapter.save(remote_key, file_data)
        logger.info(f"Successfully uploaded {remote_key} to cloud storage")
        return True
    except Exception as e:
        logger.error(f"Error uploading {remote_key} to cloud storage: {e}")
        return False


def process_video_task(video_id: str, uploaded_file_path: str):
    """
    Enhanced RQ task to process an uploaded video:
    - Extract metadata
    - Generate multiple resolutions
    - Create thumbnails at multiple timestamps
    - Optimize for web delivery
    """
    logger.info(
        f"Starting enhanced video processing for video_id: {video_id} from {uploaded_file_path}"
    )

    with get_task_session() as session:
        video_repo = SQLiteVideoRepository(session)
        video = None

        try:
            video = video_repo.get_by_id(video_id)
            if not video:
                logger.error(f"Video with id {video_id} not found. Exiting processing.")
                return

            # Mark video as PROCESSING
            video = video.mark_as_processing()
            video_repo.save(video)
            session.commit()

            # --- Enhanced Video Processing ---
            input_path = UPLOAD_DIR / uploaded_file_path
            if not input_path.exists():
                raise FileNotFoundError(f"Uploaded file not found at {input_path}")

            # Extract comprehensive metadata
            logger.info(f"Extracting metadata from {input_path}...")
            metadata = get_video_metadata(str(input_path))
            if not metadata:
                raise ValueError("Failed to extract video metadata")

            duration = metadata.get("duration", 0)
            logger.info(f"Video metadata: {json.dumps(metadata, indent=2)}")

            file_stem = input_path.stem

            # Generate multiple thumbnails at different timestamps
            thumbnail_timestamps = [
                "00:00:01",
                "00:00:05",
                str(duration * 0.25),
                str(duration * 0.5),
            ]
            thumbnail_urls = []

            for i, timestamp in enumerate(thumbnail_timestamps):
                if float(timestamp) <= duration:
                    thumbnail_filename = f"{file_stem}_thumb_{i}.jpg"
                    thumbnail_path = THUMBNAIL_DIR / thumbnail_filename

                    if generate_thumbnail_at_time(
                        str(input_path), str(thumbnail_path), timestamp
                    ):
                        # Upload to cloud storage
                        remote_key = f"thumbnails/{thumbnail_filename}"
                        if upload_to_storage(str(thumbnail_path), remote_key):
                            thumbnail_url = storage_adapter.get_url(remote_key)
                        else:
                            thumbnail_url = (
                                f"/uploads/thumbnails/{thumbnail_filename}"  # Fallback
                            )

                        thumbnail_urls.append(thumbnail_url)

                        # Clean up local file
                        os.remove(thumbnail_path)

            # Transcode to multiple resolutions for adaptive streaming
            resolution_urls = {}
            original_height = metadata.get("height", 0)

            # Determine which resolutions to generate based on original quality
            target_resolutions = []
            if original_height >= 1080:
                target_resolutions = ["1080p", "720p", "360p"]
            elif original_height >= 720:
                target_resolutions = ["720p", "360p"]
            else:
                target_resolutions = ["360p"]

            for res_name in target_resolutions:
                res_config = VIDEO_RESOLUTIONS[res_name]
                processed_filename = f"{file_stem}_{res_name}.mp4"
                processed_path = UPLOAD_DIR / processed_filename

                if transcode_video(str(input_path), str(processed_path), res_config):
                    # Upload to cloud storage
                    remote_key = processed_filename
                    if upload_to_storage(str(processed_path), remote_key):
                        resolution_urls[res_name] = storage_adapter.get_url(remote_key)
                    else:
                        resolution_urls[res_name] = (
                            f"/uploads/{processed_filename}"  # Fallback
                        )

                    # Clean up local file
                    os.remove(processed_path)

            # Use the highest quality as main video URL, others for adaptive streaming
            main_video_url = resolution_urls.get(target_resolutions[0], "")
            main_thumbnail_url = thumbnail_urls[0] if thumbnail_urls else ""

            # Update video with all processed information
            video = video.mark_as_ready(
                url=main_video_url, thumbnail_url=main_thumbnail_url, duration=duration
            )
            video_repo.save(video)
            session.commit()

            logger.info(
                f"Video {video_id} processed successfully with {len(resolution_urls)} resolutions and {len(thumbnail_urls)} thumbnails"
            )

            # Delete the original uploaded file to save space
            os.remove(input_path)
            logger.info(f"Original uploaded file {input_path} deleted.")

        except Exception as e:
            logger.error(f"Error during video processing for {video_id}: {e}")
            if video:
                video = video.mark_as_failed()
                video_repo.save(video)
                session.commit()


def generate_captions_task(video_id: str):
    """
    Enhanced RQ task to generate captions for a given video.
    Downloads the processed video, extracts audio, transcribes, and saves captions.
    """
    logger.info(f"Starting caption generation for video_id: {video_id}")

    downloaded_video_path = None
    audio_file_path = None

    with get_task_session() as session:
        video_repo = SQLiteVideoRepository(session)
        caption_repo = SQLiteCaptionRepository(session)

        try:
            video = video_repo.get_by_id(video_id)
            if not video or not video.url:
                logger.warning(
                    f"Video {video_id} not found or has no URL. Exiting caption generation."
                )
                return

            # 1. Download the processed video locally
            backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
            video_url_full = f"{backend_url}{video.url}"
            downloaded_video_path = UPLOAD_DIR / f"{uuid4()}_downloaded_for_caption.mp4"
            logger.info(
                f"Downloading video from {video_url_full} to {downloaded_video_path}"
            )

            response = requests.get(video_url_full, stream=True, timeout=30)
            response.raise_for_status()

            with open(downloaded_video_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Video downloaded to {downloaded_video_path}")

            # 2. Extract high-quality audio from the downloaded video
            audio_file_path = UPLOAD_DIR / f"{uuid4()}_extracted_audio.wav"
            logger.info(f"Extracting audio to {audio_file_path}")

            (
                ffmpeg.input(str(downloaded_video_path))
                .output(str(audio_file_path), acodec="pcm_s16le", ac=1, ar="16000")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            logger.info(f"Audio extracted to {audio_file_path}")

            # 3. Generate captions using the use case
            generate_captions_use_case = GenerateCaptionsUseCase(
                video_repo, caption_repo
            )
            generated_captions = generate_captions_use_case.execute(
                video_id, str(audio_file_path)
            )

            logger.info(
                f"Captions generated for video {video_id}: {len(generated_captions)} captions."
            )

        except Exception as e:
            logger.error(f"Error during caption generation for {video_id}: {e}")
        finally:
            # Clean up temporary files
            if downloaded_video_path and downloaded_video_path.exists():
                os.remove(downloaded_video_path)
                logger.debug(f"Cleaned up downloaded video: {downloaded_video_path}")
            if audio_file_path and audio_file_path.exists():
                os.remove(audio_file_path)
                logger.debug(f"Cleaned up extracted audio: {audio_file_path}")
