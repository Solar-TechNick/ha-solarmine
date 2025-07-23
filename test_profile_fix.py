#!/usr/bin/env python3
"""Test proper profile setting with session."""

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

def get_session_id(host):
    """Get session ID from LuxOS."""
    print("Getting session ID...")
    result = send_luxos_command(host, "session")
    
    if result and "SESSION" in result and result["SESSION"]:
        session_id = result["SESSION"][0].get("SessionID", "")
        print(f"Session ID: '{session_id}'")
        return session_id
    
    return ""

def test_profile_with_session(host):
    """Test profile setting with session ID."""
    print(f"\n=== Testing Profile with Session on {host} ===")
    
    # Get session ID
    session_id = get_session_id(host)
    
    # Test different profile parameter formats with session_id
    profile_tests = [
        # Format: parameter_string, description
        (f"session_id={session_id},profile=default", "Default profile with session"),
        (f"session_id={session_id},delta=0", "Delta 0 with session"),
        (f"session_id={session_id},delta=2", "Delta +2 with session"),
        (f"session_id={session_id},delta=-2", "Delta -2 with session"),
        (f"profile=default,session_id={session_id}", "Profile first, session second"),
        (f"delta=0,session_id={session_id}", "Delta first, session second"),
        (f"session_id={session_id}", "Session ID only"),
    ]
    
    for param, desc in profile_tests:
        print(f"\n--- Testing {desc} ---")
        result = send_luxos_command(host, "profileset", param)
        
        if result and "STATUS" in result:
            status = result["STATUS"][0]
            status_code = status.get("STATUS", "E")
            msg = status.get("Msg", "No message")
            
            if status_code == "S":
                print(f"✅ SUCCESS: {desc}")
                print(f"Message: {msg}")
                
                # Check if profile actually changed
                print("Checking if profile changed...")
                config_result = send_luxos_command(host, "config")
                if config_result and "CONFIG" in config_result:
                    current_profile = config_result["CONFIG"][0].get("Profile", "unknown")
                    print(f"Current profile: {current_profile}")
                
                return True
            else:
                print(f"❌ Failed: {msg}")
    
    return False

def main():
    """Test profile setting with proper session."""
    print("🔍 Testing LuxOS Profile Setting with Session")
    print("=" * 50)
    
    host = "192.168.1.212"
    
    success = test_profile_with_session(host)
    
    if success:
        print("\n✅ Found working profile command format!")
    else:
        print("\n❌ No working profile command format found")
        print("LuxOS may require web-based authentication or different approach")

if __name__ == "__main__":
    main()