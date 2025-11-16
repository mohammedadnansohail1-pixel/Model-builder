"""Storage service for MinIO/S3."""

import io
from typing import Optional, BinaryIO
from datetime import timedelta
from minio import Minio
from minio.error import S3Error

from app.core.config import settings


class StorageService:
    """Service for file storage operations using MinIO."""

    def __init__(self):
        """Initialize MinIO client."""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()

    def _ensure_bucket(self):
        """Ensure the bucket exists."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as e:
            print(f"Error ensuring bucket: {e}")

    def upload_file(
        self,
        file_path: str,
        file_data: BinaryIO,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload a file to MinIO.

        Args:
            file_path: Path in bucket
            file_data: File data as binary stream
            content_type: MIME type
            metadata: Optional metadata

        Returns:
            str: Path to uploaded file
        """
        try:
            # Get file size
            file_data.seek(0, 2)  # Seek to end
            file_size = file_data.tell()
            file_data.seek(0)  # Reset to beginning

            self.client.put_object(
                self.bucket,
                file_path,
                file_data,
                file_size,
                content_type=content_type,
                metadata=metadata or {}
            )
            return file_path
        except S3Error as e:
            raise Exception(f"Failed to upload file: {e}")

    def download_file(self, file_path: str) -> bytes:
        """
        Download a file from MinIO.

        Args:
            file_path: Path in bucket

        Returns:
            bytes: File content
        """
        try:
            response = self.client.get_object(self.bucket, file_path)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            raise Exception(f"Failed to download file: {e}")

    def get_presigned_url(
        self,
        file_path: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Get a presigned URL for file access.

        Args:
            file_path: Path in bucket
            expires: URL expiration time

        Returns:
            str: Presigned URL
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket,
                file_path,
                expires=expires
            )
            return url
        except S3Error as e:
            raise Exception(f"Failed to generate presigned URL: {e}")

    def get_presigned_upload_url(
        self,
        file_path: str,
        expires: timedelta = timedelta(minutes=30)
    ) -> str:
        """
        Get a presigned URL for file upload.

        Args:
            file_path: Path in bucket
            expires: URL expiration time

        Returns:
            str: Presigned upload URL
        """
        try:
            url = self.client.presigned_put_object(
                self.bucket,
                file_path,
                expires=expires
            )
            return url
        except S3Error as e:
            raise Exception(f"Failed to generate presigned upload URL: {e}")

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from MinIO.

        Args:
            file_path: Path in bucket

        Returns:
            bool: Success status
        """
        try:
            self.client.remove_object(self.bucket, file_path)
            return True
        except S3Error as e:
            print(f"Failed to delete file: {e}")
            return False

    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in MinIO.

        Args:
            file_path: Path in bucket

        Returns:
            bool: True if file exists
        """
        try:
            self.client.stat_object(self.bucket, file_path)
            return True
        except S3Error:
            return False

    def list_files(self, prefix: str = "") -> list:
        """
        List files in bucket with prefix.

        Args:
            prefix: File path prefix

        Returns:
            list: List of file objects
        """
        try:
            objects = self.client.list_objects(
                self.bucket,
                prefix=prefix,
                recursive=True
            )
            return [obj.object_name for obj in objects]
        except S3Error as e:
            raise Exception(f"Failed to list files: {e}")


# Global instance
storage_service = StorageService()
