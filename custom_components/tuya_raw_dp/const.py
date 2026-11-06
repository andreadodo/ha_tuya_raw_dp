"""Costanti per l'integrazione Tuya Raw DP."""

DOMAIN = "tuya_raw_dp"

CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_DEVICE_ID = "device_id"
CONF_ENDPOINT = "endpoint"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 30  # secondi

# Endpoint ufficiali Tuya OpenAPI per data center
ENDPOINTS = {
    "Europe Central": "https://openapi.tuyaeu.com",
    "Europe West": "https://openapi-weaz.tuyaeu.com",
    "America West": "https://openapi.tuyaus.com",
    "America East": "https://openapi-ueaz.tuyaus.com",
    "China": "https://openapi.tuyacn.com",
    "India": "https://openapi.tuyain.com",
}

DEFAULT_ENDPOINT_LABEL = "Europe Central"
