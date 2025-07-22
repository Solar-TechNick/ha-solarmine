"""Solar Miner switch platform."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
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
        self._attr_name = f"Solar Miner {config_entry.data['host']} Board {board_id}"
        self._attr_unique_id = f"{config_entry.entry_id}_board_{board_id}_switch"
        self._attr_icon = "mdi:memory"
    
    @property
    def is_on(self) -> bool | None:
        """Return True if the hashboard is enabled."""
        if self.coordinator.data and "devs" in self.coordinator.data:
            devs = self.coordinator.data["devs"].get("DEVS", [])
            if self._board_id < len(devs):
                status = devs[self._board_id].get("Status", "")
                return status.lower() in ["alive", "active", "enabled"]
        return None
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the hashboard."""
        try:
            success = await self._client.enable_board(self._board_id)
            if success:
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to enable board %s", self._board_id)
        except Exception as err:
            _LOGGER.error("Error enabling board %s: %s", self._board_id, err)
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the hashboard."""
        try:
            success = await self._client.disable_board(self._board_id)
            if success:
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to disable board %s", self._board_id)
        except Exception as err:
            _LOGGER.error("Error disabling board %s: %s", self._board_id, err)
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if self.coordinator.data and "devs" in self.coordinator.data:
            devs = self.coordinator.data["devs"].get("DEVS", [])
            if self._board_id < len(devs):
                dev = devs[self._board_id]
                return {
                    "temperature": dev.get("Temperature"),
                    "frequency": dev.get("Frequency"),
                    "voltage": dev.get("Voltage"),
                    "hashrate_ghs": dev.get("GHS 5s"),
                    "chip_count": dev.get("Chip Count"),
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
        self._attr_name = f"Solar Miner {config_entry.data['host']} Mining"
        self._attr_unique_id = f"{config_entry.entry_id}_mining_switch"
        self._attr_icon = "mdi:pickaxe"
    
    @property
    def is_on(self) -> bool | None:
        """Return True if mining is active."""
        if self.coordinator.data and "devs" in self.coordinator.data:
            devs = self.coordinator.data["devs"].get("DEVS", [])
            active_boards = sum(
                1 for dev in devs
                if dev.get("Status", "").lower() in ["alive", "active", "enabled"]
            )
            return active_boards > 0
        return None
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start mining (enable all boards)."""
        try:
            success = await self._client.resume_mining()
            if success:
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to start mining")
        except Exception as err:
            _LOGGER.error("Error starting mining: %s", err)
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop mining (disable all boards)."""
        try:
            success = await self._client.pause_mining()
            if success:
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to stop mining")
        except Exception as err:
            _LOGGER.error("Error stopping mining: %s", err)


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
        self._attr_name = f"Solar Miner {config_entry.data['host']} Solar Mode"
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
        self._attr_name = f"Solar Miner {config_entry.data['host']} Auto Standby"
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