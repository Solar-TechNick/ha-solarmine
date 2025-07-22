"""Solar Miner number platform."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower, UnitOfTemperature, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, TEMP_PROTECTION_THRESHOLD
from . import SolarMinerDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Solar Miner number entries."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    client = hass.data[DOMAIN][config_entry.entry_id]["client"]
    
    entities = [
        # Solar power controls
        SolarMinerSolarPowerInput(coordinator, client, config_entry),
        SolarMinerPowerLimitInput(coordinator, client, config_entry),
        SolarMinerMinimumPowerInput(coordinator, client, config_entry),
        
        # Temperature controls
        SolarMinerTempProtectionInput(coordinator, client, config_entry),
        
        # Performance controls
        SolarMinerPerformanceInput(coordinator, client, config_entry),
        
        # Automation settings
        SolarMinerAutomationIntervalInput(coordinator, client, config_entry),
    ]
    
    async_add_entities(entities)


class SolarMinerNumberEntity(CoordinatorEntity, NumberEntity):
    """Base Solar Miner number entity."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
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


class SolarMinerSolarPowerInput(SolarMinerNumberEntity):
    """Solar Miner solar power input."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Solar Power"
        self._attr_unique_id = f"{config_entry.entry_id}_solar_power_input"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_native_min_value = 0
        self._attr_native_max_value = 50000
        self._attr_native_step = 100
        self._attr_icon = "mdi:solar-power"
        self._solar_power = 0
    
    @property
    def native_value(self) -> float:
        """Return the current solar power value."""
        return self._solar_power
    
    async def async_set_native_value(self, value: float) -> None:
        """Set the solar power value."""
        self._solar_power = value
        self.async_write_ha_state()
        _LOGGER.info(
            "Solar power set to %s watts for miner %s",
            value,
            self._config_entry.data['host']
        )
        
        # Trigger solar automation if enabled
        await self._trigger_solar_automation()
    
    async def _trigger_solar_automation(self) -> None:
        """Trigger solar power automation."""
        # This would implement the solar automation logic
        # For now, just log the action
        _LOGGER.info(
            "Solar automation triggered with %s watts for miner %s",
            self._solar_power,
            self._config_entry.data['host']
        )


class SolarMinerPowerLimitInput(SolarMinerNumberEntity):
    """Solar Miner power limit input."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Power Limit"
        self._attr_unique_id = f"{config_entry.entry_id}_power_limit_input"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_native_min_value = 100
        self._attr_native_max_value = 5000
        self._attr_native_step = 50
        self._attr_icon = "mdi:flash"
        self._power_limit = 3250  # Default for S19j Pro+
    
    @property
    def native_value(self) -> float:
        """Return the current power limit value."""
        return self._power_limit
    
    async def async_set_native_value(self, value: float) -> None:
        """Set the power limit value."""
        try:
            success = await self._client.set_power_limit(int(value))
            if success:
                self._power_limit = value
                self.async_write_ha_state()
                await self.coordinator.async_request_refresh()
                _LOGGER.info(
                    "Power limit set to %s watts for miner %s",
                    value,
                    self._config_entry.data['host']
                )
            else:
                _LOGGER.error("Failed to set power limit for miner %s", self._config_entry.data['host'])
        except Exception as err:
            _LOGGER.error("Error setting power limit: %s", err)


class SolarMinerMinimumPowerInput(SolarMinerNumberEntity):
    """Solar Miner minimum power input for auto standby."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Minimum Power"
        self._attr_unique_id = f"{config_entry.entry_id}_minimum_power_input"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_native_min_value = 0
        self._attr_native_max_value = 5000
        self._attr_native_step = 50
        self._attr_icon = "mdi:power-standby"
        self._minimum_power = 1000
    
    @property
    def native_value(self) -> float:
        """Return the current minimum power value."""
        return self._minimum_power
    
    async def async_set_native_value(self, value: float) -> None:
        """Set the minimum power value."""
        self._minimum_power = value
        self.async_write_ha_state()
        _LOGGER.info(
            "Minimum power threshold set to %s watts for miner %s",
            value,
            self._config_entry.data['host']
        )


class SolarMinerTempProtectionInput(SolarMinerNumberEntity):
    """Solar Miner temperature protection input."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Temp Protection"
        self._attr_unique_id = f"{config_entry.entry_id}_temp_protection_input"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_native_min_value = 60
        self._attr_native_max_value = 90
        self._attr_native_step = 1
        self._attr_icon = "mdi:thermometer-alert"
        self._temp_threshold = TEMP_PROTECTION_THRESHOLD
    
    @property
    def native_value(self) -> float:
        """Return the current temperature threshold."""
        return self._temp_threshold
    
    async def async_set_native_value(self, value: float) -> None:
        """Set the temperature protection threshold."""
        try:
            success = await self._client.set_temp_control(value)
            if success:
                self._temp_threshold = value
                self.async_write_ha_state()
                _LOGGER.info(
                    "Temperature protection set to %s°C for miner %s",
                    value,
                    self._config_entry.data['host']
                )
            else:
                _LOGGER.error("Failed to set temperature protection for miner %s", self._config_entry.data['host'])
        except Exception as err:
            _LOGGER.error("Error setting temperature protection: %s", err)


class SolarMinerPerformanceInput(SolarMinerNumberEntity):
    """Solar Miner performance input (50% to 130%)."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Performance"
        self._attr_unique_id = f"{config_entry.entry_id}_performance_input"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_native_min_value = 50
        self._attr_native_max_value = 130
        self._attr_native_step = 5
        self._attr_icon = "mdi:speedometer"
        self._performance = 100
    
    @property
    def native_value(self) -> float:
        """Return the current performance value."""
        return self._performance
    
    async def async_set_native_value(self, value: float) -> None:
        """Set the performance value."""
        try:
            # Calculate overclock level based on percentage
            if value == 100:
                profile = "default"
            elif value > 100:
                overclock_level = int((value - 100) / 10)
                profile = f"overclock_{overclock_level}"
            else:
                underclock_level = int((100 - value) / 10)
                profile = f"underclock_{underclock_level}"
            
            success = await self._client.set_profile(profile)
            if success:
                self._performance = value
                self.async_write_ha_state()
                await self.coordinator.async_request_refresh()
                _LOGGER.info(
                    "Performance set to %s%% (%s) for miner %s",
                    value,
                    profile,
                    self._config_entry.data['host']
                )
            else:
                _LOGGER.error("Failed to set performance for miner %s", self._config_entry.data['host'])
        except Exception as err:
            _LOGGER.error("Error setting performance: %s", err)


class SolarMinerAutomationIntervalInput(SolarMinerNumberEntity):
    """Solar Miner automation interval input."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Automation Interval"
        self._attr_unique_id = f"{config_entry.entry_id}_automation_interval_input"
        self._attr_native_unit_of_measurement = "minutes"
        self._attr_native_min_value = 1
        self._attr_native_max_value = 60
        self._attr_native_step = 1
        self._attr_icon = "mdi:timer"
        self._automation_interval = 10
    
    @property
    def native_value(self) -> float:
        """Return the current automation interval."""
        return self._automation_interval
    
    async def async_set_native_value(self, value: float) -> None:
        """Set the automation interval."""
        self._automation_interval = value
        self.async_write_ha_state()
        _LOGGER.info(
            "Automation interval set to %s minutes for miner %s",
            value,
            self._config_entry.data['host']
        )