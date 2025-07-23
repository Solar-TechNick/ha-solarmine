#!/usr/bin/env python3
"""Check available profiles and test different approaches."""

import socket
import json

def send_luxos_command(host, command, parameter="", port=4028):
    """Send command to LuxOS API."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        cmd_data = {"command": command}
        if parameter:
            cmd_data["parameter"] = parameter
            
        cmd_json = json.dumps(cmd_data) + "\n"
        print(f"Command: {cmd_json.strip()}")
        
        sock.send(cmd_json.encode('utf-8'))
        response = sock.recv(8192)
        
        data = json.loads(response.decode('utf-8'))
        print(f"Response: {json.dumps(data, indent=2)}")
        
        return data
        
    except Exception as err:
        print(f"Error: {err}")
        return None
    finally:
        sock.close()

def main():
    """Check profiles and other details."""
    print("🔍 Checking LuxOS Profiles and Configuration")
    print("=" * 50)
    
    host = "192.168.1.212"
    
    print("\n--- Available Profiles ---")
    send_luxos_command(host, "profiles")
    
    print("\n--- ATM Configuration ---")
    send_luxos_command(host, "atm")
    
    print("\n--- Power Information ---")
    send_luxos_command(host, "power")
    
    print("\n--- Current Configuration ---")
    config_result = send_luxos_command(host, "config")
    
    if config_result and "CONFIG" in config_result:
        config = config_result["CONFIG"][0]
        print(f"\nKey Configuration Values:")
        print(f"  Profile: {config.get('Profile', 'Unknown')}")
        print(f"  ProfileStep: {config.get('ProfileStep', 'Unknown')}")
        print(f"  IsAtmEnabled: {config.get('IsAtmEnabled', 'Unknown')}")
        print(f"  IsTuning: {config.get('IsTuning', 'Unknown')}")

if __name__ == "__main__":
    main()