#!/usr/bin/env python3
"""Debug specific field names in LuxOS API responses."""

import asyncio
import json
import sys

async def debug_field_names(host: str, port: int = 4028):
    """Debug specific field names for sensors that aren't working."""
    print(f"Debugging field names for {host}:{port}...")
    
    commands = [
        ("summary", "SUMMARY"),
        ("devs", "DEVS"), 
        ("stats", "STATS"),
        ("pools", "POOLS")
    ]
    
    for command, array_key in commands:
        print(f"\n{'='*60}")
        print(f"Command: {command} -> Looking for {array_key} array")
        print('='*60)
        
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
            
            # Check if array exists and print field names
            if array_key in result and result[array_key]:
                print(f"✅ Found {array_key} array with {len(result[array_key])} items")
                
                # Print all field names in first item
                first_item = result[array_key][0]
                print("\nAvailable fields:")
                for key, value in first_item.items():
                    print(f"  '{key}': {value}")
                
                # For DEVS, show all devices
                if array_key == "DEVS" and len(result[array_key]) > 1:
                    print(f"\nAll {len(result[array_key])} devices:")
                    for i, dev in enumerate(result[array_key]):
                        print(f"  Device {i}: {dev.get('Name', 'Unknown')} - {dev.get('Status', 'Unknown')}")
            else:
                print(f"❌ No {array_key} array found")
                print("Available keys:", list(result.keys()))
                
        except Exception as e:
            print(f"❌ Error with {command}: {e}")

async def main():
    """Main debug function."""
    if len(sys.argv) != 2:
        print("Usage: python3 debug_specific_fields.py <miner_ip>")
        print("Example: python3 debug_specific_fields.py 192.168.1.212")
        sys.exit(1)
    
    host = sys.argv[1]
    await debug_field_names(host)

if __name__ == "__main__":
    asyncio.run(main())