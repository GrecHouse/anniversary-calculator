"""Config flow for Anniversary Calculator."""
import logging

import voluptuous as vol
import re

import homeassistant.helpers.config_validation as cv

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_NAME, CONF_DATE, CONF_TYPE, CONF_LUNAR, CONF_INTERCAL, ANNIV_TYPE

_LOGGER = logging.getLogger(__name__)

class AnniversaryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Anniversary Calculator."""

    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_ASSUMED

    def __init__(self):
        """Initialize flow."""
        self._name: Required[str] = None
        self._date: Required[str] = None
        self._type: Required[str] = None
        self._is_lunar: Optional[bool] = None
        self._is_intercal: Optional[bool] = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self._name = user_input[CONF_NAME]
            self._date = user_input[CONF_DATE]
            self._type = user_input[CONF_TYPE]
            self._is_lunar = user_input[CONF_LUNAR]
            self._is_intercal = user_input[CONF_INTERCAL]

            key = f'anniv-{self._name}-{self._date}'
            await self.async_set_unique_id(key)

            stitle = self._name

            _LOGGER.debug("key: %s, stitle: %s", key, stitle)

            return self.async_create_entry(title=stitle, data=user_input)

        if user_input is None:
            return self._show_user_form(errors)

    async def async_step_import(self, import_info):
        """Handle import from config file."""
        return await self.async_step_user(import_info)

    async def validate_date_format(value):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", value) and not re.match(r"^\d{2}-\d{2}$", value):
            translations = self.hass.components.frontend.translations
            raise vol.Invalid(translations["config.invalid.date"])
        return value

    @callback
    def _show_user_form(self, errors=None):
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=None): str,
                vol.Required(CONF_DATE, default=None): str,
                vol.Required(CONF_TYPE, default='anniversary'): vol.In(ANNIV_TYPE),
                vol.Optional(CONF_LUNAR, default=False): selector.BooleanSelector(selector.BooleanSelectorConfig()),
                vol.Optional(CONF_INTERCAL, default=False): selector.BooleanSelector(selector.BooleanSelectorConfig()),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors or {}
        )
