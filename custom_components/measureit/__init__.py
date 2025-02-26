"""MeasureIt integration."""
import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, ATTR_ENTITY_ID
from homeassistant.core import Config, CoreState, callback
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.template import Template
from homeassistant.helpers import config_validation as cv
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.util import dt as dt_util

from .const import CONF_CONDITION, CONF_CONFIG_NAME, DOMAIN, SOURCE_ENTITY_ID
from .const import CONF_METER_TYPE
from .const import CONF_SOURCE
from .const import CONF_TW_DAYS
from .const import CONF_TW_FROM
from .const import CONF_TW_TILL
from .const import COORDINATOR
from .const import DOMAIN_DATA
from .const import METER_TYPE_SOURCE
from .coordinator import MeasureItCoordinator
from .time_window import TimeWindow

_LOGGER: logging.Logger = logging.getLogger(__name__)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN) # required to pass hassfest validation due to use of async_setup

async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    hass.data.setdefault(DOMAIN, {}).setdefault(SENSOR_DOMAIN, {})
    _register_services(hass, "config_name")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""

    config_name: str = entry.options[CONF_CONFIG_NAME]
    meter_type: str = entry.options[CONF_METER_TYPE]
    condition: str | None = entry.options.get(CONF_CONDITION)
    source_entity = None

    if meter_type == METER_TYPE_SOURCE:
        registry = er.async_get(hass)

        try:
            source_entity = er.async_validate_entity_id(
                registry, entry.options[CONF_SOURCE]
            )
            hass.data.setdefault(DOMAIN_DATA, {}).setdefault(entry.entry_id, {}).update(
                {
                    SOURCE_ENTITY_ID: entry.options[CONF_SOURCE],
                }
            )
        except vol.Invalid:
            # The entity is identified by an unknown entity registry ID
            _LOGGER.error(
                "%s # Failed to setup MeasureIt for unknown entity %s",
                config_name,
                entry.options[CONF_SOURCE],
            )
            return False

    if condition:
        condition = Template(condition)
        condition.ensure_valid()

    time_window = TimeWindow(
        entry.options[CONF_TW_DAYS],
        entry.options[CONF_TW_FROM],
        entry.options[CONF_TW_TILL],
    )

    coordinator = MeasureItCoordinator(
        hass, config_name, condition, time_window, meter_type, source_entity
    )
    hass.data.setdefault(DOMAIN_DATA, {}).setdefault(entry.entry_id, {}).update(
        {
            COORDINATOR: coordinator,
        }
    )

    await hass.config_entries.async_forward_entry_setups(entry, ([Platform.SENSOR]))

    @callback
    def run_start(event):
        # pylint: disable=unused-argument
        _LOGGER.debug("%s # Start coordinator", config_name)
        coordinator.start()

    if hass.state != CoreState.running:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, run_start)
    else:
        run_start(None)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


def _register_services(hass: HomeAssistant, config_name: str):
    """Register services for MeasureIt."""

    def reset_sensor(service_call):
        """Reset sensor."""
        _LOGGER.debug("%s # Reset sensor with: %s", config_name, service_call.data)
        reset_datetime = service_call.data.get("reset_datetime") or dt_util.now()
        if not reset_datetime.tzinfo:
            reset_datetime = reset_datetime.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)

        for entity_id in service_call.data[ATTR_ENTITY_ID]:
            hass.data[DOMAIN][SENSOR_DOMAIN].get(entity_id).reset(reset_datetime)

    hass.services.async_register(
        DOMAIN,
        "reset_sensor",
        reset_sensor,
        vol.Schema(
            {
                vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
                vol.Optional("reset_datetime"): cv.datetime,
            }
        ),
    )


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener, called when the config entry options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator = hass.data[DOMAIN_DATA][entry.entry_id][COORDINATOR]
    coordinator.stop()

    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry,
        (Platform.SENSOR,),
    ):
        hass.data[DOMAIN_DATA].pop(entry.entry_id)

    return unload_ok
