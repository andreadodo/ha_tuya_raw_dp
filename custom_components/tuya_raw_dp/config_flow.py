"""Config flow per Tuya Raw DP."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from tuya_connector import TuyaOpenAPI

from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_DEVICE_ID,
    CONF_ENDPOINT,
    CONF_SCAN_INTERVAL,
    DEFAULT_ENDPOINT_LABEL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ENDPOINTS,
)

_LOGGER = logging.getLogger(__name__)


def _test_connection(endpoint: str, client_id: str, client_secret: str, device_id: str) -> dict:
    """Chiamata sincrona di validazione (eseguita nell'executor)."""
    api = TuyaOpenAPI(endpoint, client_id, client_secret)
    login = api.connect()
    if not login.get("success", False):
        return {"success": False, "error": login.get("msg", "login fallito")}

    resp = api.get(f"/v1.0/iot-03/devices/{device_id}/status")
    if not resp.get("success", False):
        return {"success": False, "error": resp.get("msg", "device_id non valido o non raggiungibile")}

    return {"success": True}


class TuyaRawDPConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestisce il flusso di configurazione da UI."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "TuyaRawDPOptionsFlow":
        return TuyaRawDPOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            endpoint = ENDPOINTS[user_input[CONF_ENDPOINT]]

            result = await self.hass.async_add_executor_job(
                _test_connection,
                endpoint,
                user_input[CONF_CLIENT_ID],
                user_input[CONF_CLIENT_SECRET],
                user_input[CONF_DEVICE_ID],
            )

            if result["success"]:
                await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Tuya Raw DP ({user_input[CONF_DEVICE_ID]})",
                    data={
                        CONF_CLIENT_ID: user_input[CONF_CLIENT_ID],
                        CONF_CLIENT_SECRET: user_input[CONF_CLIENT_SECRET],
                        CONF_DEVICE_ID: user_input[CONF_DEVICE_ID],
                        CONF_ENDPOINT: endpoint,
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    },
                )

            _LOGGER.error("Validazione fallita: %s", result.get("error"))
            errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): str,
                vol.Required(CONF_CLIENT_SECRET): str,
                vol.Required(CONF_DEVICE_ID): str,
                vol.Required(CONF_ENDPOINT, default=DEFAULT_ENDPOINT_LABEL): vol.In(
                    list(ENDPOINTS.keys())
                ),
                vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=5, max=3600)
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class TuyaRawDPOptionsFlow(config_entries.OptionsFlow):
    """Permette di modificare client_id, client_secret, device_id, endpoint
    e intervallo di polling dopo il setup iniziale, da GUI
    (Impostazioni → Dispositivi e servizi → Tuya Raw DP → Configura)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        current = {**self._entry.data, **self._entry.options}

        # Ricostruisco la label del data center a partire dall'endpoint salvato
        current_endpoint_label = next(
            (label for label, url in ENDPOINTS.items() if url == current.get(CONF_ENDPOINT)),
            DEFAULT_ENDPOINT_LABEL,
        )

        if user_input is not None:
            endpoint = ENDPOINTS[user_input[CONF_ENDPOINT]]

            result = await self.hass.async_add_executor_job(
                _test_connection,
                endpoint,
                user_input[CONF_CLIENT_ID],
                user_input[CONF_CLIENT_SECRET],
                user_input[CONF_DEVICE_ID],
            )

            if result["success"]:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_CLIENT_ID: user_input[CONF_CLIENT_ID],
                        CONF_CLIENT_SECRET: user_input[CONF_CLIENT_SECRET],
                        CONF_DEVICE_ID: user_input[CONF_DEVICE_ID],
                        CONF_ENDPOINT: endpoint,
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    },
                )

            errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID, default=current.get(CONF_CLIENT_ID, "")): str,
                vol.Required(CONF_CLIENT_SECRET, default=current.get(CONF_CLIENT_SECRET, "")): str,
                vol.Required(CONF_DEVICE_ID, default=current.get(CONF_DEVICE_ID, "")): str,
                vol.Required(CONF_ENDPOINT, default=current_endpoint_label): vol.In(
                    list(ENDPOINTS.keys())
                ),
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=3600)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
