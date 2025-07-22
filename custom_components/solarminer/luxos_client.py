"""LuxOS API client for Solar Miner integration."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp

from .const import LUXOS_ENDPOINTS, DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class LuxOSClient:
    """LuxOS API client."""
    
    def __init__(
        self,
        host: str,
        port: int = 80,
        username: str | None = None,
        password: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the client."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self._session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            auth = None
            if self.username and self.password:
                auth = aiohttp.BasicAuth(self.username, self.password)
            
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                auth=auth,
            )
        return self._session
    
    async def _request(self, endpoint: str, params: dict | None = None) -> dict[str, Any]:
        """Make API request."""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                return data
        except aiohttp.ClientError as err:
            _LOGGER.error("Error communicating with LuxOS API: %s", err)
            raise
        except json.JSONDecodeError as err:
            _LOGGER.error("Error parsing JSON response: %s", err)
            raise
    
    async def _post_request(self, endpoint: str, data: dict | None = None) -> dict[str, Any]:
        """Make API POST request."""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with session.post(url, json=data) as response:
                response.raise_for_status()
                result = await response.json()
                return result
        except aiohttp.ClientError as err:
            _LOGGER.error("Error communicating with LuxOS API: %s", err)
            raise
        except json.JSONDecodeError as err:
            _LOGGER.error("Error parsing JSON response: %s", err)
            raise
    
    async def get_summary(self) -> dict[str, Any]:
        """Get miner summary."""
        return await self._request(LUXOS_ENDPOINTS["summary"])
    
    async def get_pools(self) -> dict[str, Any]:
        """Get pool information."""
        return await self._request(LUXOS_ENDPOINTS["pools"])
    
    async def get_devs(self) -> dict[str, Any]:
        """Get device information."""
        return await self._request(LUXOS_ENDPOINTS["devs"])
    
    async def set_frequency(self, board: int, frequency: int) -> dict[str, Any]:
        """Set hashboard frequency."""
        data = {"board": board, "frequency": frequency}
        return await self._post_request(LUXOS_ENDPOINTS["frequencyset"], data)
    
    async def set_voltage(self, board: int, voltage: float) -> dict[str, Any]:
        """Set hashboard voltage."""
        data = {"board": board, "voltage": voltage}
        return await self._post_request(LUXOS_ENDPOINTS["voltageset"], data)
    
    async def set_profile(self, profile_name: str) -> dict[str, Any]:
        """Set overclocking profile."""
        data = {"profile": profile_name}
        return await self._post_request(LUXOS_ENDPOINTS["profileset"], data)
    
    async def set_temp_control(self, target_temp: float) -> dict[str, Any]:
        """Set temperature control."""
        data = {"target_temp": target_temp}
        return await self._post_request(LUXOS_ENDPOINTS["tempctrlset"], data)
    
    async def reboot(self) -> dict[str, Any]:
        """Reboot miner."""
        return await self._post_request(LUXOS_ENDPOINTS["reboot"])
    
    async def enable_board(self, board: int) -> bool:
        """Enable specific hashboard."""
        try:
            # Implementation depends on LuxOS API
            # This is a placeholder for the actual API call
            data = {"board": board, "action": "enable"}
            result = await self._post_request("/cgi-bin/luci/admin/miner/api/boardcontrol", data)
            return result.get("success", False)
        except Exception as err:
            _LOGGER.error("Error enabling board %s: %s", board, err)
            return False
    
    async def disable_board(self, board: int) -> bool:
        """Disable specific hashboard."""
        try:
            # Implementation depends on LuxOS API
            # This is a placeholder for the actual API call
            data = {"board": board, "action": "disable"}
            result = await self._post_request("/cgi-bin/luci/admin/miner/api/boardcontrol", data)
            return result.get("success", False)
        except Exception as err:
            _LOGGER.error("Error disabling board %s: %s", board, err)
            return False
    
    async def set_power_limit(self, watts: int) -> bool:
        """Set power limit in watts."""
        try:
            data = {"power_limit": watts}
            result = await self._post_request("/cgi-bin/luci/admin/miner/api/powerlimit", data)
            return result.get("success", False)
        except Exception as err:
            _LOGGER.error("Error setting power limit to %s watts: %s", watts, err)
            return False
    
    async def pause_mining(self) -> bool:
        """Pause mining (disable all boards)."""
        try:
            # Disable all boards
            for board in range(3):  # Assuming 3 boards
                await self.disable_board(board)
            return True
        except Exception as err:
            _LOGGER.error("Error pausing mining: %s", err)
            return False
    
    async def resume_mining(self) -> bool:
        """Resume mining (enable all boards)."""
        try:
            # Enable all boards
            for board in range(3):  # Assuming 3 boards
                await self.enable_board(board)
            return True
        except Exception as err:
            _LOGGER.error("Error resuming mining: %s", err)
            return False
    
    async def close(self) -> None:
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()