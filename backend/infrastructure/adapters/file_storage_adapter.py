import os
import shutil
from typing import BinaryIO
from ...domain.ports.storage_port import StoragePort

UPLOAD_DIR = "backend/uploads"

class FileSystemStorageAdapter(StoragePort):
    def __init__(self, base_url: str = "http://localhost:8001/uploads"):
        self.base_url = base_url
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

    async def save(self, file_name: str, file_data: BinaryIO) -> str:
        file_path = os.path.join(UPLOAD_DIR, file_name)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file_data, buffer)
        
        return self.get_url(file_name)

    def get_url(self, file_name: str) -> str:
        return f"{self.base_url}/{file_name}"
