from __future__ import annotations

import json
from dataclasses import dataclass

from homeassistant.components import mqtt
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_BASE_TOPIC,
    CONF_OUT_COUNT,
    TOPIC_STATE_SUFFIX,
    TOPIC_COMMAND_SUFFIX,
)

@dataclass(frozen=True)
class TWGConfig:
    device_id: str
    base_topic: str
    out_count: int

def _topics(cfg: TWGConfig) -> tuple[str, str]:
    state_topic = f"{cfg.base_topic}/{TOPIC_STATE_SUFFIX}"
    cmd_topic = f"{cfg.base_topic}/{TOPIC_COMMAND_SUFFIX}"
    return state_topic, cmd_topic

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    cfg = TWGConfig(
        device_id=entry.data[CONF_DEVICE_ID],
        base_topic=entry.data[CONF_BASE_TOPIC],
        out_count=entry.data[CONF_OUT_COUNT],
    )
    entities = [TWGOutSwitch(cfg, out_id=i) for i in range(1, cfg.out_count + 1)]
    async_add_entities(entities, update_before_add=False)

class TWGOutSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:power-socket-eu"

    def __init__(self, cfg: TWGConfig, out_id: int) -> None:
        self._cfg = cfg
        self._out_id = out_id
        self._is_on = False
        self._state_topic, self._cmd_topic = _topics(cfg)

        self._attr_unique_id = f"{cfg.device_id}_out_{out_id}"
        self._attr_name = f"Out {out_id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, cfg.device_id)},
            name=f"TWG {cfg.device_id}",
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
            uscite = data["Data"]["IO"]["Uscite"]
            for item in uscite:
                if int(item.get("id")) == self._out_id:
                    self._is_on = bool(int(item.get("val", 0)))
                    self.async_write_ha_state()
                    return
        except Exception:
            return

    async def async_turn_on(self, **kwargs) -> None:
        await self._publish_command(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._publish_command(False)

    async def _publish_command(self, on_off: bool) -> None:
        payload = {
            "device_id": self._cfg.device_id,
            "Type": "DigCommand",
            "Data": {
                "Channel": "LOC",
                "Out": self._out_id,
                "Status": on_off,  # true/false
            },
        }
        await mqtt.async_publish(self.hass, self._cmd_topic, json.dumps(payload), qos=0, retain=False)
