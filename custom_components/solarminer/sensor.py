"""Solar Miner sensor platform."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
)
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
    """Set up Solar Miner sensor entries."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    entities = [
        # Mining statistics
        SolarMinerHashrateSensor(coordinator, config_entry),
        SolarMinerPowerSensor(coordinator, config_entry),
        SolarMinerTemperatureSensor(coordinator, config_entry),
        SolarMinerFanSpeedSensor(coordinator, config_entry),
        SolarMinerEfficiencySensor(coordinator, config_entry),
        
        # Individual board sensors
        SolarMinerBoardSensor(coordinator, config_entry, 0),
        SolarMinerBoardSensor(coordinator, config_entry, 1),
        SolarMinerBoardSensor(coordinator, config_entry, 2),
        
        # Pool information
        SolarMinerPoolSensor(coordinator, config_entry),
        
        # Solar power sensors
        SolarMinerSolarPowerSensor(coordinator, config_entry),
        SolarMinerSolarEfficiencySensor(coordinator, config_entry),
        
        # Status sensors
        SolarMinerStatusSensor(coordinator, config_entry),
        SolarMinerUptimeSensor(coordinator, config_entry),
    ]
    
    async_add_entities(entities)


class SolarMinerSensorEntity(CoordinatorEntity, SensorEntity):
    """Base Solar Miner sensor entity."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
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


class SolarMinerHashrateSensor(SolarMinerSensorEntity):
    """Solar Miner hashrate sensor."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Hashrate"
        self._attr_unique_id = f"{config_entry.entry_id}_hashrate"
        self._attr_native_unit_of_measurement = "TH/s"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:pickaxe"
    
    @property
    def native_value(self) -> float | None:
        """Return the hashrate."""
        if self.coordinator.data and "summary" in self.coordinator.data:
            summary_data = self.coordinator.data["summary"]
            # LuxOS returns data in SUMMARY array
            if "SUMMARY" in summary_data and len(summary_data["SUMMARY"]) > 0:
                summary_item = summary_data["SUMMARY"][0]
                hashrate_str = summary_item.get("GHS 5s", "0")
                try:
                    # Convert GH/s to TH/s
                    return float(hashrate_str) / 1000
                except (ValueError, TypeError):
                    return None
        return None


class SolarMinerPowerSensor(SolarMinerSensorEntity):
    """Solar Miner power consumption sensor."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Power"
        self._attr_unique_id = f"{config_entry.entry_id}_power"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self) -> float | None:
        """Return the power consumption."""
        if self.coordinator.data and "summary" in self.coordinator.data:
            summary_data = self.coordinator.data["summary"]
            # LuxOS returns data in SUMMARY array
            if "SUMMARY" in summary_data and len(summary_data["SUMMARY"]) > 0:
                summary_item = summary_data["SUMMARY"][0]
                # Try different power field names used by LuxOS
                power_fields = [
                    "Power", "Power Consumption", "Watts", "Power Usage",
                    "Utility", "Work Utility"  # Sometimes LuxOS reports efficiency metrics
                ]
                for power_field in power_fields:
                    power_str = summary_item.get(power_field, "0")
                    try:
                        power_val = float(power_str)
                        if power_val > 0:
                            return power_val
                    except (ValueError, TypeError):
                        continue
                
                # If no direct power reading, estimate from hashrate (S21+ typically 17.5 J/TH)
                hashrate_str = summary_item.get("GHS 5s", "0")
                try:
                    hashrate_ghs = float(hashrate_str)
                    hashrate_ths = hashrate_ghs / 1000
                    estimated_power = hashrate_ths * 17.5  # S21+ efficiency
                    return round(estimated_power) if estimated_power > 0 else None
                except (ValueError, TypeError):
                    pass
        return None


class SolarMinerTemperatureSensor(SolarMinerSensorEntity):
    """Solar Miner temperature sensor."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Temperature"
        self._attr_unique_id = f"{config_entry.entry_id}_temperature"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self) -> float | None:
        """Return the temperature."""
        if self.coordinator.data and "devs" in self.coordinator.data:
            devs_data = self.coordinator.data["devs"]
            # LuxOS returns data in DEVS array
            if "DEVS" in devs_data:
                temps = []
                for dev in devs_data["DEVS"]:
                    # Try different temperature field names
                    for temp_field in ["Temperature", "Temp", "temp1", "temp2", "temp3"]:
                        temp_str = dev.get(temp_field, "0")
                        try:
                            temps.append(float(temp_str))
                        except (ValueError, TypeError):
                            continue
                return max(temps) if temps else None
        return None


