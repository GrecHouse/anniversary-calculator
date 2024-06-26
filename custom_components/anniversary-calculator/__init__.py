""" Anniversary Sensor for Home Assistant """
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from .const import DOMAIN, PLATFORM

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("call async_setup_entry")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_options))
    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("call async_unload_entry")
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)

async def _async_update_options(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    # update entry replacing data with new options
    _LOGGER.debug("call _async_update_options")
    hass.config_entries.async_update_entry(config_entry, data={**config_entry.data, **config_entry.options})
    await hass.config_entries.async_reload(config_entry.entry_id)
