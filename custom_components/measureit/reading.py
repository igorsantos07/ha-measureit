"""Data class for reading data."""
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass


@dataclass
class ReadingData:
    """Class containing data for a specific reading."""

    reading_datetime: datetime = None
    template_active: bool = None
    timewindow_active: bool = None
    value: Decimal = None
