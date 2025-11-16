"""Dataset service for handling dataset operations."""

import io
import json
import csv
from typing import Dict, Any, Optional, BinaryIO
import pandas as pd
from app.models.dataset import DatasetFormat, ValidationStatus
from app.services.storage_service import storage_service


class DatasetService:
    """Service for dataset operations."""

    def __init__(self):
        """Initialize the service."""
        self.storage = storage_service

    def detect_format(self, filename: str, file_data: BinaryIO) -> DatasetFormat:
        """
        Detect dataset format from filename and content.

        Args:
            filename: Original filename
            file_data: File data stream

        Returns:
            DatasetFormat: Detected format
        """
        extension = filename.lower().split('.')[-1]

        format_map = {
            'csv': DatasetFormat.CSV,
            'json': DatasetFormat.JSON,
            'jsonl': DatasetFormat.JSONL,
            'parquet': DatasetFormat.PARQUET,
            'txt': DatasetFormat.TEXT,
        }

        return format_map.get(extension, DatasetFormat.CUSTOM)

    def validate_dataset(
        self,
        file_data: BinaryIO,
        format: DatasetFormat
    ) -> Dict[str, Any]:
        """
        Validate dataset and generate report.

        Args:
            file_data: File data stream
            format: Dataset format

        Returns:
            Dict: Validation report
        """
        report = {
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "row_count": 0,
            "column_info": {},
            "sample_rows": []
        }

        try:
            if format == DatasetFormat.CSV:
                report = self._validate_csv(file_data)
            elif format == DatasetFormat.JSON:
                report = self._validate_json(file_data)
            elif format == DatasetFormat.JSONL:
                report = self._validate_jsonl(file_data)
            elif format == DatasetFormat.PARQUET:
                report = self._validate_parquet(file_data)
            elif format == DatasetFormat.TEXT:
                report = self._validate_text(file_data)
            else:
                report["warnings"].append("Unknown format, skipping validation")
                report["is_valid"] = True

        except Exception as e:
            report["errors"].append(f"Validation error: {str(e)}")

        return report

    def _validate_csv(self, file_data: BinaryIO) -> Dict[str, Any]:
        """Validate CSV dataset."""
        file_data.seek(0)
        content = file_data.read().decode('utf-8')

        # Parse CSV
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        report = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "row_count": len(rows),
            "column_info": {},
            "sample_rows": rows[:5] if rows else []
        }

        # Get column information
        if rows:
            for col in rows[0].keys():
                report["column_info"][col] = {
                    "type": "string",  # Simple type detection
                    "non_null_count": sum(1 for row in rows if row.get(col))
                }

        # Check for required columns (example)
        if not rows:
            report["errors"].append("Dataset is empty")
            report["is_valid"] = False

        return report

    def _validate_json(self, file_data: BinaryIO) -> Dict[str, Any]:
        """Validate JSON dataset."""
        file_data.seek(0)
        content = file_data.read().decode('utf-8')

        data = json.loads(content)

        report = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "row_count": 0,
            "column_info": {},
            "sample_rows": []
        }

        if isinstance(data, list):
            report["row_count"] = len(data)
            report["sample_rows"] = data[:5]

            if data:
                # Get column info from first item
                if isinstance(data[0], dict):
                    for key in data[0].keys():
                        report["column_info"][key] = {"type": "mixed"}
        else:
            report["errors"].append("JSON must be an array of objects")
            report["is_valid"] = False

        return report

    def _validate_jsonl(self, file_data: BinaryIO) -> Dict[str, Any]:
        """Validate JSONL dataset."""
        file_data.seek(0)
        content = file_data.read().decode('utf-8')

        lines = [line.strip() for line in content.split('\n') if line.strip()]
        rows = []

        for i, line in enumerate(lines):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                return {
                    "is_valid": False,
                    "errors": [f"Invalid JSON on line {i+1}"],
                    "warnings": [],
                    "row_count": 0,
                    "column_info": {},
                    "sample_rows": []
                }

        report = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "row_count": len(rows),
            "column_info": {},
            "sample_rows": rows[:5]
        }

        if rows and isinstance(rows[0], dict):
            for key in rows[0].keys():
                report["column_info"][key] = {"type": "mixed"}

        return report

    def _validate_parquet(self, file_data: BinaryIO) -> Dict[str, Any]:
        """Validate Parquet dataset."""
        file_data.seek(0)

        try:
            df = pd.read_parquet(file_data)

            report = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "row_count": len(df),
                "column_info": {},
                "sample_rows": df.head(5).to_dict('records')
            }

            for col in df.columns:
                report["column_info"][col] = {
                    "type": str(df[col].dtype),
                    "non_null_count": int(df[col].count())
                }

            return report

        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"Failed to read Parquet: {str(e)}"],
                "warnings": [],
                "row_count": 0,
                "column_info": {},
                "sample_rows": []
            }

    def _validate_text(self, file_data: BinaryIO) -> Dict[str, Any]:
        """Validate text dataset."""
        file_data.seek(0)
        content = file_data.read().decode('utf-8')

        lines = content.split('\n')

        return {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "row_count": len(lines),
            "column_info": {"text": {"type": "string"}},
            "sample_rows": [{"text": line} for line in lines[:5]]
        }

    def generate_statistics(
        self,
        file_data: BinaryIO,
        format: DatasetFormat
    ) -> Dict[str, Any]:
        """
        Generate statistics for dataset.

        Args:
            file_data: File data stream
            format: Dataset format

        Returns:
            Dict: Statistics
        """
        stats = {
            "total_rows": 0,
            "total_columns": 0,
            "missing_values": 0,
            "duplicate_rows": 0
        }

        try:
            if format == DatasetFormat.CSV:
                file_data.seek(0)
                df = pd.read_csv(file_data)
                stats["total_rows"] = len(df)
                stats["total_columns"] = len(df.columns)
                stats["missing_values"] = int(df.isnull().sum().sum())
                stats["duplicate_rows"] = int(df.duplicated().sum())

            elif format == DatasetFormat.PARQUET:
                file_data.seek(0)
                df = pd.read_parquet(file_data)
                stats["total_rows"] = len(df)
                stats["total_columns"] = len(df.columns)
                stats["missing_values"] = int(df.isnull().sum().sum())
                stats["duplicate_rows"] = int(df.duplicated().sum())

        except Exception as e:
            stats["error"] = str(e)

        return stats

    def split_dataset(
        self,
        file_data: BinaryIO,
        format: DatasetFormat,
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1
    ) -> Dict[str, Any]:
        """
        Split dataset into train/val/test sets.

        Args:
            file_data: File data stream
            format: Dataset format
            train_ratio: Training set ratio
            val_ratio: Validation set ratio
            test_ratio: Test set ratio

        Returns:
            Dict: Split information
        """
        # For now, return split configuration
        # Actual splitting would be done during training
        return {
            "train_split": train_ratio,
            "validation_split": val_ratio,
            "test_split": test_ratio,
            "message": "Split configuration saved"
        }


# Global instance
dataset_service = DatasetService()
