"""Solar Miner switch platform."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_ALIAS
from . import SolarMinerDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Solar Miner switch entries."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    client = hass.data[DOMAIN][config_entry.entry_id]["client"]
    
    entities = [
        # Individual hashboard switches
        SolarMinerHashboardSwitch(coordinator, client, config_entry, 0),
        SolarMinerHashboardSwitch(coordinator, client, config_entry, 1),
        SolarMinerHashboardSwitch(coordinator, client, config_entry, 2),
        
        # Mining control switches
        SolarMinerMiningSwitch(coordinator, client, config_entry),
        SolarMinerPauseMiningSwitch(coordinator, client, config_entry),
        SolarMinerSolarModeSwitch(coordinator, client, config_entry),
        SolarMinerAutoStandbySwitch(coordinator, client, config_entry),
    ]
    
    async_add_entities(entities)


class SolarMinerSwitchEntity(CoordinatorEntity, SwitchEntity):
    """Base Solar Miner switch entity."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._client = client
        self._config_entry = config_entry
        # State persistence for switches
        self._stored_state = None
        self._last_known_state = None
        # Create device identifier using IP address
        host_ip = config_entry.data['host']
        device_id = f"solarminer_{host_ip.replace('.', '_')}"
        
        # Get display name from alias or fallback to IP
        self._display_name = self._get_display_name()
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": self._display_name,
            "manufacturer": "Bitmain",
            "model": self._get_miner_model(),
            "sw_version": self._get_firmware_version(),
            "configuration_url": f"http://{host_ip}",
        }
    
    def _get_miner_model(self) -> str:
        """Get miner model from data."""
        if self.coordinator.data and "summary" in self.coordinator.data:
            summary_data = self.coordinator.data["summary"]
            if "SUMMARY" in summary_data and summary_data["SUMMARY"]:
                return summary_data["SUMMARY"][0].get("Type", "Unknown")
        return "Unknown"
    
    def _get_firmware_version(self) -> str:
        """Get firmware version from data."""
        if self.coordinator.data and "summary" in self.coordinator.data:
            summary_data = self.coordinator.data["summary"]
            if "SUMMARY" in summary_data and summary_data["SUMMARY"]:
                return summary_data["SUMMARY"][0].get("Version", "Unknown")
        return "Unknown"
    
    def _get_display_name(self) -> str:
        """Get display name from alias or fallback to default."""
        alias = self._config_entry.data.get(CONF_ALIAS, "").strip()
        if alias:
            return alias
        else:
            # Fallback to IP address for backward compatibility
            host_ip = self._config_entry.data['host']
            return f"Solar Miner {host_ip}"


