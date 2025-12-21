from ...domain.ports.repository_ports import VideoRepositoryPort, CaptionRepositoryPort
from ...domain.entities.caption import Caption
from ..dtos.caption_dto import CaptionResponseDTO
from typing import List
import assemblyai as aai
import os # For environment variable

class GenerateCaptionsUseCase:
    def __init__(self, video_repo: VideoRepositoryPort, caption_repo: CaptionRepositoryPort):
        self._video_repo = video_repo
        self._caption_repo = caption_repo

    def execute(self, video_id: str, audio_file_path: str) -> List[CaptionResponseDTO]:
        video = self._video_repo.get_by_id(video_id)
        if not video:
            raise ValueError(f"Video with ID {video_id} not found.")
        # if not video.url: # This check is now redundant as audio_file_path is directly provided
        #     raise ValueError(f"Video with ID {video_id} is not processed yet.")

        # AssemblyAI API Key from environment variable
        aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
        if not aai.settings.api_key:
            raise ValueError("ASSEMBLYAI_API_KEY environment variable not set.")

        transcriber = aai.Transcriber()
        # You might want to define a specific configuration for the transcription
        config = aai.TranscriptionConfig(
            # speaker_labels=True, # Example advanced feature
            # auto_chapters=True, # Example advanced feature
            word_boost=["clipsmith", "video", "editing"], # Example word boost
        )

        print(f"Starting AssemblyAI transcription for audio: {audio_file_path}")
        transcript = transcriber.transcribe(audio_file_path, config=config)
        print(f"AssemblyAI transcription status: {transcript.status}")

        if transcript.status == aai.TranscriptStatus.error:
            raise ValueError(f"AssemblyAI transcription failed: {transcript.error}")

        generated_captions = []
        if transcript.words: # Use words to get precise timings for captions
            current_caption_text = ""
            current_start_time = 0.0
            for word_info in transcript.words:
                # Simple logic: group words into captions, could be more sophisticated
                if not current_caption_text:
                    current_start_time = word_info.start / 1000.0 # Convert ms to seconds
                
                current_caption_text += word_info.text + " "

                # Decide when to create a new caption segment
                # For simplicity, create a caption for every few words or at sentence end
                # A more advanced approach would use VTT/SRT segmenting logic
                if len(current_caption_text.split()) >= 5 or word_info.text.endswith(('.', '?', '!')):
                    end_time = word_info.end / 1000.0
                    caption = Caption(
                        video_id=video_id,
                        text=current_caption_text.strip(),
                        start_time=current_start_time,
                        end_time=end_time,
                        language="en" # AssemblyAI usually detects, but hardcoding for now
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
