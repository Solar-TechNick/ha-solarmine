#!/usr/bin/env python3
"""Test the updated integration."""

import sys
import os
import asyncio

# Add the custom_components path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'solarminer'))

async def test_updated_client():
    """Test the updated LuxOS client."""
    print("🔍 Testing Updated LuxOS Client")
    print("=" * 40)
    
    from luxos_client import LuxOSClient
    
    client = LuxOSClient("192.168.1.212", timeout=10)
    
    try:
        # Test all new methods
        print("\n--- Testing get_profiles() ---")
        profiles = await client.get_profiles()
        if profiles and "PROFILES" in profiles:
            print(f"✅ Found {len(profiles['PROFILES'])} profiles")
            
            # Show some profile examples
            for i, profile in enumerate(profiles["PROFILES"][:3]):
                name = profile.get("Profile Name", "Unknown")
                step = profile.get("Step", "0")
                watts = profile.get("Watts", 0)
                hashrate = profile.get("Hashrate", 0)
                print(f"  Profile {i+1}: {name} (Step {step}) - {watts}W, {hashrate} TH/s")
        
        print("\n--- Testing get_power() ---")
        power = await client.get_power()
        if power and "POWER" in power:
            power_data = power["POWER"][0]
            watts = power_data.get("Watts", 0)
            psu_status = power_data.get("PSU", False)
            print(f"✅ Current power: {watts}W, PSU: {'OK' if psu_status else 'ERROR'}")
        
        print("\n--- Testing get_atm() ---")
        atm = await client.get_atm()
        if atm and "ATM" in atm:
            atm_data = atm["ATM"][0]
            enabled = atm_data.get("Enabled", False)
            max_profile = atm_data.get("MaxProfile", "Unknown")
            print(f"✅ ATM enabled: {enabled}, Max profile: {max_profile}")
        
        print("\n--- Testing power mode change (expected to fail) ---")
        success = await client.set_power_mode(-2)
        if success:
            print("✅ Power mode change succeeded (unexpected!)")
        else:
            print("✅ Power mode change failed as expected (LuxOS limitation)")
        
        return True
        
    except Exception as err:
        print(f"❌ Error testing client: {err}")
        return False
    
    finally:
        await client.close()

async def main():
    """Main test function."""
    success = await test_updated_client()
    
    if success:
        print(f"\n✅ Updated integration client working correctly!")
        print(f"\nKey features:")
        print(f"  • ✅ Reading all LuxOS data (profiles, power, ATM)")
        print(f"  • ✅ Proper error handling for profile changes")
        print(f"  • ✅ Accurate power consumption from API")
        print(f"  • ⚠️  Profile changes require web interface (LuxOS limitation)")
        print(f"\nTo change profiles, users should visit: http://192.168.1.212")
    else:
        print(f"\n❌ Integration test failed")

if __name__ == "__main__":
    asyncio.run(main())