"""Integrazione Tuya Raw DP.

Espone come sensori HA TUTTI i data point (DP) grezzi che un
dispositivo Tuya restituisce via API cloud, inclusi quelli che
l'integrazione Tuya ufficiale di Home Assistant non mappa su
nessuna entità standard. Utile per dispositivi Zigbee collegati
a un gateway Tuya non raggiungibile in LAN (quindi Local Tuya non
è un'opzione) e che espongono più valori di quelli visibili con
l'integrazione cloud standard.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_DEVICE_ID,
    CONF_ENDPOINT,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import TuyaRawDPCoordinator

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Imposta la config entry: crea il coordinator e il primo refresh.

    Le `options` (modificabili da GUI dopo il setup, via Configura)
    sovrascrivono i `data` originali del primo setup.
    """
    data = {**entry.data, **entry.options}

    coordinator = TuyaRawDPCoordinator(
        hass,
        client_id=data[CONF_CLIENT_ID],
        client_secret=data[CONF_CLIENT_SECRET],
        device_id=data[CONF_DEVICE_ID],
        endpoint=data[CONF_ENDPOINT],
        scan_interval=data[CONF_SCAN_INTERVAL],
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Ricarica l'intera entry quando le opzioni vengono modificate da GUI
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Ricarica la config entry dopo un cambio di opzioni da GUI."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Rimuove la config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
