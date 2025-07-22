"""Solar Miner select platform."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SOLAR_MODES, NIGHT_MODES, POWER_PROFILES
from . import SolarMinerDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Solar Miner select entries."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    client = hass.data[DOMAIN][config_entry.entry_id]["client"]
    
    entities = [
        # Solar mode selector
        SolarMinerSolarModeSelect(coordinator, client, config_entry),
        
        # Night mode selector
        SolarMinerNightModeSelect(coordinator, client, config_entry),
        
        # Power profile selector
        SolarMinerPowerProfileSelect(coordinator, client, config_entry),
        
        # Mining pool selector
        SolarMinerPoolSelect(coordinator, client, config_entry),
    ]
    
    async_add_entities(entities)


class SolarMinerSelectEntity(CoordinatorEntity, SelectEntity):
    """Base Solar Miner select entity."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._client = client
        self._config_entry = config_entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": f"Solar Miner {config_entry.data['host']}",
            "manufacturer": "Bitmain",
            "model": self._get_miner_model(),
            "sw_version": self._get_firmware_version(),
        }
    
    def _get_miner_model(self) -> str:
        """Get miner model from data."""
        if self.coordinator.data and "summary" in self.coordinator.data:
            return self.coordinator.data["summary"].get("Type", "Unknown")
        return "Unknown"
    
    def _get_firmware_version(self) -> str:
        """Get firmware version from data."""
        if self.coordinator.data and "summary" in self.coordinator.data:
            return self.coordinator.data["summary"].get("Version", "Unknown")
        return "Unknown"


class SolarMinerSolarModeSelect(SolarMinerSelectEntity):
    """Solar Miner solar mode selector."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Solar Mode"
        self._attr_unique_id = f"{config_entry.entry_id}_solar_mode_select"
        self._attr_options = list(SOLAR_MODES.values())
        self._attr_icon = "mdi:solar-power"
        self._current_option = SOLAR_MODES["manual"]
    
    @property
    def current_option(self) -> str:
        """Return the current option."""
        return self._current_option
    
    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        if option in self._attr_options:
            self._current_option = option
            self.async_write_ha_state()
            
            # Find the mode key
            mode_key = None
            for key, value in SOLAR_MODES.items():
                if value == option:
                    mode_key = key
                    break
            
            _LOGGER.info(
                "Solar mode set to %s (%s) for miner %s",
                option,
                mode_key,
                self._config_entry.data['host']
            )
            
            # Implement mode-specific logic
            if mode_key == "sun_curve":
                await self._enable_sun_curve_mode()
            elif mode_key == "manual":
                await self._enable_manual_mode()
    
    async def _enable_sun_curve_mode(self) -> None:
        """Enable automatic sun curve following mode."""
        _LOGGER.info("Sun curve mode enabled for miner %s", self._config_entry.data['host'])
        # This would implement the sun curve automation
    
    async def _enable_manual_mode(self) -> None:
        """Enable manual control mode."""
        _LOGGER.info("Manual mode enabled for miner %s", self._config_entry.data['host'])
        # This would disable automatic sun curve following


class SolarMinerNightModeSelect(SolarMinerSelectEntity):
    """Solar Miner night mode selector."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Night Mode"
        self._attr_unique_id = f"{config_entry.entry_id}_night_mode_select"
        self._attr_options = [mode["name"] for mode in NIGHT_MODES.values()]
        self._attr_icon = "mdi:weather-night"
        self._current_option = NIGHT_MODES["30_percent"]["name"]
    
    @property
    def current_option(self) -> str:
        """Return the current option."""
        return self._current_option
    
    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        if option in self._attr_options:
            self._current_option = option
            self.async_write_ha_state()
            
            # Find the mode configuration
            mode_config = None
            mode_key = None
            for key, config in NIGHT_MODES.items():
                if config["name"] == option:
                    mode_config = config
                    mode_key = key
                    break
            
            if mode_config:
                _LOGGER.info(
                    "Night mode set to %s (%s%% power) for miner %s",
                    option,
                    mode_config["power_percent"],
                    self._config_entry.data['host']
                )
                
                # Apply the night mode power setting
                await self._apply_night_mode(mode_config["power_percent"])
    
    async def _apply_night_mode(self, power_percent: int) -> None:
        """Apply night mode power setting."""
        try:
            if power_percent == 0:
                # Standby mode - pause mining
                success = await self._client.pause_mining()
                if success:
                    _LOGGER.info("Standby mode activated for miner %s", self._config_entry.data['host'])
            else:
                # Calculate target power based on percentage
                base_power = 3250  # Typical S19j Pro+ power consumption
                target_power = int(base_power * (power_percent / 100))
                
                success = await self._client.set_power_limit(target_power)
                if success:
                    await self._client.resume_mining()
                    await self.coordinator.async_request_refresh()
                    _LOGGER.info(
                        "Night mode power set to %s watts (%s%%) for miner %s",
                        target_power,
                        power_percent,
                        self._config_entry.data['host']
                    )
        except Exception as err:
            _LOGGER.error("Error applying night mode: %s", err)


