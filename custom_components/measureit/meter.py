"""Meter logic for MeasureIt."""
from __future__ import annotations
from enum import Enum
from decimal import Decimal
from .reading import ReadingData


class MeterState(str, Enum):
    """Enum with possible meter states."""

    INITIALIZING = "initializing"
    MEASURING = "measuring"
    WAITING_FOR_CONDITION = "waiting for condition"
    WAITING_FOR_TIME_WINDOW = "waiting for time window"


class Meter:
    """Meter implementation."""

    def __init__(self):
        """Initialize meter."""
        self.state: MeterState = MeterState.INITIALIZING
        self.measured_value: Decimal = 0
        self.prev_measured_value: Decimal = 0
        self._session_start_reading: Decimal | None = None
        self._start_measured_value: Decimal | None = None

        self._template_active: bool = False
        self._time_window_active: bool = False
        self._last_reading_value: Decimal | None = None

    def reset(self):
        """Reset the meter."""
        self.prev_measured_value, self.measured_value = self.measured_value, 0
        self._session_start_reading = self._last_reading_value
        self._start_measured_value = self.measured_value

    def update(self, reading: ReadingData):
        """Update the meter with reading data."""
        self._last_reading_value = (
            reading.value
        )  # always store the last reading value as we need it for the reset

        if self.state == MeterState.MEASURING:
            # Update the measured_value with the difference between the current reading and the session_start_reading
            session_value = reading.value - self._session_start_reading
            self.measured_value = self._start_measured_value + session_value

        self._template_active = reading.template_active
        self._time_window_active = reading.timewindow_active
        self._update_state(reading.value)

    def _start(self, reading):
        """Initialize the session reading so we know where we started and can subtract that from future readings to get the difference."""
        self._session_start_reading = reading
        self._start_measured_value = self.measured_value

    def _update_state(self, reading: Decimal) -> MeterState:
        """Update the state (MeterState) of the meeting (MEASURING/WAITING_FOR_CONDITION/WAITING_FOR_TIME_WINDOW)."""

        # If we enter the MEASURING state, we also start a new session (self._start(reading)).
        if self._template_active is True and self._time_window_active is True:
            new_state = MeterState.MEASURING
        elif self._time_window_active is False:
            new_state = MeterState.WAITING_FOR_TIME_WINDOW
        elif self._template_active is False:
            new_state = MeterState.WAITING_FOR_CONDITION
        else:
            raise ValueError("Invalid state determined.")

        if new_state == self.state:
            return
        if new_state == MeterState.MEASURING:
            self._start(reading)
        self.state = new_state
