#!/usr/bin/env python3
"""Test script to verify LuxOS API connectivity."""

import asyncio
import sys
import os

# Add the custom_components path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'solarminer'))

from luxos_client import LuxOSClient

async def test_miner_connection(host: str, name: str):
    """Test connection to a specific miner."""
    print(f"\n=== Testing {name} ({host}) ===")
    
    client = LuxOSClient(host, timeout=5, use_tcp_api=True)
    
    try:
        print("Testing TCP API (port 4028)...")
        summary = await client.get_summary()
        print(f"✅ TCP API successful")
        print(f"Response keys: {list(summary.keys()) if summary else 'Empty response'}")
        
        if summary and "SUMMARY" in summary:
            print(f"SUMMARY data available: {len(summary['SUMMARY'])} items")
            if summary["SUMMARY"]:
                summary_item = summary["SUMMARY"][0]
                print(f"Sample fields: {list(summary_item.keys())[:5]}...")
        
        return True
        
    except Exception as tcp_err:
        print(f"❌ TCP API failed: {tcp_err}")
        
        # Try HTTP API as fallback
        print("Testing HTTP API (port 8080)...")
        client_http = LuxOSClient(host, timeout=5, use_tcp_api=False)
        try:
            summary = await client_http.get_summary()
            print(f"✅ HTTP API successful")
            print(f"Response keys: {list(summary.keys()) if summary else 'Empty response'}")
            return True
        except Exception as http_err:
            print(f"❌ HTTP API failed: {http_err}")
            return False
    
    finally:
        await client.close()

async def test_button_functionality(host: str, name: str):
    """Test button functionality."""
    print(f"\n=== Testing {name} Button Functionality ===")
    
    client = LuxOSClient(host, timeout=10, use_tcp_api=True)
    
    try:
        # Test profile setting
        print("Testing profile setting...")
        result = await client.set_profile("delta,0")  # Balanced mode
        print(f"Profile set result: {result}")
        
        # Check if result has proper status
        if result and "STATUS" in result:
            status = result["STATUS"][0] if result["STATUS"] else {}
            status_code = status.get("STATUS", "E")
            msg = status.get("Msg", "No message")
            print(f"Status: {status_code}, Message: {msg}")
            
            if status_code == "S":
                print("✅ Profile setting successful")
            else:
                print(f"❌ Profile setting failed: {msg}")
        else:
            print(f"❌ Unexpected response format: {result}")
            
    except Exception as err:
        print(f"❌ Button test failed: {err}")
    
    finally:
        await client.close()

async def main():
    """Main test function."""
    print("🔍 Solar Miner LuxOS Connection Test")
    print("=" * 50)
    
    # Test both miners
    miners = [
        ("192.168.1.210", "S19j Pro+"),
        ("192.168.1.212", "S21+")
    ]
    
    success_count = 0
    
    for host, name in miners:
        try:
            if await test_miner_connection(host, name):
                success_count += 1
                await test_button_functionality(host, name)
        except KeyboardInterrupt:
            print("\n❌ Test interrupted by user")
            break
        except Exception as err:
            print(f"❌ Unexpected error testing {name}: {err}")
    
    print(f"\n📊 Results: {success_count}/{len(miners)} miners connected successfully")
    
    if success_count == 0:
        print("\n🚨 No miners could be reached. Check:")
        print("1. Miner IP addresses (192.168.1.210, 192.168.1.212)")
        print("2. Network connectivity")
        print("3. LuxOS firmware is running")
        print("4. API ports 4028 (TCP) or 8080 (HTTP) are open")
    
    return success_count > 0

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n❌ Test cancelled")
        sys.exit(1)