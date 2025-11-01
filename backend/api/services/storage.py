"""
Supabase Storage Service for managing dataset files.

Handles all interactions with Supabase Storage bucket for datasets (PDFs, JSON files).
"""

import os
import tempfile
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class DatasetNotFoundError(Exception):
    """Raised when dataset is not found in cloud storage."""
    pass


class SupabaseStorageService:
    """
    Manages all dataset files in Supabase Storage.

    Bucket structure:
        ragrace-datasets/
        ├── squad2/
        │   ├── train-v2.0.json
        │   └── dev-v2.0.json
        ├── qasper/
        │   └── pdfs/
        │       ├── 1907.05664.pdf
        │       └── ...
        └── policyqa/
            ├── train.json
            └── pdfs/
                └── ...
    """

    BUCKET_NAME = "ragrace-datasets"

    def __init__(self):
        """Initialize Supabase Storage client."""
        from supabase import create_client

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError(
                "Missing Supabase credentials. Set SUPABASE_URL and "
                "SUPABASE_SERVICE_KEY (or SUPABASE_ANON_KEY) in environment."
            )

        self.client = create_client(supabase_url, supabase_key)
        self.storage = self.client.storage.from_(self.BUCKET_NAME)

    def check_exists(self, path: str) -> bool:
        """
        Check if file exists in storage.

        Args:
            path: Path within bucket (e.g., 'squad2/train-v2.0.json')

        Returns:
            True if file exists, False otherwise
        """
        try:
            # Try to get file info - if it exists, this won't raise
            files = self.storage.list(path=str(Path(path).parent))
            filename = Path(path).name
            return any(f['name'] == filename for f in files)
        except Exception as e:
            logger.debug(f"File {path} does not exist: {e}")
            return False

    def download_to_temp(self, path: str) -> Path:
        """
        Download file from storage to temporary location.

        Args:
            path: Path within bucket (e.g., 'squad2/train-v2.0.json')

        Returns:
            Path to temporary file

        Raises:
            DatasetNotFoundError: If file not found in storage
        """
        try:
            # Download file data
            data = self.storage.download(path)

            # Create temp file with appropriate suffix
            suffix = Path(path).suffix
            temp_file = Path(tempfile.mktemp(suffix=suffix))

            # Write data to temp file
            temp_file.write_bytes(data)

            logger.info(f"Downloaded {path} to {temp_file}")
            return temp_file

        except Exception as e:
            available = self.list_available()
            raise DatasetNotFoundError(
                f"Dataset '{path}' not found in Supabase Storage.\n\n"
                f"Available datasets:\n" +
                "\n".join(f"  - {f}" for f in available[:10]) +
                (f"\n  ... and {len(available) - 10} more" if len(available) > 10 else "") +
                f"\n\nTo upload this dataset:\n"
                f"  1. See: local_docs/MANUAL_UPLOAD_GUIDE.md\n"
                f"  2. Or run: python backend/scripts/upload_datasets_to_storage.py\n\n"
                f"Original error: {e}"
            )

    def upload(self, local_path: str, storage_path: str) -> str:
        """
        Upload file to storage.

        Args:
            local_path: Path to local file
            storage_path: Destination path in bucket (e.g., 'squad2/train-v2.0.json')

        Returns:
            Public URL of uploaded file

        Raises:
            FileNotFoundError: If local file doesn't exist
        """
        local_file = Path(local_path)
        if not local_file.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        # Read file data
        with open(local_file, 'rb') as f:
            file_data = f.read()

        # Upload to storage
        try:
            self.storage.upload(storage_path, file_data, {"upsert": "true"})
            logger.info(f"Uploaded {local_path} to {storage_path}")

            # Return public URL
            return self.get_public_url(storage_path)

        except Exception as e:
            logger.error(f"Failed to upload {local_path}: {e}")
            raise

    def get_public_url(self, path: str) -> str:
        """
        Get public URL for a file in storage.

        Args:
            path: Path within bucket

        Returns:
            Public URL
        """
        return self.storage.get_public_url(path)

    def list_available(self, prefix: str = "") -> List[str]:
        """
        List all available datasets in storage.

        Args:
            prefix: Optional prefix to filter by (e.g., 'squad2/')

        Returns:
            List of file paths
        """
        try:
            files = self.storage.list(path=prefix)

            # Recursively list all files
            all_files = []
            for item in files:
                item_path = f"{prefix}/{item['name']}" if prefix else item['name']

                # If it's a folder, recursively list
                if item.get('id') is None:  # Folders don't have IDs
                    all_files.extend(self.list_available(prefix=item_path))
                else:
                    all_files.append(item_path)

            return sorted(all_files)

        except Exception as e:
            logger.warning(f"Failed to list files in {prefix or 'root'}: {e}")
            return []

    def delete(self, path: str):
        """
        Delete file from storage.

        Args:
            path: Path within bucket
        """
        try:
            self.storage.remove([path])
            logger.info(f"Deleted {path} from storage")
        except Exception as e:
            logger.error(f"Failed to delete {path}: {e}")
            raise
