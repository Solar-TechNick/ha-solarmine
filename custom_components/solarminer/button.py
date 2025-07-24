"""Solar Miner button platform."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MINING_PRESETS, POWER_PROFILES, CONF_ALIAS
from . import SolarMinerDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Solar Miner button entries."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    client = hass.data[DOMAIN][config_entry.entry_id]["client"]
    
    entities = [
        # Mining control buttons
        SolarMinerPauseButton(coordinator, client, config_entry),
        SolarMinerResumeButton(coordinator, client, config_entry),
        SolarMinerSolarMaxButton(coordinator, client, config_entry),
        SolarMinerEcoModeButton(coordinator, client, config_entry),
        
        # Profile control buttons
        SolarMinerMaxPowerButton(coordinator, client, config_entry),
        SolarMinerBalancedButton(coordinator, client, config_entry),
        SolarMinerUltraEcoButton(coordinator, client, config_entry),
        
        # Solar control buttons
        SolarMinerUpdateSolarPowerButton(coordinator, client, config_entry),
        SolarMinerNightMode30Button(coordinator, client, config_entry),
        SolarMinerNightMode15Button(coordinator, client, config_entry),
        SolarMinerStandbyButton(coordinator, client, config_entry),
        SolarMinerPeakSolarButton(coordinator, client, config_entry),
        
        # System control buttons
        SolarMinerRebootButton(coordinator, client, config_entry),
    ]
    
    async_add_entities(entities)


class SolarMinerButtonEntity(CoordinatorEntity, ButtonEntity):
    """Base Solar Miner button entity."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._client = client
        self._config_entry = config_entry
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


class SolarMinerPauseButton(SolarMinerButtonEntity):
    """Solar Miner pause button."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"{self._display_name} Pause"
        self._attr_unique_id = f"{config_entry.entry_id}_pause_button"
        self._attr_icon = "mdi:pause"
    
    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            success = await self._client.pause_mining()
            if success:
                await self.coordinator.async_request_refresh()
                _LOGGER.info("Mining paused for miner %s", self._config_entry.data['host'])
            else:
                _LOGGER.error("Failed to pause mining for miner %s", self._config_entry.data['host'])
        except Exception as err:
            _LOGGER.error("Error pausing mining: %s", err)


class SolarMinerResumeButton(SolarMinerButtonEntity):
    """Solar Miner resume button."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"{self._display_name} Resume"
        self._attr_unique_id = f"{config_entry.entry_id}_resume_button"
        self._attr_icon = "mdi:play"
    
    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            success = await self._client.resume_mining()
            if success:
                await self.coordinator.async_request_refresh()
                _LOGGER.info("Mining resumed for miner %s", self._config_entry.data['host'])
            else:
                _LOGGER.error("Failed to resume mining for miner %s", self._config_entry.data['host'])
        except Exception as err:
            _LOGGER.error("Error resuming mining: %s", err)


class SolarMinerSolarMaxButton(SolarMinerButtonEntity):
    """Solar Miner solar max button."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"{self._display_name} Solar Max"
        self._attr_unique_id = f"{config_entry.entry_id}_solar_max_button"
        self._attr_icon = "mdi:solar-power-variant"
    
    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            power_watts = MINING_PRESETS["solar_max"]["power_watts"]
            success = await self._client.set_power_limit(power_watts)
            if success:
                await self._client.resume_mining()
                await self.coordinator.async_request_refresh()
                _LOGGER.info(
                    "Solar Max mode set (%s watts) for miner %s",
                    power_watts,
                    self._config_entry.data['host']
                )
            else:
                _LOGGER.error("Failed to set Solar Max mode for miner %s", self._config_entry.data['host'])
        except Exception as err:
            _LOGGER.error("Error setting Solar Max mode: %s", err)


class SolarMinerEcoModeButton(SolarMinerButtonEntity):
    """Solar Miner eco mode button."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"{self._display_name} Eco Mode"
        self._attr_unique_id = f"{config_entry.entry_id}_eco_mode_button"
        self._attr_icon = "mdi:leaf"
    
    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            power_watts = MINING_PRESETS["eco_mode"]["power_watts"]
            success = await self._client.set_power_limit(power_watts)
            if success:
                await self._client.resume_mining()
                await self.coordinator.async_request_refresh()
                _LOGGER.info(
                    "Eco Mode set (%s watts) for miner %s",
                    power_watts,
                    self._config_entry.data['host']
                )
            else:
                _LOGGER.error("Failed to set Eco Mode for miner %s", self._config_entry.data['host'])
        except Exception as err:
            _LOGGER.error("Error setting Eco Mode: %s", err)