class SolarMinerPowerProfileSelect(SolarMinerSelectEntity):
    """Solar Miner power profile selector."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Power Profile"
        self._attr_unique_id = f"{config_entry.entry_id}_power_profile_select"
        self._attr_options = [profile["name"] for profile in POWER_PROFILES.values()]
        self._attr_icon = "mdi:speedometer"
        self._current_option = POWER_PROFILES["balanced"]["name"]
    
    @property
    def current_option(self) -> str:
        """Return the current option."""
        return self._current_option
    
    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        if option in self._attr_options:
            self._current_option = option
            self.async_write_ha_state()
            
            # Find the profile configuration
            profile_config = None
            profile_key = None
            for key, config in POWER_PROFILES.items():
                if config["name"] == option:
                    profile_config = config
                    profile_key = key
                    break
            
            if profile_config:
                _LOGGER.info(
                    "Power profile set to %s (overclock: %s) for miner %s",
                    option,
                    profile_config["overclock"],
                    self._config_entry.data['host']
                )
                
                # Apply the power profile
                await self._apply_power_profile(profile_key, profile_config)
    
    async def _apply_power_profile(self, profile_key: str, profile_config: dict) -> None:
        """Apply power profile setting."""
        try:
            overclock = profile_config["overclock"]
            
            if profile_key == "balanced":
                profile_name = "default"
            elif overclock > 0:
                profile_name = f"overclock_{overclock}"
            else:
                profile_name = f"underclock_{abs(overclock)}"
            
            success = await self._client.set_profile(profile_name)
            if success:
                await self.coordinator.async_request_refresh()
                _LOGGER.info(
                    "Power profile %s applied for miner %s",
                    profile_name,
                    self._config_entry.data['host']
                )
            else:
                _LOGGER.error("Failed to apply power profile for miner %s", self._config_entry.data['host'])
        except Exception as err:
            _LOGGER.error("Error applying power profile: %s", err)


class SolarMinerPoolSelect(SolarMinerSelectEntity):
    """Solar Miner mining pool selector."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Pool"
        self._attr_unique_id = f"{config_entry.entry_id}_pool_select"
        self._attr_options = []
        self._attr_icon = "mdi:server-network"
        self._current_option = None
        self._update_pool_options()
    
    def _update_pool_options(self) -> None:
        """Update available pool options from coordinator data."""
        if self.coordinator.data and "pools" in self.coordinator.data:
            pools = self.coordinator.data["pools"].get("POOLS", [])
            self._attr_options = [
                f"Pool {i}: {pool.get('URL', 'Unknown')}"
                for i, pool in enumerate(pools)
            ]
            
            # Set current option to active pool
            for i, pool in enumerate(pools):
                if pool.get("Stratum Active"):
                    self._current_option = f"Pool {i}: {pool.get('URL', 'Unknown')}"
                    break
    
    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        self._update_pool_options()
        return self._current_option
    
    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        if option in self._attr_options:
            # Extract pool index from option
            try:
                pool_index = int(option.split(":")[0].replace("Pool ", ""))
                
                # Switch to the selected pool
                # This would use the LuxOS API to switch pools
                _LOGGER.info(
                    "Switching to pool %s for miner %s",
                    option,
                    self._config_entry.data['host']
                )
                
                # Update current option
                self._current_option = option
                self.async_write_ha_state()
                
                # Refresh coordinator to get updated pool status
                await self.coordinator.async_request_refresh()
                
            except (ValueError, IndexError) as err:
                _LOGGER.error("Error parsing pool selection: %s", err)
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if self.coordinator.data and "pools" in self.coordinator.data:
            pools = self.coordinator.data["pools"].get("POOLS", [])
            return {
                "total_pools": len(pools),
                "pools_configured": [pool.get("URL") for pool in pools],
            }
        return {}