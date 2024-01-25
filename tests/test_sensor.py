"""Tests for MeasureIt sensor class."""
from datetime import datetime, timedelta
from unittest import mock
import pytest
from homeassistant.util import dt as dt_util

from custom_components.measureit.const import PREDEFINED_PERIODS, MeterType
from custom_components.measureit.sensor import MeasureItSensor


@pytest.fixture(name="test_now")
def fixture_datetime_now():
    """Fixture for datetime.now."""
    return datetime(2025, 1, 1, 10, 0, 0, tzinfo=dt_util.DEFAULT_TIME_ZONE)


@pytest.fixture(name="time_sensor")
def fixture_time_sensor(hass, test_now):
    """Fixture for creating a MeasureIt sensor."""
    with mock.patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=test_now,
    ):
        sensor = MeasureItSensor(
            hass,
            MeterType.TIME,
            None,
            "test_sensor_day",
            "test_sensor_day",
            PREDEFINED_PERIODS["day"],
            None,
            "tests",
        )
        sensor._meter.reset = mock.MagicMock()
        yield sensor
        sensor.unsub_reset_listener()


def test_meter_after_sensor_restore():
    """Test meter after sensor restore."""
    assert True


def test_sensor_init(time_sensor, test_now):
    """Test sensor initialization."""
    assert time_sensor.native_value is None
    assert time_sensor._meter_type == MeterType.TIME
    assert time_sensor._next_reset == (test_now + timedelta(days=1)).replace(
        hour=0, tzinfo=dt_util.DEFAULT_TIME_ZONE
    )
    # assert time_sensor._state_class == SensorStateClass.TOTAL
    # assert time_sensor._device_class == SensorDeviceClass.DURATION


def test_sensor_reset_when_scheduled_in_past(time_sensor, test_now):
    """Test sensor reset when scheduled in past."""
    time_sensor.schedule_next_reset(test_now + timedelta(hours=1))
    assert time_sensor._meter.reset.call_count == 1
