"""Tests for MeasureIt meter class."""

from datetime import datetime
from decimal import Decimal

import pytest
from homeassistant.util import dt as dt_util
from custom_components.measureit.meter import Meter
from custom_components.measureit.meter import MeterState
from custom_components.measureit.reading import ReadingData

START_PATTERN = "0 0 * * *"  # every day at midnight
NAME = "24h"
TEST_TIME_ZONE = "Europe/Amsterdam"
dt_util.set_default_time_zone(dt_util.get_time_zone(TEST_TIME_ZONE))
TZ = dt_util.DEFAULT_TIME_ZONE


def test_init():
    """Test initializing a meter."""
    meter = Meter()
    assert meter.measured_value == 0
    assert meter.state == MeterState.INITIALIZING


def test_start_on_first_reading():
    """Test if meter starts measuring after the first reading."""
    meter = Meter()
    meter.update(ReadingData(datetime(2022, 1, 1, 11, 5, tzinfo=TZ), True, True, 100))
    assert meter.measured_value == 0
    assert meter.state == MeterState.MEASURING
    assert meter._session_start_reading == 100
    assert meter._start_measured_value == 0


@pytest.mark.parametrize(
    "reading, expected_measured_value",
    [
        (
            ReadingData(datetime(2022, 1, 1, 11, 5, tzinfo=TZ), True, True, 200),
            Decimal("100"),
        ),
        (
            ReadingData(datetime(2022, 1, 1, 11, 5, tzinfo=TZ), True, True, 200000),
            199900,
        ),
        (
            ReadingData(
                datetime(2022, 1, 1, 11, 5, tzinfo=TZ), True, True, Decimal("100.01")
            ),
            Decimal("0.01"),
        ),
        (ReadingData(datetime(2022, 1, 1, 11, 5, tzinfo=TZ), True, True, 50), -50),
        (ReadingData(datetime(2022, 1, 1, 11, 5, tzinfo=TZ), True, True, 0), -100),
        (ReadingData(datetime(2022, 1, 1, 11, 5, tzinfo=TZ), True, True, -100), -200),
    ],
)
def test_update_measured_value(reading, expected_measured_value):
    """Test updating the measured value."""
    meter = Meter()
    meter.update(ReadingData(datetime(2022, 1, 1, 11, 5, tzinfo=TZ), True, True, 100))
    meter.update(reading)
    assert meter.measured_value == expected_measured_value


# def test_heartbeat(meter: Meter):
#     """Test on_heartbeat function of meter."""
#     # should trigger meter start()
#     reading = ReadingData(
#         reading_datetime=datetime(2022, 1, 1, 11, 5, tzinfo=TZ),
#         value=123,
#         template_active=True,
#         timewindow_active=True,
#     )
#     meter.on_update(reading)
#     assert meter._session_start_reading == 123
#     assert meter._start_measured_value == 0

#     fake_now = datetime(2022, 1, 1, 11, 10, tzinfo=dt_util.DEFAULT_TIME_ZONE)
#     meter.on_update(ReadingData(fake_now, True, True, 130))
#     assert meter.measured_value == 7

#     # next day, meter should reset
#     fake_now = datetime(2022, 1, 2, 11, 11, tzinfo=TZ)
#     meter.on_update(ReadingData(fake_now, True, True, 132))
#     assert meter.measured_value == 0
#     assert meter.prev_measured_value == 9

#     fake_now = datetime(2022, 1, 2, 11, 20, tzinfo=TZ)
#     meter.on_update(ReadingData(fake_now, True, False, 140))
#     assert meter.measured_value == 8

#     fake_now = datetime(2022, 1, 2, 11, 20, tzinfo=TZ)
#     meter.on_update(ReadingData(fake_now, True, False, 145))
#     assert meter.measured_value == 8

#     fake_now = datetime(2022, 1, 2, 11, 20, tzinfo=TZ)
#     meter.on_update(ReadingData(fake_now, True, True, 148))
#     assert meter.measured_value == 8

#     fake_now = datetime(2022, 1, 2, 11, 21, tzinfo=TZ)
#     meter.on_update(ReadingData(fake_now, True, True, 150))
#     assert meter.measured_value == 10


# def test_template_update(meter: Meter):
#     """Test on_template_change function of meter."""
#     fake_now = datetime(2022, 1, 1, 11, 5, tzinfo=TZ)
#     meter.on_update(ReadingData(fake_now, True, True, 123))
#     assert meter.state == MeterState.MEASURING