class SolarMinerMaxPowerButton(SolarMinerButtonEntity):
    """Solar Miner max power button."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"{self._display_name} Max Power"
        self._attr_unique_id = f"{config_entry.entry_id}_max_power_button"
        self._attr_icon = "mdi:lightning-bolt"
    
    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            host = self._config_entry.data['host']
            _LOGGER.warning(
                "LuxOS profile changes require web authentication. "
                "Please change to Max Power profile manually at http://%s", 
                host
            )
            
            # Still attempt the change in case authentication is available
            profile = POWER_PROFILES["max_power"]
            success = await self._client.set_power_mode(profile['overclock'])
            
            if success:
                await self.coordinator.async_request_refresh()
                _LOGGER.info("Max Power profile applied for miner %s", host)
            else:
                _LOGGER.info(
                    "Profile change failed (expected for LuxOS). "
                    "Please use web interface at http://%s to change to Max Power profile.", 
                    host
                )
        except Exception as err:
            _LOGGER.error("Error with Max Power profile change: %s", err)


class SolarMinerBalancedButton(SolarMinerButtonEntity):
    """Solar Miner balanced button."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"{self._display_name} Balanced"
        self._attr_unique_id = f"{config_entry.entry_id}_balanced_button"
        self._attr_icon = "mdi:scale-balance"
    
    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            host = self._config_entry.data['host']
            _LOGGER.warning(
                "LuxOS profile changes require web authentication. "
                "Please change to Balanced profile manually at http://%s", 
                host
            )
            
            # Still attempt the change in case authentication is available
            profile = POWER_PROFILES["balanced"]
            success = await self._client.set_power_mode(profile['overclock'])
            
            if success:
                await self.coordinator.async_request_refresh()
                _LOGGER.info("Balanced profile applied for miner %s", host)
            else:
                _LOGGER.info(
                    "Profile change failed (expected for LuxOS). "
                    "Please use web interface at http://%s to change to Balanced profile.", 
                    host
                )
        except Exception as err:
            _LOGGER.error("Error with Balanced profile change: %s", err)


class SolarMinerUltraEcoButton(SolarMinerButtonEntity):
    """Solar Miner ultra eco button."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"{self._display_name} Ultra Eco"
        self._attr_unique_id = f"{config_entry.entry_id}_ultra_eco_button"
        self._attr_icon = "mdi:leaf-circle"
    
    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            host = self._config_entry.data['host']
            _LOGGER.warning(
                "LuxOS profile changes require web authentication. "
                "Please change to Ultra Eco profile manually at http://%s", 
                host
            )
            
            # Still attempt the change in case authentication is available
            profile = POWER_PROFILES["ultra_eco"]
            success = await self._client.set_power_mode(profile['overclock'])
            
            if success:
                await self.coordinator.async_request_refresh()
                _LOGGER.info("Ultra Eco profile applied for miner %s", host)
            else:
                _LOGGER.info(
                    "Profile change failed (expected for LuxOS). "
                    "Please use web interface at http://%s to change to Ultra Eco profile.", 
                    host
                )
        except Exception as err:
            _LOGGER.error("Error with Ultra Eco profile change: %s", err)


class SolarMinerUpdateSolarPowerButton(SolarMinerButtonEntity):
    """Solar Miner update solar power button."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"{self._display_name} Update Solar Power"
        self._attr_unique_id = f"{config_entry.entry_id}_update_solar_power_button"
        self._attr_icon = "mdi:solar-power"
    
    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # This would trigger an update of solar power from external source
            # For now, just refresh the coordinator
            await self.coordinator.async_request_refresh()
            _LOGGER.info("Solar power updated for miner %s", self._config_entry.data['host'])
        except Exception as err:
            _LOGGER.error("Error updating solar power: %s", err)


