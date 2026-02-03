import os
import logging
from typing import BinaryIO, Optional
from urllib.parse import quote
from ...domain.ports.storage_port import StoragePort
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class S3StorageAdapter(StoragePort):
    """AWS S3 storage adapter for production-ready file storage."""

    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: str = "us-east-1",
        cloudfront_domain: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):
        self.bucket_name = bucket_name
        self.aws_region = aws_region
        self.cloudfront_domain = cloudfront_domain

        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=aws_secret_access_key
                or os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=aws_region,
                endpoint_url=endpoint_url
                or os.getenv("AWS_ENDPOINT_URL"),  # For S3-compatible services
            )

            # Test connection
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"Successfully connected to S3 bucket: {bucket_name}")

        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS credentials.")
            raise
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.error(f"S3 bucket {bucket_name} not found.")
                raise
            else:
                logger.error(f"Error connecting to S3: {e}")
                raise

    def save(self, file_name: str, file_data: BinaryIO) -> str:
        """Save file to S3 and return the file key."""
        try:
            # Reset file pointer to beginning
            file_data.seek(0)

            # Determine content type based on file extension
            content_type = self._get_content_type(file_name)

            # Upload to S3 with proper metadata
            self.s3_client.upload_fileobj(
                file_data,
                self.bucket_name,
                file_name,
                ExtraArgs={
                    "ContentType": content_type,
                    "ACL": "public-read",  # Make files publicly accessible
                    "Metadata": {
                        "original-name": file_name,
                        "uploaded-by": "clipsmith",
                    },
                },
            )

            logger.info(f"Successfully uploaded {file_name} to S3")
            return file_name

        except ClientError as e:
            logger.error(f"Error uploading {file_name} to S3: {e}")
            raise

    def get_url(self, file_name: str) -> str:
        """Get public URL for a file."""
        if self.cloudfront_domain:
            # Use CloudFront CDN if configured
            return f"https://{self.cloudfront_domain}/{quote(file_name)}"
        else:
            # Use direct S3 URL
            return f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{quote(file_name)}"

    def delete(self, file_path: str) -> bool:
        """Delete file from S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)
            logger.info(f"Successfully deleted {file_path} from S3")
            return True
        except ClientError as e:
            logger.error(f"Error deleting {file_path} from S3: {e}")
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

    def generate_presigned_url(
        self, file_name: str, expiration: int = 3600
    ) -> Optional[str]:
        """Generate a presigned URL for private file access."""
        try:
            return self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": file_name},
                ExpiresIn=expiration,
            )
        except ClientError as e:
            logger.error(f"Error generating presigned URL for {file_name}: {e}")
            return None

    def copy_file(self, source_key: str, destination_key: str) -> bool:
        """Copy a file within S3."""
        try:
            copy_source = {"Bucket": self.bucket_name, "Key": source_key}
            self.s3_client.copy_object(
                CopySource=copy_source, Bucket=self.bucket_name, Key=destination_key
            )
            logger.info(f"Successfully copied {source_key} to {destination_key}")
            return True
        except ClientError as e:
            logger.error(f"Error copying file: {e}")
            return False

    def file_exists(self, file_name: str) -> bool:
        """Check if file exists in S3."""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=file_name)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            logger.error(f"Error checking file existence: {e}")
            return False
