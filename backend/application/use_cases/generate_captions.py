from ...domain.ports.repository_ports import VideoRepositoryPort, CaptionRepositoryPort
from ...domain.entities.caption import Caption
from ..dtos.caption_dto import CaptionResponseDTO
from typing import List
import os
import logging

logger = logging.getLogger(__name__)


class GenerateCaptionsUseCase:
    def __init__(self, video_repo: VideoRepositoryPort, caption_repo: CaptionRepositoryPort):
        self._video_repo = video_repo
        self._caption_repo = caption_repo

    def execute(self, video_id: str, audio_file_path: str) -> List[CaptionResponseDTO]:
        video = self._video_repo.get_by_id(video_id)
        if not video:
            raise ValueError(f"Video with ID {video_id} not found.")

        api_key = os.getenv("ASSEMBLYAI_API_KEY")
        environment = os.getenv("ENVIRONMENT", "development")

        # Use mock/placeholder captions in development when no API key is configured
        if not api_key or api_key in ("", "your-assemblyai-api-key"):
            if environment == "production":
                raise ValueError(
                    "ASSEMBLYAI_API_KEY environment variable not set. "
                    "This is required in production."
                )

            logger.warning(
                "ASSEMBLYAI_API_KEY not configured. "
                "Generating placeholder captions for development."
            )
            return self._generate_placeholder_captions(video_id, audio_file_path)

        return self._generate_assemblyai_captions(video_id, audio_file_path, api_key)

    def _generate_assemblyai_captions(
        self, video_id: str, audio_file_path: str, api_key: str
    ) -> List[CaptionResponseDTO]:
        """Generate captions using AssemblyAI transcription service."""
        import assemblyai as aai

        aai.settings.api_key = api_key

        transcriber = aai.Transcriber()
        config = aai.TranscriptionConfig(
            word_boost=["clipsmith", "video", "editing"],
        )

        logger.info(f"Starting AssemblyAI transcription for audio: {audio_file_path}")
        transcript = transcriber.transcribe(audio_file_path, config=config)
        logger.info(f"AssemblyAI transcription status: {transcript.status}")

        if transcript.status == aai.TranscriptStatus.error:
            raise ValueError(f"AssemblyAI transcription failed: {transcript.error}")

        generated_captions = []
        if transcript.words:
            current_caption_text = ""
            current_start_time = 0.0
            for word_info in transcript.words:
                if not current_caption_text:
                    current_start_time = word_info.start / 1000.0

                current_caption_text += word_info.text + " "

                if len(current_caption_text.split()) >= 5 or word_info.text.endswith(('.', '?', '!')):
                    end_time = word_info.end / 1000.0
                    caption = Caption(
                        video_id=video_id,
                        text=current_caption_text.strip(),
                        start_time=current_start_time,
                        end_time=end_time,
                        language="en"
                    )
                    saved_caption = self._caption_repo.save(caption)
                    generated_captions.append(CaptionResponseDTO(
                        id=saved_caption.id,
                        video_id=saved_caption.video_id,
                        text=saved_caption.text,
                        start_time=saved_caption.start_time,
                        end_time=saved_caption.end_time,
                        language=saved_caption.language
                    ))
                    current_caption_text = ""
                    current_start_time = 0.0

            # Add any remaining words as a caption
            if current_caption_text:
                caption = Caption(
                    video_id=video_id,
                    text=current_caption_text.strip(),
                    start_time=current_start_time,
                    end_time=transcript.words[-1].end / 1000.0,
                    language="en"
                )
                saved_caption = self._caption_repo.save(caption)
                generated_captions.append(CaptionResponseDTO(
                    id=saved_caption.id,
                    video_id=saved_caption.video_id,
                    text=saved_caption.text,
                    start_time=saved_caption.start_time,
                    end_time=saved_caption.end_time,
                    language=saved_caption.language
                ))
        return generated_captions

    def _generate_placeholder_captions(
        self, video_id: str, audio_file_path: str
    ) -> List[CaptionResponseDTO]:
        """Generate placeholder captions for development/testing.

        Attempts to read the audio duration via ffprobe; falls back to a
        default 30-second duration if ffprobe is unavailable.
        """
        duration = 30.0  # default fallback
        try:
            import ffmpeg
            probe = ffmpeg.probe(audio_file_path)
            duration = float(probe.get("format", {}).get("duration", 30.0))
        except Exception:
            logger.debug("Could not probe audio duration, using default 30s")

        placeholder_texts = [
            "This is a placeholder caption for development.",
            "AssemblyAI integration is not configured.",
            "Set ASSEMBLYAI_API_KEY in your environment to enable real captions.",
            "These captions are automatically generated for testing.",
            "The actual caption service will produce accurate transcriptions.",
        ]

        generated_captions = []
        segment_duration = duration / len(placeholder_texts)

        for i, text in enumerate(placeholder_texts):
            start_time = i * segment_duration
            end_time = (i + 1) * segment_duration

            if end_time > duration:
                break

            caption = Caption(
                video_id=video_id,
                text=text,
                start_time=round(start_time, 3),
                end_time=round(end_time, 3),
                language="en"
            )
            saved_caption = self._caption_repo.save(caption)
            generated_captions.append(CaptionResponseDTO(
                id=saved_caption.id,
                video_id=saved_caption.video_id,
                text=saved_caption.text,
                start_time=saved_caption.start_time,
                end_time=saved_caption.end_time,
                language=saved_caption.language
            ))

        logger.info(
            f"Generated {len(generated_captions)} placeholder captions "
            f"for video {video_id}"
        )
        return generated_captions
