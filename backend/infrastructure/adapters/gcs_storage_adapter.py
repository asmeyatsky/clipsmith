"""
Google Cloud Storage adapter for Clipsmith.

Provides file storage using Google Cloud Storage buckets.
Requires the google-cloud-storage package and appropriate credentials.
"""

import os
import logging
from typing import BinaryIO, Optional
from urllib.parse import quote
from ...domain.ports.storage_port import StoragePort

logger = logging.getLogger(__name__)


class GCSStorageAdapter(StoragePort):
    """Google Cloud Storage adapter for production-ready file storage."""

    def __init__(
        self,
        bucket_name: str,
        project_id: Optional[str] = None,
        credentials_path: Optional[str] = None,
        cdn_domain: Optional[str] = None,
    ):
        self.bucket_name = bucket_name
        self.cdn_domain = cdn_domain

        try:
            from google.cloud import storage as gcs_storage

            # Configure credentials
            if credentials_path:
                self.client = gcs_storage.Client.from_service_account_json(
                    credentials_path, project=project_id
                )
            elif project_id:
                self.client = gcs_storage.Client(project=project_id)
            else:
                # Uses default credentials (GOOGLE_APPLICATION_CREDENTIALS env var
                # or Application Default Credentials)
                self.client = gcs_storage.Client()

            self.bucket = self.client.bucket(bucket_name)

            # Verify bucket exists
            if not self.bucket.exists():
                logger.error(f"GCS bucket {bucket_name} not found.")
                raise ValueError(f"GCS bucket {bucket_name} does not exist")

            logger.info(f"Successfully connected to GCS bucket: {bucket_name}")

        except ImportError:
            logger.error(
                "google-cloud-storage package not installed. "
                "Install it with: pip install google-cloud-storage"
            )
            raise
        except Exception as e:
            logger.error(f"Error connecting to GCS: {e}")
            raise

    def save(self, file_name: str, file_data: BinaryIO) -> str:
        """Save file to GCS and return the file key."""
        try:
            file_data.seek(0)

            blob = self.bucket.blob(file_name)
            content_type = self._get_content_type(file_name)
            blob.upload_from_file(file_data, content_type=content_type)

            # Make publicly accessible
            blob.make_public()

            logger.info(f"Successfully uploaded {file_name} to GCS")
            return file_name

        except Exception as e:
            logger.error(f"Error uploading {file_name} to GCS: {e}")
            raise

    def get_url(self, file_name: str) -> str:
        """Get public URL for a file."""
        if self.cdn_domain:
            return f"https://{self.cdn_domain}/{quote(file_name)}"
        else:
            return f"https://storage.googleapis.com/{self.bucket_name}/{quote(file_name)}"

    def delete(self, file_path: str) -> bool:
        """Delete file from GCS."""
        try:
            blob = self.bucket.blob(file_path)
            blob.delete()
            logger.info(f"Successfully deleted {file_path} from GCS")
            return True
        except Exception as e:
            logger.error(f"Error deleting {file_path} from GCS: {e}")
            return False

    def _get_content_type(self, file_name: str) -> str:
        """Determine content type based on file extension."""
        content_types = {
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
            ".avi": "video/x-msvideo",
            ".webm": "video/webm",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".pdf": "application/pdf",
            ".txt": "text/plain",
        }

        _, ext = os.path.splitext(file_name.lower())
        return content_types.get(ext, "application/octet-stream")

    def generate_signed_url(
        self, file_name: str, expiration: int = 3600
    ) -> Optional[str]:
        """Generate a signed URL for private file access."""
        try:
            import datetime

            blob = self.bucket.blob(file_name)
            return blob.generate_signed_url(
                expiration=datetime.timedelta(seconds=expiration),
                method="GET",
            )
        except Exception as e:
            logger.error(f"Error generating signed URL for {file_name}: {e}")
            return None

    def file_exists(self, file_name: str) -> bool:
        """Check if file exists in GCS."""
        try:
            blob = self.bucket.blob(file_name)
            return blob.exists()
        except Exception as e:
            logger.error(f"Error checking file existence: {e}")
            return False
