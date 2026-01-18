from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_BASE_TOPIC,
    CONF_OUT_COUNT,
    DEFAULT_BASE_TOPIC,
    DEFAULT_OUT_COUNT,
)

class TWGConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=f"TWG {user_input[CONF_DEVICE_ID]}", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_ID, default="Twg_Test_Mqtt"): str,
                vol.Required(CONF_BASE_TOPIC, default=DEFAULT_BASE_TOPIC): str,
                vol.Required(CONF_OUT_COUNT, default=DEFAULT_OUT_COUNT): vol.All(int, vol.Range(min=1, max=64)),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return TWGOptionsFlow(config_entry)


class TWGOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_TOPIC, default=self._entry.data.get(CONF_BASE_TOPIC, DEFAULT_BASE_TOPIC)): str,
                vol.Required(CONF_OUT_COUNT, default=self._entry.data.get(CONF_OUT_COUNT, DEFAULT_OUT_COUNT)): vol.All(
                    int, vol.Range(min=1, max=64)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