class SolarMinerNightMode30Button(SolarMinerButtonEntity):
    """Solar Miner night mode 30% button."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"{self._display_name} Night Mode 30%"
        self._attr_unique_id = f"{config_entry.entry_id}_night_mode_30_button"
        self._attr_icon = "mdi:weather-night"
    
    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # Calculate 30% power - assuming base power consumption
            base_power = 3250  # Typical S19j Pro+ power consumption
            target_power = int(base_power * 0.3)
            
            success = await self._client.set_power_limit(target_power)
            if success:
                await self.coordinator.async_request_refresh()
                _LOGGER.info(
                    "Night Mode 30% (%s watts) set for miner %s",
                    target_power,
                    self._config_entry.data['host']
                )
            else:
                _LOGGER.error("Failed to set Night Mode 30% for miner %s", self._config_entry.data['host'])
        except Exception as err:
            _LOGGER.error("Error setting Night Mode 30%: %s", err)


class SolarMinerNightMode15Button(SolarMinerButtonEntity):
    """Solar Miner night mode 15% button."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"{self._display_name} Night Mode 15%"
        self._attr_unique_id = f"{config_entry.entry_id}_night_mode_15_button"
        self._attr_icon = "mdi:sleep"
    
    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # Calculate 15% power
            base_power = 3250  # Typical S19j Pro+ power consumption
            target_power = int(base_power * 0.15)
            
            success = await self._client.set_power_limit(target_power)
            if success:
                await self.coordinator.async_request_refresh()
                _LOGGER.info(
                    "Night Mode 15% (%s watts) set for miner %s",
                    target_power,
                    self._config_entry.data['host']
                )
            else:
                _LOGGER.error("Failed to set Night Mode 15% for miner %s", self._config_entry.data['host'])
        except Exception as err:
            _LOGGER.error("Error setting Night Mode 15%: %s", err)


class SolarMinerStandbyButton(SolarMinerButtonEntity):
    """Solar Miner standby button."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"{self._display_name} Standby"
        self._attr_unique_id = f"{config_entry.entry_id}_standby_button"
        self._attr_icon = "mdi:power-standby"
    
    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            success = await self._client.pause_mining()
            if success:
                await self.coordinator.async_request_refresh()
                _LOGGER.info("Standby mode activated for miner %s", self._config_entry.data['host'])
            else:
                _LOGGER.error("Failed to activate standby mode for miner %s", self._config_entry.data['host'])
        except Exception as err:
            _LOGGER.error("Error activating standby mode: %s", err)


class SolarMinerPeakSolarButton(SolarMinerButtonEntity):
    """Solar Miner peak solar button."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"{self._display_name} Peak Solar"
        self._attr_unique_id = f"{config_entry.entry_id}_peak_solar_button"
        self._attr_icon = "mdi:weather-sunny"
    
    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # Set 120% power for peak solar
            base_power = 3250  # Typical S19j Pro+ power consumption
            target_power = int(base_power * 1.2)
            
            success = await self._client.set_power_limit(target_power)
            if success:
                await self._client.resume_mining()
                await self.coordinator.async_request_refresh()
                _LOGGER.info(
                    "Peak Solar mode (120% - %s watts) set for miner %s",
                    target_power,
                    self._config_entry.data['host']
                )
            else:
                _LOGGER.error("Failed to set Peak Solar mode for miner %s", self._config_entry.data['host'])
        except Exception as err:
            _LOGGER.error("Error setting Peak Solar mode: %s", err)


class SolarMinerRebootButton(SolarMinerButtonEntity):
    """Solar Miner reboot button."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = f"{self._display_name} Reboot"
        self._attr_unique_id = f"{config_entry.entry_id}_reboot_button"
        self._attr_icon = "mdi:restart"
    
    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            success = await self._client.reboot()
            if success:
                _LOGGER.info("Reboot initiated for miner %s", self._config_entry.data['host'])
            else:
                _LOGGER.error("Failed to reboot miner %s", self._config_entry.data['host'])
        except Exception as err:
            _LOGGER.error("Error rebooting miner: %s", err)