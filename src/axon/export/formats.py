"""Export format definitions."""

from enum import Enum


class ExportFormat(str, Enum):
    """Supported export formats."""
    CSV = "csv"
    EXCEL = "xlsx"
    JSON = "json"
    TEXT = "txt"  # Human-readable summary

