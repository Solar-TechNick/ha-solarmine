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
            
            # Read response
            response_data = await asyncio.wait_for(
                reader.read(8192), 
                timeout=self.timeout
            )
            
            # Close connection
            writer.close()
            await writer.wait_closed()
            
            # Parse response
            response_text = response_data.decode('utf-8', errors='ignore').strip()
            result = json.loads(response_text)
            
            _LOGGER.debug(f"TCP API command '{command}' successful")
            return result
            
        except asyncio.TimeoutError:
            _LOGGER.error(f"TCP API timeout for command '{command}'")
            raise
        except json.JSONDecodeError as err:
            _LOGGER.error(f"Error parsing TCP API JSON response for command '{command}': {err}")
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
                result = await response.json()
                
                _LOGGER.debug(f"HTTP API command '{command}' successful")
                return result
                
        except aiohttp.ClientError as err:
            _LOGGER.error(f"HTTP API error for command '{command}': {err}")
            raise
        except json.JSONDecodeError as err:
            _LOGGER.error(f"Error parsing HTTP API JSON response for command '{command}': {err}")
            raise
    
    async def _api_request(self, command: str, parameter: str = "") -> dict[str, Any]:
        """Make API request using preferred method (TCP or HTTP)."""
        try:
            if self.use_tcp_api:
                return await self._tcp_request(command, parameter)
            else:
                return await self._http_request(command, parameter)
        except Exception as err:
            # If preferred method fails, try the alternative
            _LOGGER.warning(f"Primary API method failed for '{command}', trying alternative: {err}")
            try:
                if self.use_tcp_api:
                    return await self._http_request(command, parameter)
                else:
                    return await self._tcp_request(command, parameter)
            except Exception as fallback_err:
                _LOGGER.error(f"Both API methods failed for command '{command}': {fallback_err}")
                raise
    
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
    
    async def set_profile(self, profile_params: str) -> dict[str, Any]:
        """Set profile using LuxOS profileset command.
        
        Args:
            profile_params: Profile parameters as comma-separated string
                          e.g., "delta,-2" for delta profile with -2 setting
        """
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
        """Set power mode using profile delta.
        
        Args:
            profile_delta: Delta value for profile (-2 for eco, 0 for balanced, +2 for max power)
        """
        try:
            result = await self.set_profile(f"delta,{profile_delta}")
            # Check if command was successful based on LuxOS response format
            status = result.get("STATUS", [{}])[0]
            return status.get("STATUS") == "S"  # "S" means success in LuxOS
        except Exception as err:
            _LOGGER.error("Error setting power mode with delta %s: %s", profile_delta, err)
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
    
    async def close(self) -> None:
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()