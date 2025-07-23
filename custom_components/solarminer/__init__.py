"""The Solar Miner integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .luxos_client import LuxOSClient
from .automation import SolarMinerAutomation

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Solar Miner from a config entry."""
    host = entry.data["host"]
    port = entry.data.get("port", 80)
    username = entry.data.get("username")
    password = entry.data.get("password")
    
    client = LuxOSClient(host, port, username, password)
    
    coordinator = SolarMinerDataUpdateCoordinator(hass, client)
    
    await coordinator.async_config_entry_first_refresh()
    
    # Initialize solar automation
    automation = SolarMinerAutomation(hass, client, coordinator, entry)
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
        "automation": automation,
    }
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Cleanup automation
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            automation = hass.data[DOMAIN][entry.entry_id].get("automation")
            if automation:
                automation.cleanup()
        
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


class SolarMinerDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Solar Miner."""
    
    def __init__(self, hass: HomeAssistant, client: LuxOSClient) -> None:
        """Initialize."""
        self.client = client
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
    
    async def _async_update_data(self):
        """Update data via library."""
        try:
            # Get core data
            summary = await self.client.get_summary()
            pools = await self.client.get_pools()
            devs = await self.client.get_devs()
            stats = await self.client.get_stats()
            
            # Get additional LuxOS-specific data with error handling
            profiles = None
            power = None
            atm = None
            
            try:
                profiles = await self.client.get_profiles()
            except Exception as err:
                _LOGGER.warning(f"Failed to get profiles data: {err}")
                profiles = {"PROFILES": []}  # Empty fallback
            
            try:
                power = await self.client.get_power()
            except Exception as err:
                _LOGGER.warning(f"Failed to get power data: {err}")
                power = {"POWER": [{"Watts": 0}]}  # Fallback
            
            try:
                atm = await self.client.get_atm()
            except Exception as err:
                _LOGGER.warning(f"Failed to get ATM data: {err}")
                atm = {"ATM": [{"Enabled": False}]}  # Fallback
            
            return {
                "summary": summary,
                "pools": pools,
                "devices": devs,  # Use 'devices' key for consistency with sensors
                "stats": stats,
                "profiles": profiles,
                "power": power,
                "atm": atm,
                "last_update": self.hass.loop.time(),
            }
        except Exception as exception:
            raise UpdateFailed(f"Error communicating with API: {exception}") from exception