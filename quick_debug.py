#!/usr/bin/env python3
"""Quick debug to see actual field names."""

import asyncio
import json
import sys

async def quick_debug(host: str):
    """Quick debug of actual field names."""
    print(f"Quick debug of {host}...")
    
    try:
        # Test summary command
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, 4028), timeout=5
        )
        
        cmd_data = {"command": "summary"}
        cmd_json = json.dumps(cmd_data) + "\n"
        writer.write(cmd_json.encode('utf-8'))
        await writer.drain()
        
        response_data = await asyncio.wait_for(reader.read(8192), timeout=5)
        writer.close()
        await writer.wait_closed()
        
        result = json.loads(response_data.decode('utf-8', errors='ignore').strip())
        
        if "SUMMARY" in result and result["SUMMARY"]:
            summary_item = result["SUMMARY"][0]
            print("\n🔍 SUMMARY fields available:")
            for key, value in sorted(summary_item.items()):
                print(f"  '{key}': {value}")
                
            # Look for power-related fields
            print("\n⚡ Power-related fields:")
            for key, value in summary_item.items():
                if any(word in key.lower() for word in ['power', 'watt', 'utility', 'consumption']):
                    print(f"  ✅ '{key}': {value}")
                    
            # Look for fan-related fields  
            print("\n🌪️ Fan-related fields:")
            for key, value in summary_item.items():
                if any(word in key.lower() for word in ['fan', 'speed', 'rpm']):
                    print(f"  ✅ '{key}': {value}")
                    
        else:
            print("❌ No SUMMARY data found")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 quick_debug.py <miner_ip>")
        sys.exit(1)
    
    asyncio.run(quick_debug(sys.argv[1]))