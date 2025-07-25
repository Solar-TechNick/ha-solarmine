"""Config flow for Solar Miner integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, CONF_ALIAS
from .luxos_client import LuxOSClient

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_ALIAS, default=""): str,
        vol.Optional(CONF_PORT, default=80): int,
        vol.Optional(CONF_USERNAME): str,
        vol.Optional(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    
    client = LuxOSClient(
        data[CONF_HOST],
        data.get(CONF_PORT, 80),
        data.get(CONF_USERNAME),
        data.get(CONF_PASSWORD),
    )
    
    try:
        summary = await client.get_summary()
        if not summary or "SUMMARY" not in summary or not summary["SUMMARY"]:
            raise CannotConnect
        
        # Extract miner model and create unique identifier
        summary_data = summary["SUMMARY"][0]
        miner_model = summary_data.get("Type", "Unknown")
        
        # Try to get serial number, but fall back to IP address if not available
        miner_serial = summary_data.get("SN", summary_data.get("Serial", ""))
        
        # Use IP address as unique identifier to allow multiple miners
        host_ip = data[CONF_HOST]
        unique_id = f"solarminer_{host_ip.replace('.', '_')}"
        
        # Create title using alias if provided, otherwise use model and IP
        alias = data.get(CONF_ALIAS, "").strip()
        if alias:
            title = f"Solar Miner - {alias}"
        else:
            # Fallback to model and IP if no alias provided
            if miner_serial and miner_serial != "Unknown":
                title = f"Solar Miner {miner_model} ({host_ip}) - {miner_serial}"
            else:
                title = f"Solar Miner {miner_model} ({host_ip})"
        
        return {
            "title": title,
            "miner_model": miner_model,
            "miner_serial": miner_serial,
            "unique_id": unique_id,
            "host_ip": host_ip,
            "alias": alias,
        }
    except Exception as exc:
        _LOGGER.error("Error connecting to miner: %s", exc)
        raise CannotConnect from exc


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Solar Miner."""
    
    VERSION = 1
    
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Set unique ID based on IP address to allow multiple miners
                await self.async_set_unique_id(info["unique_id"])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )
        
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""