class SolarMinerFanSpeedSensor(SolarMinerSensorEntity):
    """Solar Miner fan speed sensor."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Fan Speed"
        self._attr_unique_id = f"{config_entry.entry_id}_fan_speed"
        self._attr_native_unit_of_measurement = "RPM"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:fan"
    
    @property
    def native_value(self) -> float | None:
        """Return the fan speed."""
        if self.coordinator.data and "summary" in self.coordinator.data:
            summary_data = self.coordinator.data["summary"]
            if "SUMMARY" in summary_data and len(summary_data["SUMMARY"]) > 0:
                summary_item = summary_data["SUMMARY"][0]
                # Try different fan speed field names used by LuxOS
                fan_fields = [
                    "Fan Speed In", "Fan1", "Fan2", "FanSpeedIn", "Fan Speed",
                    "Fan1 Speed", "Fan2 Speed", "Fan 1", "Fan 2"
                ]
                for fan_field in fan_fields:
                    fan_speed_str = summary_item.get(fan_field, "0")
                    try:
                        fan_speed = float(fan_speed_str)
                        if fan_speed > 0:
                            return fan_speed
                    except (ValueError, TypeError):
                        continue
                        
        # Also try to get fan speed from stats if not in summary
        if self.coordinator.data and "stats" in self.coordinator.data:
            stats_data = self.coordinator.data["stats"]
            if "STATS" in stats_data:
                for stat_item in stats_data["STATS"]:
                    for fan_field in ["Fan1", "Fan2", "fan1", "fan2"]:
                        fan_speed_str = stat_item.get(fan_field, "0")
                        try:
                            fan_speed = float(fan_speed_str)
                            if fan_speed > 0:
                                return fan_speed
                        except (ValueError, TypeError):
                            continue
        return None


class SolarMinerEfficiencySensor(SolarMinerSensorEntity):
    """Solar Miner efficiency sensor."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Efficiency"
        self._attr_unique_id = f"{config_entry.entry_id}_efficiency"
        self._attr_native_unit_of_measurement = "J/TH"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:lightning-bolt"
    
    @property
    def native_value(self) -> float | None:
        """Return the efficiency in J/TH."""
        if self.coordinator.data and "summary" in self.coordinator.data:
            summary_data = self.coordinator.data["summary"]
            if "SUMMARY" in summary_data and len(summary_data["SUMMARY"]) > 0:
                summary = summary_data["SUMMARY"][0]
                try:
                    # Try different power field names
                    power = 0
                    for power_field in ["Power", "Power Consumption", "Watts"]:
                        power_str = summary.get(power_field, "0")
                        try:
                            power = float(power_str)
                            if power > 0:
                                break
                        except (ValueError, TypeError):
                            continue
                    
                    # Get hashrate
                    hashrate_ghs = float(summary.get("GHS 5s", "0"))
                    hashrate_ths = hashrate_ghs / 1000
                    
                    if hashrate_ths > 0 and power > 0:
                        return round(power / hashrate_ths, 2)  # W/TH (J/TH = W/TH for continuous operation)
                except (ValueError, TypeError, ZeroDivisionError):
                    pass
        return None


class SolarMinerBoardSensor(SolarMinerSensorEntity):
    """Solar Miner hashboard sensor."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        config_entry: ConfigEntry,
        board_id: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._board_id = board_id
        self._attr_name = f"Solar Miner {config_entry.data['host']} Board {board_id}"
        self._attr_unique_id = f"{config_entry.entry_id}_board_{board_id}"
        self._attr_native_unit_of_measurement = "TH/s"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:memory"
    
    @property
    def native_value(self) -> float | None:
        """Return the board hashrate."""
        if self.coordinator.data and "devs" in self.coordinator.data:
            devs_data = self.coordinator.data["devs"]
            if "DEVS" in devs_data:
                devs = devs_data["DEVS"]
                if self._board_id < len(devs):
                    dev = devs[self._board_id]
                    # Try different hashrate field names
                    hashrate_fields = [
                        "GHS 5s", "GHS av", "MHS 5s", "MHS av", 
                        "Hashrate", "Hash Rate", "5s", "Avg"
                    ]
                    for hashrate_field in hashrate_fields:
                        hashrate_str = dev.get(hashrate_field, "0")
                        try:
                            hashrate = float(hashrate_str)
                            if hashrate > 0:
                                # Convert based on unit
                                if hashrate_field.startswith("GHS") or "GHS" in hashrate_field:
                                    return hashrate / 1000  # GH/s to TH/s
                                elif hashrate_field.startswith("MHS") or "MHS" in hashrate_field:
                                    return hashrate / 1000000  # MH/s to TH/s
                                else:
                                    # For S21+, individual boards typically show 60-80 TH/s
                                    # If value is very high, it's likely GH/s
                                    if hashrate > 1000:
                                        return hashrate / 1000  # GH/s to TH/s
                                    else:
                                        return hashrate  # Already in TH/s
                        except (ValueError, TypeError):
                            continue
                            
                # If no individual board data, estimate from total hashrate
                if self.coordinator.data and "summary" in self.coordinator.data:
                    summary_data = self.coordinator.data["summary"]
                    if "SUMMARY" in summary_data and len(summary_data["SUMMARY"]) > 0:
                        summary_item = summary_data["SUMMARY"][0]
                        total_hashrate_str = summary_item.get("GHS 5s", "0")
                        try:
                            total_hashrate_ghs = float(total_hashrate_str)
                            total_hashrate_ths = total_hashrate_ghs / 1000
                            # S21+ has 3 boards, distribute evenly
                            return round(total_hashrate_ths / 3, 2)
                        except (ValueError, TypeError):
                            pass
        return None
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if self.coordinator.data and "devs" in self.coordinator.data:
            devs_data = self.coordinator.data["devs"]
            if "DEVS" in devs_data:
                devs = devs_data["DEVS"]
                if self._board_id < len(devs):
                    dev = devs[self._board_id]
                    return {
                        "temperature": dev.get("Temperature"),
                        "frequency": dev.get("Frequency"),
                        "voltage": dev.get("Voltage"),
                        "status": dev.get("Status"),
                        "chip_count": dev.get("Chip Count"),
                        "device_elapsed": dev.get("Device Elapsed"),
                        "enabled": dev.get("Enabled"),
                    }
        return {}


class SolarMinerPoolSensor(SolarMinerSensorEntity):
    """Solar Miner pool sensor."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Pool"
        self._attr_unique_id = f"{config_entry.entry_id}_pool"
        self._attr_icon = "mdi:server-network"
    
    @property
    def native_value(self) -> str | None:
        """Return the active pool."""
        if self.coordinator.data and "pools" in self.coordinator.data:
            pools = self.coordinator.data["pools"].get("POOLS", [])
            for pool in pools:
                if pool.get("Stratum Active"):
                    return pool.get("URL", "Unknown")
        return None
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if self.coordinator.data and "pools" in self.coordinator.data:
            pools = self.coordinator.data["pools"].get("POOLS", [])
            active_pool = None
            for pool in pools:
                if pool.get("Stratum Active"):
                    active_pool = pool
                    break
            
            if active_pool:
                return {
                    "status": active_pool.get("Status"),
                    "user": active_pool.get("User"),
                    "accepted": active_pool.get("Accepted"),
                    "rejected": active_pool.get("Rejected"),
                    "difficulty": active_pool.get("Difficulty"),
                    "last_share_time": active_pool.get("Last Share Time"),
                }
        return {}


