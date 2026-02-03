import os
import logging
from typing import Union
from .file_storage_adapter import FileSystemStorageAdapter
from .s3_storage_adapter import S3StorageAdapter
from ...domain.ports.storage_port import StoragePort

logger = logging.getLogger(__name__)


def create_storage_adapter() -> StoragePort:
    """Factory function to create appropriate storage adapter based on environment."""

    storage_type = os.getenv("STORAGE_TYPE", "local").lower()

    if storage_type == "s3":
        logger.info("Initializing S3 storage adapter")

        required_env_vars = [
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "S3_BUCKET_NAME",
        ]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]

        if missing_vars:
            logger.error(f"Missing required S3 environment variables: {missing_vars}")
            raise ValueError(f"Missing environment variables: {missing_vars}")

        return S3StorageAdapter(
            bucket_name=os.getenv("S3_BUCKET_NAME"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            cloudfront_domain=os.getenv("CLOUDFRONT_DOMAIN"),
            endpoint_url=os.getenv(
                "AWS_ENDPOINT_URL"
            ),  # For testing with localstack/minio
        )

    elif storage_type == "local":
        logger.info("Initializing local filesystem storage adapter")
        base_url = os.getenv("STORAGE_BASE_URL", "http://localhost:8000/uploads")
        return FileSystemStorageAdapter(base_url=base_url)

    else:
        logger.error(
            f"Unknown storage type: {storage_type}. Supported types: 'local', 's3'"
        )
        raise ValueError(f"Unsupported storage type: {storage_type}")


# Singleton instance for the application
storage_adapter: Union[StoragePort, None] = None


def get_storage_adapter() -> StoragePort:
    """Get the singleton storage adapter instance."""
    global storage_adapter
    if storage_adapter is None:
        storage_adapter = create_storage_adapter()
    return storage_adapter
