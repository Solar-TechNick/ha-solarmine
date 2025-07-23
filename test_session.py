#!/usr/bin/env python3
"""Test session authentication."""

import socket
import json
import time

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

def test_session_auth(host):
    """Test session-based authentication."""
    print(f"\n=== Testing Session Auth on {host} ===")
    
    # Try different session approaches
    session_tests = [
        ("login", "", "Try login command"),
        ("auth", "", "Try auth command"),
        ("session", "", "Try session command"),
        ("profileset", "session_id=test", "Try with session_id param"),
        ("profileset", "session_id=admin", "Try with admin session"),
        ("profileset", "session_id=default", "Try with default session"),
        ("profileset", "profile=default,session_id=admin", "Combined params"),
    ]
    
    for cmd, param, desc in session_tests:
        print(f"\n--- {desc} ---")
        result = send_luxos_command(host, cmd, param)
        
        if result and "STATUS" in result:
            status = result["STATUS"][0]
            if status.get("STATUS") == "S":
                print(f"✅ Success: {status.get('Msg', 'No message')}")
                return True
            else:
                print(f"❌ Failed: {status.get('Msg', 'No message')}")
        
    return False

def test_alternative_commands(host):
    """Test alternative control commands."""
    print(f"\n=== Testing Alternative Commands on {host} ===")
    
    # Test other possible control commands
    alt_commands = [
        ("frequency", "700", "Set frequency"),
        ("fanspeed", "50", "Set fan speed"),
        ("reboot", "", "Reboot (test only)"),
        ("restart", "", "Restart command"),
        ("powermode", "eco", "Power mode"),
        ("profile", "default", "Profile command"),
    ]
    
    for cmd, param, desc in alt_commands:
        print(f"\n--- {desc} ---")
        if cmd == "reboot":
            print("Skipping reboot test for safety")
            continue
            
        result = send_luxos_command(host, cmd, param)
        
        if result and "STATUS" in result:
            status = result["STATUS"][0]
            if status.get("STATUS") == "S":
                print(f"✅ {desc} works!")

def main():
    """Test session and alternative commands."""
    print("🔍 Testing LuxOS Session Auth & Alternatives")
    print("=" * 50)
    
    host = "192.168.1.212"
    
    # Test session authentication
    test_session_auth(host)
    
    # Test alternative commands
    test_alternative_commands(host)

if __name__ == "__main__":
    main()