class SolarMinerHashboardSwitch(SolarMinerSwitchEntity):
    """Solar Miner hashboard switch."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
        board_id: int,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, client, config_entry)
        self._board_id = board_id
        self._attr_name = f"{self._display_name} Board {board_id}"
        self._attr_unique_id = f"{config_entry.entry_id}_board_{board_id}_switch"
        self._attr_icon = "mdi:memory"
    
    @property
    def is_on(self) -> bool | None:
        """Return True if the hashboard is enabled."""
        if self.coordinator.data and "devices" in self.coordinator.data:
            devs_data = self.coordinator.data["devices"]
            if "DEVS" in devs_data:
                devs = devs_data["DEVS"]
                if self._board_id < len(devs):
                    dev = devs[self._board_id]
                    # Check multiple status indicators
                    status = dev.get("Status", "")
                    enabled = dev.get("Enabled", "")
                    
                    # Check for various "enabled" indicators
                    if status.lower() in ["alive", "active", "enabled", "mining"]:
                        return True
                    elif enabled and str(enabled).lower() in ["true", "yes", "1", "enabled"]:
                        return True
                    elif status.lower() in ["dead", "disabled", "inactive"]:
                        return False
                    
                    # Fallback: check if board has hashrate (indicates it's working)
                    hashrate_fields = ["GHS 5s", "GHS av", "MHS 5s", "Hashrate"]
                    for field in hashrate_fields:
                        hashrate_str = dev.get(field, "0")
                        try:
                            hashrate = float(hashrate_str)
                            return hashrate > 0
                        except (ValueError, TypeError):
                            continue
        return None
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the hashboard using ASC enable command."""
        try:
            # Use working ASC enable command instead of profile changes
            success = await self._client.asc_enable(self._board_id)
            if success:
                await self.coordinator.async_request_refresh()
                _LOGGER.info("Board %s enabled successfully", self._board_id)
            else:
                _LOGGER.error("Failed to enable board %s", self._board_id)
        except Exception as err:
            _LOGGER.error("Error enabling board %s: %s", self._board_id, err)
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the hashboard using ASC disable command."""
        try:
            # Use working ASC disable command instead of profile changes
            success = await self._client.asc_disable(self._board_id)
            if success:
                await self.coordinator.async_request_refresh()
                _LOGGER.info("Board %s disabled successfully", self._board_id)
            else:
                _LOGGER.error("Failed to disable board %s", self._board_id)
        except Exception as err:
            _LOGGER.error("Error disabling board %s: %s", self._board_id, err)
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if self.coordinator.data and "devices" in self.coordinator.data:
            devs_data = self.coordinator.data["devices"]
            if "DEVS" in devs_data:
                devs = devs_data["DEVS"]
                if self._board_id < len(devs):
                    dev = devs[self._board_id]
                    return {
                        "temperature": dev.get("Temperature"),
                        "frequency": dev.get("Frequency"),
                        "voltage": dev.get("Voltage"),
                        "hashrate_ghs": dev.get("GHS 5s"),
                        "chip_count": dev.get("Chip Count"),
                        "device_elapsed": dev.get("Device Elapsed"),
                        "enabled": dev.get("Enabled"),
                        "control_method": "ASC enable/disable commands",
                    }
        return {}


class SolarMinerMiningSwitch(SolarMinerSwitchEntity):
    """Solar Miner main mining switch."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"{self._display_name} Mining"
        self._attr_unique_id = f"{config_entry.entry_id}_mining_switch"
        self._attr_icon = "mdi:pickaxe"
    
    @property
    def is_on(self) -> bool | None:
        """Return True if mining is active."""
        if self.coordinator.data and "devices" in self.coordinator.data:
            devs_data = self.coordinator.data["devices"]
            if "DEVS" in devs_data:
                devs = devs_data["DEVS"]
                active_boards = 0
                for dev in devs:
                    status = dev.get("Status", "").lower()
                    enabled = dev.get("Enabled", "")
                    
                    # Check if board is active
                    if (status in ["alive", "active", "enabled", "mining"] or
                        str(enabled).lower() in ["true", "yes", "1", "enabled"]):
                        active_boards += 1
                    else:
                        # Fallback: check hashrate
                        for field in ["GHS 5s", "GHS av", "MHS 5s"]:
                            try:
                                hashrate = float(dev.get(field, "0"))
                                if hashrate > 0:
                                    active_boards += 1
                                    break
                            except (ValueError, TypeError):
                                continue
                
                return active_boards > 0
        return None
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start mining using restart command."""
        try:
            success = await self._client.restart_mining()
            if success:
                await self.coordinator.async_request_refresh()
                _LOGGER.info("Mining started via restart command")
            else:
                _LOGGER.error("Failed to start mining")
        except Exception as err:
            _LOGGER.error("Error starting mining: %s", err)
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop mining by disabling all ASC units."""
        try:
            # Disable all 3 hashboards/ASC units
            success_count = 0
            for asc_id in range(3):
                if await self._client.asc_disable(asc_id):
                    success_count += 1
            
            if success_count > 0:
                await self.coordinator.async_request_refresh()
                _LOGGER.info("Mining stopped - disabled %s/3 ASC units", success_count)
            else:
                _LOGGER.error("Failed to stop mining - no ASC units disabled")
        except Exception as err:
            _LOGGER.error("Error stopping mining: %s", err)


