"""Tests for MeasureIt sensor class."""
from datetime import datetime, timedelta
from unittest import mock
import pytest
from homeassistant.util import dt as dt_util

from custom_components.measureit.const import PREDEFINED_PERIODS, MeterType
from custom_components.measureit.meter import MeterState
from custom_components.measureit.reading import ReadingData
from custom_components.measureit.sensor import MeasureItSensor


@pytest.fixture(name="test_now")
def fixture_datetime_now():
    """Fixture for datetime.now."""
    return datetime(2025, 1, 1, 10, 0, 0, tzinfo=dt_util.DEFAULT_TIME_ZONE)


@pytest.fixture(name="day_sensor")
def fixture_day_sensor(hass, test_now):
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
        sensor.entity_id = "sensor.test_sensor_day"
        sensor._value_template_renderer = mock.MagicMock(side_effect=lambda x: x)
        yield sensor
        sensor.unsub_reset_listener()


@pytest.fixture(name="none_sensor")
def fixture_none_sensor(hass, test_now):
    """Fixture for creating a MeasureIt sensor."""
    with mock.patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=test_now,
    ):
        sensor = MeasureItSensor(
            hass,
            MeterType.TIME,
            None,
            "test_sensor_none",
            "test_sensor_none",
            None,
            None,
            "tests",
        )
        sensor.entity_id = "sensor.test_sensor_none"
        sensor._value_template_renderer = mock.MagicMock(side_effect=lambda x: x)
        yield sensor
        sensor.unsub_reset_listener()


def test_meter_after_sensor_restore():
    """Test meter after sensor restore."""
    assert True


def test_day_sensor_init(day_sensor, test_now):
    """Test sensor initialization."""
    assert day_sensor.native_value == 0
    assert day_sensor._meter_type == MeterType.TIME
    assert day_sensor.next_reset == (test_now + timedelta(days=1)).replace(
        hour=0, tzinfo=dt_util.DEFAULT_TIME_ZONE
    )
    # assert day_sensor._state_class == SensorStateClass.TOTAL
    # assert day_sensor._device_class == SensorDeviceClass.DURATION


def test_none_sensor_init(none_sensor, test_now):
    """Test sensor initialization."""
    assert none_sensor.native_value == 0
    assert none_sensor._meter_type == MeterType.TIME
    assert none_sensor.next_reset is None
    # assert day_sensor._state_class == SensorStateClass.TOTAL
    # assert day_sensor._device_class == SensorDeviceClass.DURATION


def test_scheduled_reset_in_past(day_sensor, test_now):
    """Test sensor reset when scheduled in past."""
    with mock.patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=datetime(2025, 1, 1, 12, 0, 0, tzinfo=dt_util.DEFAULT_TIME_ZONE),
    ):
        day_sensor.reset = mock.MagicMock()
        day_sensor.schedule_next_reset(test_now + timedelta(hours=1))
    assert day_sensor.reset.call_count == 1


def test_scheduled_reset_in_future(day_sensor, test_now):
    """Test sensor reset when scheduled in past."""
    with mock.patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=datetime(2025, 1, 1, 10, 30, 0, tzinfo=dt_util.DEFAULT_TIME_ZONE),
    ):
        day_sensor.reset = mock.MagicMock()
        assert day_sensor.next_reset == datetime(
            2025, 1, 2, 0, 0, 0, tzinfo=dt_util.DEFAULT_TIME_ZONE
        )
        day_sensor.schedule_next_reset(test_now + timedelta(hours=1))

    assert day_sensor.reset.call_count == 0
    assert day_sensor.next_reset == test_now + timedelta(hours=1)

    with mock.patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=datetime(2025, 1, 3, 12, 30, 0, tzinfo=dt_util.DEFAULT_TIME_ZONE),
    ):
        day_sensor.schedule_next_reset()
    assert day_sensor.next_reset == datetime(
        2025, 1, 4, 0, 00, 0, tzinfo=dt_util.DEFAULT_TIME_ZONE
    )


def test_schedule_reset_none_sensor(none_sensor):
    """Test sensor reset when scheduled in past."""
    with mock.patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=datetime(2025, 1, 1, 12, 0, 0, tzinfo=dt_util.DEFAULT_TIME_ZONE),
    ):
        none_sensor.reset = mock.MagicMock()
        none_sensor.schedule_next_reset(
            datetime(2025, 1, 1, 13, 0, 0, tzinfo=dt_util.DEFAULT_TIME_ZONE)
        )
    assert none_sensor.reset.call_count == 0
    assert none_sensor.next_reset == datetime(
        2025, 1, 1, 13, 0, 0, tzinfo=dt_util.DEFAULT_TIME_ZONE
    )
    none_sensor.schedule_next_reset()
    assert none_sensor.next_reset is None


async def test_reset_sensor_while_measuring(none_sensor, test_now):
    none_sensor._handle_coordinator_update(ReadingData(test_now, True, True, 100))
    assert none_sensor.native_value == 0
    none_sensor._handle_coordinator_update(ReadingData(test_now, True, True, 200))
    assert none_sensor.native_value == 100
    assert none_sensor.meter_state == MeterState.MEASURING
    none_sensor.reset(datetime(2025, 1, 1, 13, 0, 0, tzinfo=dt_util.DEFAULT_TIME_ZONE))
    assert none_sensor.native_value == 0


async def test_reset_sensor_while_waiting(none_sensor, test_now):
    none_sensor._handle_coordinator_update(ReadingData(test_now, True, True, 100))
    assert none_sensor.native_value == 0
    none_sensor._handle_coordinator_update(ReadingData(test_now, False, True, 200))
    assert none_sensor.native_value == 100
    assert none_sensor.meter_state == MeterState.WAITING_FOR_CONDITION
    none_sensor.reset(datetime(2025, 1, 1, 13, 0, 0, tzinfo=dt_util.DEFAULT_TIME_ZONE))
    assert none_sensor.native_value == 0
    assert none_sensor.prev_native_value == 100
