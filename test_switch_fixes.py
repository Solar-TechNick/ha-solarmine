#!/usr/bin/env python3
"""Test the fixed switch functionality."""

import socket
import json
import asyncio
from custom_components.solarminer.luxos_client import LuxOSClient

async def test_switch_fixes():
    """Test the newly implemented switch fixes."""
    print("🔧 Testing Switch Fixes")
    print("=" * 30)
    
    # Test with S21+ (should be reachable)
    client = LuxOSClient("192.168.1.212")
    
    print("\n1. Testing ASC Control Commands")
    print("-" * 30)
    
    # Test ASC enable/disable (these should work)
    for asc_id in range(3):
        print(f"\n  Testing ASC {asc_id}:")
        
        # Test enable
        try:
            success = await client.asc_enable(asc_id)
            print(f"    Enable: {'✅ Success' if success else '❌ Failed'}")
        except Exception as err:
            print(f"    Enable: ❌ Error - {err}")
        
        await asyncio.sleep(1)  # Brief delay
        
        # Test disable  
        try:
            success = await client.asc_disable(asc_id)
            print(f"    Disable: {'✅ Success' if success else '❌ Failed'}")
        except Exception as err:
            print(f"    Disable: ❌ Error - {err}")
        
        await asyncio.sleep(1)  # Brief delay
    
    print("\n2. Testing Mining Restart Command")
    print("-" * 30)
    
    try:
        success = await client.restart_mining()
        print(f"  Restart: {'✅ Success' if success else '❌ Failed'}")
    except Exception as err:
        print(f"  Restart: ❌ Error - {err}")
    
    print("\n3. Comparing Old vs New Methods")
    print("-" * 30)
    
    # Test old failing methods for comparison
    print("  Old profile-based methods (should fail):")
    try:
        success = await client.set_balanced_mode()
        print(f"    set_balanced_mode: {'✅ Success' if success else '❌ Failed (expected)'}")
    except Exception as err:
        print(f"    set_balanced_mode: ❌ Error - {err}")
    
    try:
        success = await client.pause_mining()
        print(f"    pause_mining: {'✅ Success' if success else '❌ Failed (expected)'}")
    except Exception as err:
        print(f"    pause_mining: ❌ Error - {err}")
    
    await client.close()

def test_switch_summary():
    """Show summary of switch fixes."""
    print("\n🔧 Switch Fixes Summary")
    print("=" * 25)
    
    print("PROBLEMS FIXED:")
    print("  ❌ Hashboard switches failing due to profile changes")
    print("  ❌ Mining switches failing due to pause/resume methods")
    print("  ❌ All switches showing 'Failed to...' errors in logs")
    
    print("\nSOLUTIONS IMPLEMENTED:")
    print("  ✅ Hashboard switches now use ASC enable/disable commands")
    print("  ✅ Mining switch uses restart command for start")
    print("  ✅ Mining switch uses ASC disable-all for stop")
    print("  ✅ Pause switch uses ASC disable/enable for pause/resume")
    print("  ✅ Solar/Auto switches were already working (state-only)")
    
    print("\nNEW COMMANDS ADDED:")
    print("  • asc_enable(asc_id) - Enable individual ASC unit")
    print("  • asc_disable(asc_id) - Disable individual ASC unit") 
    print("  • restart_mining() - Restart mining process")
    
    print("\nEXPECTED RESULTS:")
    print("  🎉 Hashboard switches should now work properly")
    print("  🎉 Mining controls should function correctly")
    print("  🎉 No more profile change error messages")
    print("  🎉 Better user feedback with success/failure counts")

async def main():
    """Run switch fix tests."""
    print("🚀 Testing Switch Functionality Fixes")
    print("=" * 40)
    
    await test_switch_fixes()
    test_switch_summary()
    
    print(f"\n📝 NEXT STEPS:")
    print("  1. Restart Home Assistant to load new switch code")
    print("  2. Test hashboard switches in UI")
    print("  3. Test mining start/stop switches")
    print("  4. Check logs for success messages instead of errors")

if __name__ == "__main__":
    asyncio.run(main())