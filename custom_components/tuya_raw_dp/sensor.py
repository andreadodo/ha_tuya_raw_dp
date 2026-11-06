"""Piattaforma sensor: un'entità per ogni DP grezzo restituito da Tuya."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, DOMAIN
from .coordinator import TuyaRawDPCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator: TuyaRawDPCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_id = entry.data[CONF_DEVICE_ID]

    known_codes: set[str] = set()

    def _add_new_sensors() -> None:
        new_codes = set(coordinator.data or {}) - known_codes
        if not new_codes:
            return
        known_codes.update(new_codes)
        async_add_entities(
            TuyaRawDPSensor(coordinator, device_id, code) for code in new_codes
        )

    _add_new_sensors()
    coordinator.async_add_listener(_add_new_sensors)


class TuyaRawDPSensor(CoordinatorEntity[TuyaRawDPCoordinator], SensorEntity):
    """Un sensore per singolo data point (DP) grezzo Tuya."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: TuyaRawDPCoordinator, device_id: str, code: str) -> None:
        super().__init__(coordinator)
        self._code = code
        self._attr_unique_id = f"{device_id}_{code}"
        self._attr_name = code
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"Tuya Raw DP {device_id}",
            manufacturer="Tuya",
            model="Raw DP bridge",
        )

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._code)

    @property
    def available(self) -> bool:
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._code in self.coordinator.data
        )
