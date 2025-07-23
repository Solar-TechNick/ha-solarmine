#!/usr/bin/env python3
"""Test control commands."""

import socket
import json
import time

def send_luxos_command(host, command, parameter="", port=4028):
    """Send command to LuxOS API."""
    print(f"Sending command '{command}' with parameter '{parameter}' to {host}:{port}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        # Build command
        cmd_data = {"command": command}
        if parameter:
            cmd_data["parameter"] = parameter
            
        cmd_json = json.dumps(cmd_data) + "\n"
        print(f"Command JSON: {cmd_json.strip()}")
        
        sock.send(cmd_json.encode('utf-8'))
        response = sock.recv(8192)
        
        data = json.loads(response.decode('utf-8'))
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Check status
        if "STATUS" in data and data["STATUS"]:
            status = data["STATUS"][0]
            status_code = status.get("STATUS", "E")
            msg = status.get("Msg", "No message")
            
            if status_code == "S":
                print(f"✅ Command successful: {msg}")
                return True
            else:
                print(f"❌ Command failed: {msg}")
                return False
        else:
            print(f"❌ No status in response")
            return False
            
    except Exception as err:
        print(f"❌ Error: {err}")
        return False
    finally:
        sock.close()

def test_profile_commands(host):
    """Test profile setting commands."""
    print(f"\n=== Testing Profile Commands on {host} ===")
    
    # Test different profile formats to see what works
    test_profiles = [
        ("delta,0", "Balanced mode (delta format)"),
        ("delta,2", "Max power mode (delta format)"),  
        ("delta,-2", "Eco mode (delta format)"),
        ("overclock_0", "Balanced mode (overclock format)"),
        ("default", "Default profile"),
    ]
    
    for profile_param, description in test_profiles:
        print(f"\n--- Testing {description} ---")
        success = send_luxos_command(host, "profileset", profile_param)
        
        if success:
            print(f"✅ {description} works!")
            # Wait a bit then check current profile
            time.sleep(2)
            print("Checking current status...")
            send_luxos_command(host, "summary")
            break
        else:
            print(f"❌ {description} failed")
    
    return False

def test_available_commands(host):
    """Test what commands are available."""
    print(f"\n=== Testing Available Commands on {host} ===")
    
    commands = [
        ("help", "Get help"),
        ("version", "Get version"),
        ("summary", "Get summary"),
        ("devs", "Get devices"),
        ("pools", "Get pools"),
        ("stats", "Get stats"),
        ("config", "Get config"),
        ("profileset", "Set profile (no param)"),
    ]
    
    for cmd, desc in commands:
        print(f"\n--- Testing {cmd} ({desc}) ---")
        send_luxos_command(host, cmd)

def main():
    """Test control functionality."""
    print("🔍 Testing Solar Miner Controls")
    print("=" * 40)
    
    host = "192.168.1.212"  # Working S21+
    
    print(f"Testing controls on {host} (S21+)")
    
    # First test available commands
    test_available_commands(host)
    
    # Then test profile commands
    test_profile_commands(host)

if __name__ == "__main__":
    main()