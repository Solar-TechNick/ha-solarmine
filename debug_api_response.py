#!/usr/bin/env python3
"""Debug script to check actual LuxOS API response format."""

import asyncio
import json
import sys

async def debug_api_response(host: str, port: int = 4028):
    """Debug the actual API response format."""
    print(f"Debugging API responses for {host}:{port}...")
    
    commands = ["summary", "devs", "stats", "pools"]
    
    for command in commands:
        print(f"\n{'='*50}")
        print(f"Command: {command}")
        print('='*50)
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), 
                timeout=5
            )
            
            # Send command
            cmd_data = {"command": command}
            cmd_json = json.dumps(cmd_data) + "\n"
            writer.write(cmd_json.encode('utf-8'))
            await writer.drain()
            
            # Read response
            response_data = await asyncio.wait_for(reader.read(8192), timeout=5)
            writer.close()
            await writer.wait_closed()
            
            # Parse response
            response_text = response_data.decode('utf-8', errors='ignore').strip()
            result = json.loads(response_text)
            
            # Pretty print the response
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            print(f"❌ Error with {command}: {e}")

async def main():
    """Main debug function."""
    if len(sys.argv) != 2:
        print("Usage: python3 debug_api_response.py <miner_ip>")
        print("Example: python3 debug_api_response.py 192.168.1.212")
        sys.exit(1)
    
    host = sys.argv[1]
    await debug_api_response(host)

if __name__ == "__main__":
    asyncio.run(main())