class SolarMinerPauseMiningSwitch(SolarMinerSwitchEntity):
    """Solar Miner pause mining switch."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"{self._display_name} Pause Mining"
        self._attr_unique_id = f"{config_entry.entry_id}_pause_mining_switch"
        self._attr_icon = "mdi:pause-circle"
        self._is_paused = False
    
    @property
    def is_on(self) -> bool:
        """Return True if mining is paused."""
        return self._is_paused
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Pause mining by disabling all ASC units."""
        try:
            # Disable all 3 hashboards/ASC units to pause mining
            success_count = 0
            for asc_id in range(3):
                if await self._client.asc_disable(asc_id):
                    success_count += 1
            
            if success_count > 0:
                self._is_paused = True
                await self.coordinator.async_request_refresh()
                _LOGGER.info("Mining paused - disabled %s/3 ASC units for miner %s", success_count, self._config_entry.data['host'])
            else:
                _LOGGER.error("Failed to pause mining for miner %s", self._config_entry.data['host'])
        except Exception as err:
            _LOGGER.error("Error pausing mining: %s", err)
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Resume mining by enabling all ASC units."""
        try:
            # Enable all 3 hashboards/ASC units to resume mining
            success_count = 0
            for asc_id in range(3):
                if await self._client.asc_enable(asc_id):
                    success_count += 1
            
            if success_count > 0:
                self._is_paused = False
                await self.coordinator.async_request_refresh()
                _LOGGER.info("Mining resumed - enabled %s/3 ASC units for miner %s", success_count, self._config_entry.data['host'])
            else:
                _LOGGER.error("Failed to resume mining for miner %s", self._config_entry.data['host'])
        except Exception as err:
            _LOGGER.error("Error resuming mining: %s", err)


class SolarMinerSolarModeSwitch(SolarMinerSwitchEntity):
    """Solar Miner solar mode switch."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"{self._display_name} Solar Mode"
        self._attr_unique_id = f"{config_entry.entry_id}_solar_mode_switch"
        self._attr_icon = "mdi:solar-power"
        self._solar_mode_enabled = False
    
    @property
    def is_on(self) -> bool:
        """Return True if solar mode is enabled."""
        return self._solar_mode_enabled
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable solar mode."""
        self._solar_mode_enabled = True
        self.async_write_ha_state()
        _LOGGER.info("Solar mode enabled for miner %s", self._config_entry.data['host'])
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable solar mode."""
        self._solar_mode_enabled = False
        self.async_write_ha_state()
        _LOGGER.info("Solar mode disabled for miner %s", self._config_entry.data['host'])
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        return {
            "automation_active": self._solar_mode_enabled,
            "sun_curve_following": self._solar_mode_enabled,
        }


class SolarMinerAutoStandbySwitch(SolarMinerSwitchEntity):
    """Solar Miner auto standby switch."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"{self._display_name} Auto Standby"
        self._attr_unique_id = f"{config_entry.entry_id}_auto_standby_switch"
        self._attr_icon = "mdi:power-standby"
        self._auto_standby_enabled = False
        self._minimum_power = 1000  # Default minimum power in watts
    
    @property
    def is_on(self) -> bool:
        """Return True if auto standby is enabled."""
        return self._auto_standby_enabled
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable auto standby mode."""
        self._auto_standby_enabled = True
        self.async_write_ha_state()
        _LOGGER.info("Auto standby enabled for miner %s", self._config_entry.data['host'])
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable auto standby mode."""
        self._auto_standby_enabled = False
        self.async_write_ha_state()
        _LOGGER.info("Auto standby disabled for miner %s", self._config_entry.data['host'])
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        return {
            "minimum_power_watts": self._minimum_power,
            "auto_restart_enabled": self._auto_standby_enabled,
        }
    
    async def set_minimum_power(self, power_watts: int) -> None:
        """Set minimum power threshold for auto standby."""
        self._minimum_power = power_watts
        self.async_write_ha_state()
        _LOGGER.info(
            "Minimum power set to %s watts for miner %s",
            power_watts,
            self._config_entry.data['host']
        )