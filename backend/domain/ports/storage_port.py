from abc import ABC, abstractmethod
from typing import BinaryIO

class StoragePort(ABC):
    @abstractmethod
    def save(self, file_name: str, file_data: BinaryIO) -> str:
        """
        Saves the file and returns the public URL or path.
        """
        pass

    @abstractmethod
    def get_url(self, file_name: str) -> str:
        """
        Returns the public URL for a given file name.
        """
        pass

    @abstractmethod
    def delete(self, file_path: str) -> bool:
        """
        Deletes the file at the given path. Returns True if successful.
        """
        pass
