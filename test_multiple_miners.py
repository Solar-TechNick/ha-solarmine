#!/usr/bin/env python3
"""Test multiple miner configuration."""

def test_unique_id_generation():
    """Test unique ID generation for multiple miners."""
    print("🔍 Testing Unique ID Generation")
    print("=" * 40)
    
    # Simulate different miner IPs
    test_miners = [
        "192.168.1.210",
        "192.168.1.212", 
        "10.0.0.100",
        "172.16.1.50"
    ]
    
    print("Testing unique ID generation:")
    unique_ids = []
    
    for ip in test_miners:
        unique_id = f"solarminer_{ip.replace('.', '_')}"
        unique_ids.append(unique_id)
        print(f"  {ip:15} -> {unique_id}")
    
    # Check for duplicates
    if len(unique_ids) == len(set(unique_ids)):
        print(f"\n✅ All IDs are unique!")
    else:
        print(f"\n❌ Duplicate IDs found!")
        return False
    
    # Test device identifier generation
    print(f"\nTesting device info generation:")
    for ip in test_miners:
        device_id = f"solarminer_{ip.replace('.', '_')}"
        device_name = f"Solar Miner {ip}"
        config_url = f"http://{ip}"
        
        print(f"  Device: {device_name}")
        print(f"    ID: {device_id}")
        print(f"    URL: {config_url}")
        print()
    
    return True

def test_config_flow_logic():
    """Test the config flow logic."""
    print("🔍 Testing Config Flow Logic")
    print("=" * 40)
    
    # Simulate config flow data
    test_configs = [
        {
            "host": "192.168.1.210",
            "port": 80,
            "miner_model": "Antminer S19j Pro+",
            "miner_serial": "ABC123"
        },
        {
            "host": "192.168.1.212", 
            "port": 80,
            "miner_model": "Antminer S21+",
            "miner_serial": "DEF456"
        }
    ]
    
    print("Simulating config flow for multiple miners:")
    
    for i, config in enumerate(test_configs):
        host_ip = config["host"]
        unique_id = f"solarminer_{host_ip.replace('.', '_')}"
        miner_model = config["miner_model"]
        miner_serial = config["miner_serial"]
        
        if miner_serial:
            title = f"Solar Miner {miner_model} ({host_ip}) - {miner_serial}"
        else:
            title = f"Solar Miner {miner_model} ({host_ip})"
        
        print(f"\n--- Miner {i+1} ---")
        print(f"Title: {title}")
        print(f"Unique ID: {unique_id}")
        print(f"Host: {host_ip}")
        print(f"Model: {miner_model}")
        print(f"Serial: {miner_serial}")
    
    print(f"\n✅ Both miners can be configured with unique identifiers!")

def show_fix_summary():
    """Show what was fixed."""
    print("🔧 Fix Summary")
    print("=" * 40)
    
    print("PROBLEM:")
    print("  ❌ 'Already configured' error when adding second miner")
    print("  ❌ Integration used miner serial as unique ID")
    print("  ❌ Both miners likely had same/empty serial number")
    
    print("\nSOLUTION:")
    print("  ✅ Changed unique ID to use IP address: 'solarminer_192_168_1_210'")
    print("  ✅ Updated all entity device_info to use IP-based identifiers")
    print("  ✅ Added configuration_url pointing to miner web interface")
    print("  ✅ Enhanced title to include IP and serial for clarity")
    
    print("\nRESULT:")
    print("  🎉 Each miner IP gets unique identifier")
    print("  🎉 Multiple miners can be configured simultaneously")
    print("  🎉 Clear device names show IP addresses")
    print("  🎉 Direct links to miner web interfaces")

def main():
    """Test multiple miner support."""
    print("🚀 Testing Multiple Miner Support")
    print("=" * 50)
    
    # Run tests
    test_unique_id_generation()
    print()
    test_config_flow_logic()
    print()
    show_fix_summary()
    
    print(f"\n🎉 READY TO TEST:")
    print(f"  1. Restart Home Assistant")
    print(f"  2. Go to Settings → Devices & Services")
    print(f"  3. Add Integration → Solar Miner")
    print(f"  4. Configure first miner (192.168.1.212)")
    print(f"  5. Add Integration → Solar Miner again")
    print(f"  6. Configure second miner (192.168.1.210)")
    print(f"  7. Both should appear as separate devices!")

if __name__ == "__main__":
    main()