class SolarMinerSolarPowerSensor(SolarMinerSensorEntity):
    """Solar Miner solar power sensor."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Solar Power"
        self._attr_unique_id = f"{config_entry.entry_id}_solar_power"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:solar-power"
    
    @property
    def native_value(self) -> float | None:
        """Return the available solar power."""
        # This would be set through the solar power input
        # For now, return a placeholder value
        return getattr(self, "_solar_power", 0)


class SolarMinerSolarEfficiencySensor(SolarMinerSensorEntity):
    """Solar Miner solar efficiency sensor."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Solar Efficiency"
        self._attr_unique_id = f"{config_entry.entry_id}_solar_efficiency"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:solar-power-variant"
    
    @property
    def native_value(self) -> float | None:
        """Return the solar efficiency percentage."""
        if self.coordinator.data and "summary" in self.coordinator.data:
            try:
                power_consumption = float(self.coordinator.data["summary"].get("Power", "0"))
                solar_power = getattr(self, "_solar_power", 0)
                
                if solar_power > 0:
                    efficiency = min(100, (power_consumption / solar_power) * 100)
                    return round(efficiency, 1)
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        return None


class SolarMinerStatusSensor(SolarMinerSensorEntity):
    """Solar Miner status sensor."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Status"
        self._attr_unique_id = f"{config_entry.entry_id}_status"
        self._attr_icon = "mdi:information"
    
    @property
    def native_value(self) -> str | None:
        """Return the miner status."""
        if self.coordinator.data and "summary" in self.coordinator.data:
            summary_data = self.coordinator.data["summary"]
            if "SUMMARY" in summary_data and len(summary_data["SUMMARY"]) > 0:
                summary_item = summary_data["SUMMARY"][0]
                # Try different status field names
                for status_field in ["Status", "STATUS", "State", "Alive", "Miner Status"]:
                    status = summary_item.get(status_field)
                    if status and status != "Unknown":
                        return status
                        
                # Check if miner is working based on hashrate
                hashrate_str = summary_item.get("GHS 5s", "0")
                try:
                    hashrate = float(hashrate_str)
                    return "Mining" if hashrate > 0 else "Idle"
                except (ValueError, TypeError):
                    pass
        return "Unknown"


class SolarMinerUptimeSensor(SolarMinerSensorEntity):
    """Solar Miner uptime sensor."""
    
    def __init__(
        self,
        coordinator: SolarMinerDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"Solar Miner {config_entry.data['host']} Uptime"
        self._attr_unique_id = f"{config_entry.entry_id}_uptime"
        self._attr_native_unit_of_measurement = "days"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:timer"
    
    @property
    def native_value(self) -> float | None:
        """Return the uptime in days."""
        if self.coordinator.data and "summary" in self.coordinator.data:
            summary_data = self.coordinator.data["summary"]
            if "SUMMARY" in summary_data and len(summary_data["SUMMARY"]) > 0:
                summary_item = summary_data["SUMMARY"][0]
                elapsed_str = summary_item.get("Elapsed", "0")
                try:
                    elapsed_seconds = float(elapsed_str)
                    return round(elapsed_seconds / 86400, 2)  # Convert to days
                except (ValueError, TypeError):
                    return None
        return None