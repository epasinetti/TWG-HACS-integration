from __future__ import annotations

import json

from homeassistant.components import mqtt
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_DEVICE_ID, CONF_BASE_TOPIC, TOPIC_STATE_SUFFIX

SENSORS = [
    ("Versione FW", ("Data", "General", "VersioneFW")),
    ("MAC Address", ("Data", "General", "MACAddress")),
    ("MQTT Conn Status", ("Data", "General", "MqttConnectionStatus")),
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    device_id = entry.data[CONF_DEVICE_ID]
    base_topic = entry.data[CONF_BASE_TOPIC]
    state_topic = f"{base_topic}/{TOPIC_STATE_SUFFIX}"

    general_entities = [
        TWGGeneralSensor(device_id=device_id, state_topic=state_topic, name=n, path=p)
        for (n, p) in SENSORS
    ]

    # Analogici: default 8 ingressi (1..8)
    analog_entities = [TWGAnalogInSensor(device_id=device_id, state_topic=state_topic, ai_id=i) for i in range(1, 9)]

    async_add_entities(general_entities + analog_entities, update_before_add=False)

class TWGGeneralSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:chip"

    def __init__(self, device_id: str, state_topic: str, name: str, path: tuple[str, ...]) -> None:
        self._device_id = device_id
        self._state_topic = state_topic
        self._path = path

        self._attr_unique_id = f"{device_id}_general_{'_'.join(path)}"
        self._attr_name = name
        self._attr_native_value = None

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"TWG {device_id}",
            manufacturer="Tecnowatt",
            model="TW-G board",
        )

    async def async_added_to_hass(self) -> None:
        await mqtt.async_subscribe(self.hass, self._state_topic, self._message_received, qos=0)

    @callback
    def _message_received(self, msg) -> None:
        try:
            data = json.loads(msg.payload)
            v = data
            for k in self._path:
                v = v[k]
            self._attr_native_value = v
            self.async_write_ha_state()
        except Exception:
            return

class TWGAnalogInSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:signal"

    def __init__(self, device_id: str, state_topic: str, ai_id: int) -> None:
        self._device_id = device_id
        self._state_topic = state_topic
        self._ai_id = ai_id

        self._attr_unique_id = f"{device_id}_ai_{ai_id}"
        self._attr_name = f"AI {ai_id}"
        self._attr_native_value = None

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"TWG {device_id}",
            manufacturer="Tecnowatt",
            model="TW-G board",
        )

    async def async_added_to_hass(self) -> None:
        await mqtt.async_subscribe(self.hass, self._state_topic, self._message_received, qos=0)

    @callback
    def _message_received(self, msg) -> None:
        try:
            data = json.loads(msg.payload)
            analogici = data["Data"]["IO"].get("Analogici", [])
            for item in analogici:
                if int(item.get("id")) == self._ai_id:
                    v = item.get("val", None)
                    try:
                        self._attr_native_value = float(v)
                    except Exception:
                        self._attr_native_value = None
                    self.async_write_ha_state()
                    return
        except Exception:
            return
