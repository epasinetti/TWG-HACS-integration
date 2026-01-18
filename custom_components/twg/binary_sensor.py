from __future__ import annotations

import json

from homeassistant.components import mqtt
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_DEVICE_ID, CONF_BASE_TOPIC, TOPIC_STATE_SUFFIX

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    device_id = entry.data[CONF_DEVICE_ID]
    base_topic = entry.data[CONF_BASE_TOPIC]
    state_topic = f"{base_topic}/{TOPIC_STATE_SUFFIX}"

    # Digitali: default 8 ingressi (1..8)
    entities = [TWGDigitalInBinary(device_id, state_topic, di_id=i) for i in range(1, 9)]
    async_add_entities(entities, update_before_add=False)

class TWGDigitalInBinary(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:ray-vertex"

    def __init__(self, device_id: str, state_topic: str, di_id: int) -> None:
        self._device_id = device_id
        self._state_topic = state_topic
        self._di_id = di_id
        self._is_on = False

        self._attr_unique_id = f"{device_id}_di_{di_id}"
        self._attr_name = f"DI {di_id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"TWG {device_id}",
            manufacturer="Tecnowatt",
            model="TW-G board",
        )

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_added_to_hass(self) -> None:
        await mqtt.async_subscribe(self.hass, self._state_topic, self._message_received, qos=0)

    @callback
    def _message_received(self, msg) -> None:
        try:
            data = json.loads(msg.payload)
            digitali = data["Data"]["IO"].get("Digitali", [])
            for item in digitali:
                if int(item.get("id")) == self._di_id:
                    self._is_on = bool(int(item.get("val", 0)))
                    self.async_write_ha_state()
                    return
        except Exception:
            return
