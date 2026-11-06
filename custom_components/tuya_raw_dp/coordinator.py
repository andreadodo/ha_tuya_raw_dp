"""DataUpdateCoordinator per Tuya Raw DP.

Interroga periodicamente l'endpoint
  GET /v1.0/iot-03/devices/{device_id}/status
tramite la libreria tuya-connector-python (gestisce da sola login,
firma HMAC-SHA256 e refresh del token), e restituisce un dizionario
{codice_dp: valore} con TUTTI i data point che il dispositivo espone
lato cloud Tuya — non solo quelli che l'integrazione Tuya ufficiale
di Home Assistant sceglie di mappare su entità standard.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from tuya_connector import TuyaOpenAPI

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TuyaRawDPCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator che mantiene la connessione all'API Tuya e il dizionario DP."""

    def __init__(
        self,
        hass: HomeAssistant,
        client_id: str,
        client_secret: str,
        device_id: str,
        endpoint: str,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{device_id}",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.device_id = device_id
        self._api = TuyaOpenAPI(endpoint, client_id, client_secret)
        self._connected = False

    def _ensure_connect(self) -> None:
        """Login sincrono (chiamata bloccante, va eseguita nell'executor)."""
        if not self._connected:
            resp = self._api.connect()
            if not resp.get("success", False):
                raise UpdateFailed(f"Login Tuya fallito: {resp}")
            self._connected = True

    def _fetch_status_sync(self) -> dict:
        """Chiamata sincrona bloccante allo status del dispositivo."""
        self._ensure_connect()
        resp = self._api.get(f"/v1.0/iot-03/devices/{self.device_id}/status")
        if not resp.get("success", False):
            # Il token potrebbe essere scaduto/invalido: forziamo un nuovo login
            # al prossimo giro e segnaliamo l'errore a questo giro.
            self._connected = False
            raise UpdateFailed(f"Errore lettura status Tuya: {resp}")

        # resp["result"] è una lista di {"code": ..., "value": ...}
        return {item["code"]: item["value"] for item in resp.get("result", [])}

    async def _async_update_data(self) -> dict:
        try:
            return await self.hass.async_add_executor_job(self._fetch_status_sync)
        except UpdateFailed:
            raise
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Errore comunicazione con Tuya OpenAPI: {err}") from err
