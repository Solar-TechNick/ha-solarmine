"""LuxOS API client for Solar Miner integration."""
from __future__ import annotations

import asyncio
import json
import logging
import socket
from typing import Any

import aiohttp

from .const import LUXOS_COMMANDS, LUXOS_TCP_PORT, LUXOS_HTTP_PORT, DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class LuxOSClient:
    """LuxOS API client for Antminer S21+ with LuxOS firmware."""
    
    def __init__(
        self,
        host: str,
        port: int = 80,  # Not used for LuxOS, kept for compatibility
        username: str | None = None,
        password: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        use_tcp_api: bool = True,  # Prefer TCP API (port 4028) over HTTP API (port 8080)
    ) -> None:
        """Initialize the client.
        
        Args:
            host: Miner IP address
            port: Legacy port parameter (not used for LuxOS)
            username: Optional username (not typically required for LuxOS)
            password: Optional password (not typically required for LuxOS)
            timeout: Request timeout in seconds
            use_tcp_api: If True, use TCP API (port 4028), else use HTTP API (port 8080)
        """
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout
        self.use_tcp_api = use_tcp_api
        self.tcp_port = LUXOS_TCP_PORT
        self.http_port = LUXOS_HTTP_PORT
        self.http_url = f"http://{host}:{LUXOS_HTTP_PORT}/api"
        self._session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session for HTTP API."""
        if self._session is None or self._session.closed:
            auth = None
            if self.username and self.password:
                auth = aiohttp.BasicAuth(self.username, self.password)
            
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                auth=auth,
                connector=aiohttp.TCPConnector(ssl=False)
            )
        return self._session
    
    async def _tcp_request(self, command: str, parameter: str = "") -> dict[str, Any]:
        """Make TCP API request to LuxOS (port 4028) - Recommended method."""
        try:
            # Create command object
            cmd_data = {"command": command}
            if parameter:
                cmd_data["parameter"] = parameter
            
            # Connect to TCP API
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.tcp_port), 
                timeout=self.timeout
            )
            
            # Send command
            cmd_json = json.dumps(cmd_data) + "\n"
            writer.write(cmd_json.encode('utf-8'))
            await writer.drain()
            
            # Read response - increase buffer for large profile data
            response_data = b""
            while True:
                chunk = await asyncio.wait_for(
                    reader.read(8192), 
                    timeout=self.timeout
                )
                if not chunk:
                    break
                response_data += chunk
                # Check if we have a complete JSON response
                try:
                    response_text = response_data.decode('utf-8', errors='ignore')
                    if response_text.strip().endswith('}'):
                        break
                except UnicodeDecodeError:
                    continue
            
            # Close connection
            writer.close()
            await writer.wait_closed()
            
            # Parse response with better error handling
            response_text = response_data.decode('utf-8', errors='ignore').strip()
            
            # Handle potential truncated JSON
            if not response_text:
                raise ValueError("Empty response received")
            
            # Try to fix common JSON truncation issues
            if not response_text.endswith('}'):
                _LOGGER.warning(f"Response appears truncated, attempting to fix: ...{response_text[-50:]}")
                # Try to find the last complete object
                last_brace = response_text.rfind('}')
                if last_brace > 0:
                    response_text = response_text[:last_brace + 1]
                else:
                    raise ValueError("Response is severely truncated")
            
            result = json.loads(response_text)
            
            _LOGGER.debug(f"TCP API command '{command}' successful")
            return result
            
        except asyncio.TimeoutError:
            _LOGGER.error(f"TCP API timeout for command '{command}'")
            raise
        except json.JSONDecodeError as err:
            _LOGGER.error(f"Error parsing TCP API JSON response for command '{command}': {err}")
            _LOGGER.debug(f"Malformed JSON response (first 500 chars): {response_text[:500]}")
            _LOGGER.debug(f"Malformed JSON response (last 500 chars): {response_text[-500:]}")
            raise
        except Exception as err:
            _LOGGER.error(f"TCP API error for command '{command}': {err}")
            raise
    
    async def _http_request(self, command: str, parameter: str = "") -> dict[str, Any]:
        """Make HTTP API request to LuxOS (port 8080) - Alternative method."""
        session = await self._get_session()
        
        try:
            # Create command object
            cmd_data = {"command": command}
            if parameter:
                cmd_data["parameter"] = parameter
            
            async with session.post(
                self.http_url,
                json=cmd_data,
                headers={'Content-Type': 'application/json'}
            ) as response:
                response.raise_for_status()
                
                # Handle large responses properly
                response_text = await response.text()
                
                # Check for truncation issues
                if not response_text.strip():
                    raise ValueError("Empty HTTP response received")
                
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError as err:
                    _LOGGER.error(f"HTTP API JSON parsing error for '{command}': {err}")
                    _LOGGER.debug(f"HTTP response length: {len(response_text)}")
                    _LOGGER.debug(f"HTTP response (first 500 chars): {response_text[:500]}")
                    _LOGGER.debug(f"HTTP response (last 500 chars): {response_text[-500:]}")
                    raise
                
                _LOGGER.debug(f"HTTP API command '{command}' successful")
                return result
                
        except aiohttp.ClientError as err:
            _LOGGER.error(f"HTTP API error for command '{command}': {err}")
            raise
        except json.JSONDecodeError as err:
            _LOGGER.error(f"Error parsing HTTP API JSON response for command '{command}': {err}")
            raise
    
    async def _api_request(self, command: str, parameter: str = "") -> dict[str, Any]:
        """Make API request using preferred method (TCP or HTTP) with comprehensive error handling."""
        max_retries = 2
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if self.use_tcp_api:
                    return await self._tcp_request(command, parameter)
                else:
                    return await self._http_request(command, parameter)
            except (asyncio.TimeoutError, ConnectionError, OSError) as err:
                retry_count += 1
                if retry_count < max_retries:
                    _LOGGER.warning(f"Connection error for '{command}' (attempt {retry_count}/{max_retries}): {err}")
                    await asyncio.sleep(1)  # Brief delay before retry
                    continue
                else:
                    _LOGGER.error(f"Max retries exceeded for '{command}': {err}")
                    # Try alternative method as last resort
                    break
            except Exception as err:
                _LOGGER.error(f"Unexpected error for command '{command}': {err}")
                break
        
        # If primary method failed, try the alternative
        _LOGGER.warning(f"Primary API method failed for '{command}', trying alternative")
        try:
            if self.use_tcp_api:
                return await self._http_request(command, parameter)
            else:
                return await self._tcp_request(command, parameter)
        except Exception as fallback_err:
            _LOGGER.error(f"Both API methods failed for command '{command}': {fallback_err}")
            # Return empty result instead of raising to prevent coordinator failures
            return {"STATUS": [{"STATUS": "E", "Msg": f"API communication failed: {fallback_err}"}]}
    
    async def get_summary(self) -> dict[str, Any]:
        """Get miner summary information."""
        return await self._api_request(LUXOS_COMMANDS["summary"])
    
    async def get_pools(self) -> dict[str, Any]:
        """Get pool information."""
        return await self._api_request(LUXOS_COMMANDS["pools"])
    
    async def get_devs(self) -> dict[str, Any]:
        """Get device/hashboard information."""
        return await self._api_request(LUXOS_COMMANDS["devs"])
    
    async def get_stats(self) -> dict[str, Any]:
        """Get detailed mining statistics."""
        return await self._api_request(LUXOS_COMMANDS["stats"])
    
    async def get_config(self) -> dict[str, Any]:
        """Get miner configuration."""
        return await self._api_request(LUXOS_COMMANDS["config"])
    
    async def get_version(self) -> dict[str, Any]:
        """Get version information."""
        return await self._api_request(LUXOS_COMMANDS["version"])
    
    async def get_devdetails(self) -> dict[str, Any]:
        """Get detailed device information."""
        return await self._api_request(LUXOS_COMMANDS["devdetails"])
    
    async def get_profiles(self) -> dict[str, Any]:
        """Get available profiles information."""
        return await self._api_request("profiles")
    
    async def get_power(self) -> dict[str, Any]:
        """Get current power consumption."""
        return await self._api_request("power")
    
    async def get_atm(self) -> dict[str, Any]:
        """Get Advanced Thermal Management information."""
        return await self._api_request("atm")
    
    async def set_profile(self, profile_params: str) -> dict[str, Any]:
        """Set profile using LuxOS profileset command.
        
        Note: LuxOS requires web-based authentication for profile changes.
        This method will attempt the change but will likely fail without session_id.
        
        Args:
            profile_params: Profile parameters (requires session_id for LuxOS)
        """
        _LOGGER.warning("Profile changes require web authentication - this may fail")
        return await self._api_request(LUXOS_COMMANDS["profileset"], profile_params)
    
    async def set_atm(self, atm_params: str) -> dict[str, Any]:
        """Set ATM (Advanced Thermal Management) parameters.
        
        Args:
            atm_params: ATM parameters as comma-separated string
        """
        return await self._api_request(LUXOS_COMMANDS["atmset"], atm_params)
    
    async def reboot(self) -> dict[str, Any]:
        """Reboot the miner."""
        return await self._api_request(LUXOS_COMMANDS["reboot"])
    
    async def set_power_mode(self, profile_delta: int) -> bool:
        """Set power mode using profile step (LuxOS uses steps, not deltas).
        
        Note: LuxOS requires web authentication for profile changes.
        This method will log the limitation and return False.
        
        Args:
            profile_delta: Step value for profile (-2 for eco, 0 for balanced, +2 for max power)
        """
        _LOGGER.warning(
            "LuxOS profile changes require web authentication. "
            "Profile change to step %s cannot be performed via API. "
            "Please use the web interface at http://%s", 
            profile_delta, self.host
        )
        return False
    
    async def set_eco_mode(self) -> bool:
        """Set miner to eco mode (delta -2)."""
        return await self.set_power_mode(-2)
    
    async def set_balanced_mode(self) -> bool:
        """Set miner to balanced mode (delta 0).""" 
        return await self.set_power_mode(0)
    
    async def set_max_power_mode(self) -> bool:
        """Set miner to max power mode (delta +2)."""
        return await self.set_power_mode(2)
    
    async def set_temperature_control(self, target_temp: float, mode: str = "auto") -> bool:
        """Set Advanced Thermal Management (ATM) parameters.
        
        Args:
            target_temp: Target temperature in Celsius
            mode: ATM mode ("auto", "manual", etc.)
        """
        try:
            result = await self.set_atm(f"{mode},{target_temp}")
            status = result.get("STATUS", [{}])[0]
            return status.get("STATUS") == "S"
        except Exception as err:
            _LOGGER.error("Error setting temperature control to %s°C: %s", target_temp, err)
            return False
    
    async def get_mining_status(self) -> dict[str, Any]:
        """Get comprehensive mining status combining multiple API calls."""
        try:
            # Get all relevant data in parallel for efficiency
            summary_task = asyncio.create_task(self.get_summary())
            stats_task = asyncio.create_task(self.get_stats()) 
            devs_task = asyncio.create_task(self.get_devs())
            config_task = asyncio.create_task(self.get_config())
            
            summary, stats, devs, config = await asyncio.gather(
                summary_task, stats_task, devs_task, config_task
            )
            
            return {
                "summary": summary,
                "stats": stats,
                "devices": devs,
                "config": config
            }
        except Exception as err:
            _LOGGER.error("Error getting mining status: %s", err)
            raise
    
    async def pause_mining(self) -> bool:
        """Pause mining by setting to minimum power mode."""
        _LOGGER.info("Pausing mining by setting eco mode")
        return await self.set_eco_mode()
    
    async def resume_mining(self) -> bool:
        """Resume mining by setting to balanced mode."""
        _LOGGER.info("Resuming mining by setting balanced mode")
        return await self.set_balanced_mode()
    
    async def set_power_limit(self, watts: int) -> bool:
        """Set power limit (LuxOS doesn't support direct power limits, use profiles instead)."""
        try:
            # LuxOS doesn't support direct power limits
            # Use delta profiles based on power target
            if watts <= 1500:
                # Low power - use eco mode (delta -2)
                return await self.set_power_mode(-2)
            elif watts <= 3000:
                # Medium power - use balanced mode (delta 0)
                return await self.set_power_mode(0)
            else:
                # High power - use max mode (delta +2)
                return await self.set_power_mode(2)
        except Exception as err:
            _LOGGER.error("Error setting power limit to %s watts: %s", watts, err)
            return False
    
    async def set_temp_control(self, target_temp: float) -> bool:
        """Set temperature control threshold."""
        try:
            return await self.set_temperature_control(target_temp, "auto")
        except Exception as err:
            _LOGGER.error("Error setting temperature control: %s", err)
            return False
    
    async def enable_board(self, board_id: int) -> bool:
        """Enable hashboard (LuxOS limitation: individual board control not supported)."""
        try:
            # LuxOS API doesn't support individual hashboard control
            # Use balanced profile to ensure all boards are active
            success = await self.set_balanced_mode()
            if success:
                _LOGGER.info("Board %s enable requested - applied balanced mode (LuxOS limitation)", board_id)
            return success
        except Exception as err:
            _LOGGER.error("Error enabling board %s: %s", board_id, err)
            return False
    
    async def disable_board(self, board_id: int) -> bool:
        """Disable hashboard (LuxOS limitation: individual board control not supported)."""
        try:
            # LuxOS API doesn't support individual hashboard control
            # Use eco profile to reduce overall power
            success = await self.set_eco_mode()
            if success:
                _LOGGER.info("Board %s disable requested - applied eco mode (LuxOS limitation)", board_id)
            return success
        except Exception as err:
            _LOGGER.error("Error disabling board %s: %s", board_id, err)
            return False
    
    # Working ASC (ASIC) control methods
    async def asc_enable(self, asc_id: int) -> bool:
        """Enable ASC (ASIC) unit - working alternative to profile changes."""
        try:
            result = await self._api_request("ascenable", str(asc_id))
            status = result.get("STATUS", [{}])[0]
            success = status.get("STATUS") == "S"
            if success:
                _LOGGER.info("ASC %s enabled successfully", asc_id)
            else:
                msg = status.get("Msg", "Unknown error")
                _LOGGER.warning("ASC %s enable failed: %s", asc_id, msg)
            return success
        except Exception as err:
            _LOGGER.error("Error enabling ASC %s: %s", asc_id, err)
            return False
    
    async def asc_disable(self, asc_id: int) -> bool:
        """Disable ASC (ASIC) unit - working alternative to profile changes."""
        try:
            result = await self._api_request("ascdisable", str(asc_id))
            status = result.get("STATUS", [{}])[0]
            success = status.get("STATUS") == "S"
            if success:
                _LOGGER.info("ASC %s disabled successfully", asc_id)
            else:
                msg = status.get("Msg", "Unknown error")
                _LOGGER.warning("ASC %s disable failed: %s", asc_id, msg)
            return success
        except Exception as err:
            _LOGGER.error("Error disabling ASC %s: %s", asc_id, err)
            return False
    
    async def restart_mining(self) -> bool:
        """Restart mining - working alternative to pause/resume."""
        try:
            result = await self._api_request("restart")
            status = result.get("STATUS", [{}])[0]
            success = status.get("STATUS") == "S"
            if success:
                _LOGGER.info("Mining restart initiated")
            else:
                msg = status.get("Msg", "Unknown error")
                _LOGGER.warning("Mining restart failed: %s", msg)
            return success
        except Exception as err:
            _LOGGER.error("Error restarting mining: %s", err)
            return False
    
    async def close(self) -> None:
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()