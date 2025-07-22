"""Solar Miner automation system."""
from __future__ import annotations

import asyncio
import logging
import math
from datetime import datetime, time, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import DOMAIN, AUTO_REFRESH_INTERVAL

_LOGGER = logging.getLogger(__name__)


class SolarMinerAutomation:
    """Solar miner automation system."""
    
    def __init__(self, hass: HomeAssistant, client, coordinator, config_entry) -> None:
        """Initialize automation system."""
        self.hass = hass
        self.client = client
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.host = config_entry.data["host"]
        
        # Automation settings
        self.automation_enabled = False
        self.sun_curve_enabled = False
        self.auto_standby_enabled = False
        self.minimum_power_threshold = 1000
        self.automation_interval = 10  # minutes
        
        # Solar and time tracking
        self.current_solar_power = 0
        self.last_automation_run = None
        self.sun_curve_data = self._generate_sun_curve()
        
        # Automation state
        self.current_power_target = 0
        self.active_boards = [True, True, True]  # Track which boards are active
        
        # Setup automation timer
        self._unsub_automation = None
        self._setup_automation_timer()
    
    def _generate_sun_curve(self) -> dict[int, float]:
        """Generate a 24-hour sun curve with power percentages."""
        curve = {}
        
        # Define key points in the sun curve (hour: power_percentage)
        key_points = {
            0: 0.0,    # Midnight - no solar
            6: 0.0,    # Dawn - no solar yet
            7: 0.1,    # Early morning - minimal solar
            8: 0.2,    # Morning - increasing solar
            9: 0.4,    # Mid-morning - good solar
            10: 0.6,   # Late morning - strong solar
            11: 0.8,   # Pre-noon - very strong solar
            12: 1.0,   # Noon - peak solar
            13: 1.0,   # Early afternoon - peak solar
            14: 0.9,   # Afternoon - still strong
            15: 0.7,   # Late afternoon - decreasing
            16: 0.5,   # Evening approach - moderate
            17: 0.3,   # Evening - weak solar
            18: 0.1,   # Sunset - minimal solar
            19: 0.0,   # Night - no solar
            23: 0.0,   # Late night - no solar
        }
        
        # Interpolate for all 24 hours
        for hour in range(24):
            if hour in key_points:
                curve[hour] = key_points[hour]
            else:
                # Find surrounding points for interpolation
                before_hour = max([h for h in key_points.keys() if h < hour], default=0)
                after_hour = min([h for h in key_points.keys() if h > hour], default=23)
                
                if before_hour == after_hour:
                    curve[hour] = key_points[before_hour]
                else:
                    # Linear interpolation
                    before_power = key_points[before_hour]
                    after_power = key_points[after_hour]
                    ratio = (hour - before_hour) / (after_hour - before_hour)
                    curve[hour] = before_power + (after_power - before_power) * ratio
        
        return curve
    
    def _setup_automation_timer(self) -> None:
        """Setup the automation timer."""
        if self._unsub_automation:
            self._unsub_automation()
        
        self._unsub_automation = async_track_time_interval(
            self.hass,
            self._automation_callback,
            timedelta(minutes=self.automation_interval)
        )
        _LOGGER.info("Solar automation timer set for %s minute intervals", self.automation_interval)
    
    @callback
    async def _automation_callback(self, now: datetime) -> None:
        """Automation callback triggered by timer."""
        if not self.automation_enabled:
            return
        
        try:
            await self._run_automation()
            self.last_automation_run = now
        except Exception as err:
            _LOGGER.error("Error running solar automation: %s", err)
    
    async def _run_automation(self) -> None:
        """Run the main automation logic."""
        current_time = dt_util.now()
        current_hour = current_time.hour
        
        _LOGGER.debug("Running solar automation for miner %s at %s", self.host, current_time)
        
        # Determine target power based on mode
        if self.sun_curve_enabled:
            target_power = self._calculate_sun_curve_power(current_hour)
        else:
            target_power = self.current_solar_power
        
        # Apply auto standby logic
        if self.auto_standby_enabled and target_power < self.minimum_power_threshold:
            await self._enter_standby_mode()
            return
        
        # Apply power management
        await self._apply_power_management(target_power)
        
        # Apply temperature protection
        await self._check_temperature_protection()
        
        # Log automation status
        _LOGGER.info(
            "Solar automation applied for miner %s: target_power=%sW, mode=%s",
            self.host,
            target_power,
            "sun_curve" if self.sun_curve_enabled else "manual"
        )
    
    def _calculate_sun_curve_power(self, hour: int) -> float:
        """Calculate power based on sun curve for given hour."""
        curve_percentage = self.sun_curve_data.get(hour, 0.0)
        max_solar_power = 5000  # Maximum solar power assumption
        return max_solar_power * curve_percentage
    
    async def _apply_power_management(self, target_power: float) -> None:
        """Apply power management based on target power."""
        # Define power thresholds for different mining modes
        power_thresholds = {
            4500: {"mode": "peak_solar", "boards": 3, "profile": "max_power"},
            3500: {"mode": "solar_max", "boards": 3, "profile": "balanced"},
            2500: {"mode": "normal", "boards": 3, "profile": "balanced"},
            1500: {"mode": "eco", "boards": 2, "profile": "ultra_eco"},
            800: {"mode": "minimal", "boards": 1, "profile": "ultra_eco"},
            0: {"mode": "standby", "boards": 0, "profile": "ultra_eco"},
        }
        
        # Find appropriate mode based on target power
        selected_mode = None
        for threshold in sorted(power_thresholds.keys(), reverse=True):
            if target_power >= threshold:
                selected_mode = power_thresholds[threshold]
                break
        
        if not selected_mode:
            selected_mode = power_thresholds[0]  # Standby mode
        
        # Apply the selected mode
        await self._apply_mining_mode(selected_mode, target_power)
    
    async def _apply_mining_mode(self, mode_config: dict, target_power: float) -> None:
        """Apply a specific mining mode configuration."""
        mode_name = mode_config["mode"]
        target_boards = mode_config["boards"]
        profile = mode_config["profile"]
        
        try:
            # Apply power profile first
            await self._apply_power_profile(profile)
            
            # Manage hashboards
            await self._manage_hashboards(target_boards)
            
            # Set power limit if supported
            if target_power > 0:
                await self.client.set_power_limit(int(target_power))
            
            # Update tracking
            self.current_power_target = target_power
            
            _LOGGER.info(
                "Applied mining mode '%s' for miner %s: %s boards, %s profile, %sW target",
                mode_name, self.host, target_boards, profile, target_power
            )
            
        except Exception as err:
            _LOGGER.error("Error applying mining mode '%s': %s", mode_name, err)
    
    async def _apply_power_profile(self, profile: str) -> None:
        """Apply a power profile."""
        profile_map = {
            "max_power": "delta,2",
            "balanced": "delta,0", 
            "ultra_eco": "delta,-2"
        }
        
        luxos_profile = profile_map.get(profile, "delta,0")
        await self.client.set_profile(luxos_profile)
    
    async def _manage_hashboards(self, target_boards: int) -> None:
        """Manage hashboard activation based on target count."""
        for board_id in range(3):  # 3 hashboards (0, 1, 2)
            should_be_active = board_id < target_boards
            is_currently_active = self.active_boards[board_id]
            
            if should_be_active != is_currently_active:
                if should_be_active:
                    success = await self.client.enable_board(board_id)
                    if success:
                        self.active_boards[board_id] = True
                        _LOGGER.info("Enabled board %s for miner %s", board_id, self.host)
                else:
                    success = await self.client.disable_board(board_id)
                    if success:
                        self.active_boards[board_id] = False
                        _LOGGER.info("Disabled board %s for miner %s", board_id, self.host)
    
    async def _enter_standby_mode(self) -> None:
        """Enter standby mode (all boards off)."""
        try:
            await self.client.pause_mining()
            self.active_boards = [False, False, False]
            self.current_power_target = 0
            _LOGGER.info("Entered standby mode for miner %s (solar power below threshold)", self.host)
        except Exception as err:
            _LOGGER.error("Error entering standby mode: %s", err)
    
    async def _check_temperature_protection(self) -> None:
        """Check and apply temperature protection."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return
        
        try:
            # Get maximum temperature from all boards
            max_temp = 0
            devices_data = self.coordinator.data["devices"]
            if "DEVS" in devices_data:
                devs = devices_data["DEVS"]
                for dev in devs:
                    temp_str = dev.get("Temperature", "0")
                    try:
                        temp = float(temp_str)
                        max_temp = max(max_temp, temp)
                    except (ValueError, TypeError):
                        continue
            
            # Apply temperature protection at 75°C
            if max_temp >= 75.0:
                _LOGGER.warning("High temperature detected (%s°C) for miner %s", max_temp, self.host)
                
                # Apply temperature protection
                if max_temp >= 80.0:
                    # Critical temperature - emergency measures
                    await self._apply_emergency_cooling()
                elif max_temp >= 75.0:
                    # High temperature - apply eco profile
                    await self._apply_power_profile("ultra_eco")
                    _LOGGER.info("Applied Ultra Eco profile due to high temperature (%s°C)", max_temp)
                    
        except Exception as err:
            _LOGGER.error("Error checking temperature protection: %s", err)
    
    async def _apply_emergency_cooling(self) -> None:
        """Apply emergency cooling measures."""
        try:
            # Disable one or more boards to reduce heat
            if self.active_boards[2]:  # Disable board 2 first
                await self.client.disable_board(2)
                self.active_boards[2] = False
            elif self.active_boards[1]:  # Then board 1
                await self.client.disable_board(1)
                self.active_boards[1] = False
            
            # Apply ultra eco profile
            await self._apply_power_profile("ultra_eco")
            
            _LOGGER.warning("Emergency cooling measures applied for miner %s", self.host)
            
        except Exception as err:
            _LOGGER.error("Error applying emergency cooling: %s", err)
    
    def set_solar_power(self, power_watts: float) -> None:
        """Set the current solar power availability."""
        self.current_solar_power = power_watts
        _LOGGER.info("Solar power updated to %sW for miner %s", power_watts, self.host)
    
    def set_automation_enabled(self, enabled: bool) -> None:
        """Enable or disable automation."""
        self.automation_enabled = enabled
        _LOGGER.info("Solar automation %s for miner %s", "enabled" if enabled else "disabled", self.host)
    
    def set_sun_curve_enabled(self, enabled: bool) -> None:
        """Enable or disable sun curve mode."""
        self.sun_curve_enabled = enabled
        mode = "sun curve" if enabled else "manual"
        _LOGGER.info("Solar mode set to %s for miner %s", mode, self.host)
    
    def set_auto_standby_enabled(self, enabled: bool) -> None:
        """Enable or disable auto standby mode."""
        self.auto_standby_enabled = enabled
        _LOGGER.info("Auto standby %s for miner %s", "enabled" if enabled else "disabled", self.host)
    
    def set_minimum_power_threshold(self, threshold_watts: float) -> None:
        """Set minimum power threshold for auto standby."""
        self.minimum_power_threshold = threshold_watts
        _LOGGER.info("Minimum power threshold set to %sW for miner %s", threshold_watts, self.host)
    
    def set_automation_interval(self, interval_minutes: int) -> None:
        """Set automation interval and restart timer."""
        self.automation_interval = interval_minutes
        self._setup_automation_timer()
        _LOGGER.info("Automation interval set to %s minutes for miner %s", interval_minutes, self.host)
    
    async def manual_trigger(self) -> None:
        """Manually trigger automation run."""
        _LOGGER.info("Manual automation trigger for miner %s", self.host)
        await self._run_automation()
    
    def get_status(self) -> dict[str, Any]:
        """Get current automation status."""
        return {
            "automation_enabled": self.automation_enabled,
            "sun_curve_enabled": self.sun_curve_enabled,
            "auto_standby_enabled": self.auto_standby_enabled,
            "current_solar_power": self.current_solar_power,
            "minimum_power_threshold": self.minimum_power_threshold,
            "automation_interval": self.automation_interval,
            "current_power_target": self.current_power_target,
            "active_boards": self.active_boards,
            "last_automation_run": self.last_automation_run.isoformat() if self.last_automation_run else None,
        }
    
    def cleanup(self) -> None:
        """Cleanup automation resources."""
        if self._unsub_automation:
            self._unsub_automation()
            self._unsub_automation = None
        _LOGGER.info("Solar automation cleaned up for miner %s", self.host)