#     fake_now = datetime(2022, 1, 1, 11, 6, tzinfo=TZ)
#     meter.on_update(ReadingData(fake_now, False, True, 125))
#     assert meter.state == MeterState.WAITING_FOR_CONDITION
#     assert meter.measured_value == 2

#     fake_now = datetime(2022, 1, 1, 11, 7, tzinfo=TZ)
#     meter.on_update(ReadingData(fake_now, True, True, 127))
#     assert meter.state == MeterState.MEASURING
#     assert meter.measured_value == 2

#     fake_now = datetime(2022, 1, 1, 11, 8, tzinfo=TZ)
#     meter.on_update(ReadingData(fake_now, True, True, 130))
#     assert meter.state == MeterState.MEASURING
#     assert meter.measured_value == 5


# def test_update_after_restore(meter: Meter):
#     """Test restoring a meter after serialization."""
#     fake_now = datetime(2022, 1, 1, 10, 35, tzinfo=TZ)
#     meter.on_update(ReadingData(fake_now, True, True, 100))
#     assert meter.measured_value == 0
#     assert meter.state == MeterState.MEASURING

#     fake_now = datetime(2022, 1, 1, 23, 35, tzinfo=TZ)
#     meter.on_update(ReadingData(fake_now, True, True, 250))
#     assert meter.measured_value == 150
#     assert meter._period.end.tzinfo == TZ

#     restore = MeasureItMeterStoredData(
#         meter.state,
#         meter.measured_value,
#         meter.prev_measured_value,
#         meter._session_start_reading,
#         meter._start_measured_value,
#         meter._period.last_reset,
#         meter._period.end,
#     ).as_dict()

#     assert restore["measured_value"] == 150

#     last_meter_data = MeasureItMeterStoredData.from_dict(restore)

#     # restore is after the end of the period so meter needs to be reset
#     fake_now = datetime(2022, 1, 2, 0, 30, tzinfo=TZ)
#     period = Period(START_PATTERN, fake_now)
#     meter2 = Meter(NAME, period)

#     meter2.state = last_meter_data.state
#     meter2.measured_value = last_meter_data.measured_value
#     meter2._start_measured_value = last_meter_data.start_measured_value
#     meter2.prev_measured_value = last_meter_data.prev_measured_value
#     meter2._session_start_reading = last_meter_data.session_start_reading
#     meter2._period.last_reset = last_meter_data.period_last_reset
#     meter2._period.end = last_meter_data.period_end

#     assert meter2.measured_value == 150
#     assert meter2.last_reset == meter.last_reset
#     assert meter2._period.end.tzinfo == TZ
#     assert meter2.next_reset == datetime(2022, 1, 2, 0, 0, tzinfo=TZ)

#     fake_now = datetime(2022, 1, 2, 0, 35, tzinfo=TZ)
#     meter2.on_update(ReadingData(fake_now, True, True, 350))
#     assert meter2.measured_value == 0
#     assert meter2.prev_measured_value == 250


# def test_update_after_restore_forever_meter(meter: Meter):
#     """Test restoring a forever meter."""
#     meter.next_reset = datetime.max.replace(tzinfo=TZ)
#     assert meter.next_reset.year == 9999

#     restore = MeasureItMeterStoredData(
#         meter.state,
#         meter.measured_value,
#         meter.prev_measured_value,
#         meter._session_start_reading,
#         meter._start_measured_value,
#         meter._period.last_reset,
#         meter._period.end,
#     ).as_dict()

#     restored_meter = MeasureItMeterStoredData.from_dict(restore)
#     assert restored_meter.period_end == datetime.max.replace(tzinfo=TZ)


# def test_reset(meter: Meter):
#     """Test resetting a meter."""
#     fake_now = datetime(2022, 1, 1, 11, 5, tzinfo=TZ)
#     meter.on_update(ReadingData(fake_now, True, True, 123))
#     assert meter.measured_value == 0
#     assert meter.state == MeterState.MEASURING

#     fake_now = datetime(2022, 1, 1, 11, 6, tzinfo=TZ)
#     meter.on_update(ReadingData(fake_now, True, True, 125))
#     assert meter.measured_value == 2

#     meter.next_reset = datetime(2022, 1, 1, 17, 0, tzinfo=TZ)
#     assert meter.measured_value == 0
#     assert meter.state == MeterState.MEASURING
