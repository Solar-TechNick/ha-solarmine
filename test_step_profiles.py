#!/usr/bin/env python3
"""Test step-based profile changes."""

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

def test_step_profiles(host):
    """Test step-based profile changes."""
    print(f"\n=== Testing Step-Based Profiles on {host} ===")
    
    # Based on the profiles data, test different step formats
    step_tests = [
        # Format: parameter_string, description, expected_step
        ("step=-2", "Eco mode (step -2, 660MHz, 5327W)", "-2"),
        ("step=0", "Default mode (step 0, 710MHz, 5908W)", "0"), 
        ("step=2", "High power (step 2, 760MHz, 6519W)", "2"),
        ("profile=660MHz", "660MHz profile by name", "-2"),
        ("profile=default", "Default profile by name", "0"),
        ("profile=760MHz", "760MHz profile by name", "2"),
        ("-2", "Just step number -2", "-2"),
        ("0", "Just step number 0", "0"),
        ("2", "Just step number 2", "2"),
    ]
    
    for param, desc, expected_step in step_tests:
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
                print("Checking current profile...")
                time.sleep(2)
                config_result = send_luxos_command(host, "config")
                if config_result and "CONFIG" in config_result:
                    current_step = config_result["CONFIG"][0].get("ProfileStep", "unknown")
                    current_profile = config_result["CONFIG"][0].get("Profile", "unknown")
                    print(f"Current step: {current_step}, Profile: {current_profile}")
                    
                    if str(current_step) == str(expected_step):
                        print(f"✅ Profile changed successfully to step {expected_step}")
                        return param  # Return working format
                    else:
                        print(f"⚠️ Step didn't change as expected (got {current_step}, expected {expected_step})")
                
            else:
                print(f"❌ Failed: {msg}")
    
    return None

def test_authentication_methods(host):
    """Test different authentication approaches."""
    print(f"\n=== Testing Authentication Methods on {host} ===")
    
    # Try to get authentication token or session
    auth_tests = [
        ("auth", "", "Basic auth command"),
        ("login", "admin", "Login as admin"),
        ("login", "root", "Login as root"),  
        ("session", "admin", "Session with admin"),
        ("token", "", "Get token"),
        ("challenge", "", "Get challenge"),
    ]
    
    for cmd, param, desc in auth_tests:
        print(f"\n--- {desc} ---")
        result = send_luxos_command(host, cmd, param)
        
        if result and "STATUS" in result:
            status = result["STATUS"][0]
            if status.get("STATUS") == "S":
                print(f"✅ {desc} worked!")
                
                # If session command worked, try using the session ID
                if cmd == "session" and "SESSION" in result:
                    session_data = result["SESSION"][0]
                    session_id = session_data.get("SessionID", "")
                    print(f"Got session ID: '{session_id}'")
                    
                    if session_id:
                        # Try profile change with this session ID
                        print("Testing profile change with session ID...")
                        profile_result = send_luxos_command(host, "profileset", f"session_id={session_id},step=-2")
                        return session_id
                        
            else:
                print(f"❌ {desc} failed: {status.get('Msg', 'No message')}")
    
    return None

def main():
    """Test step-based profile system."""
    print("🔍 Testing LuxOS Step-Based Profile System")
    print("=" * 50)
    
    host = "192.168.1.212"
    
    # First try direct step commands
    working_format = test_step_profiles(host)
    
    if working_format:
        print(f"\n✅ Found working profile format: {working_format}")
    else:
        print(f"\n❌ No direct profile changes worked, trying authentication...")
        
        # Try authentication methods
        session_id = test_authentication_methods(host)
        
        if not session_id:
            print(f"\n❌ Profile changes require web-based authentication")
            print("The integration will be read-only for profile changes")
            print("Users will need to change profiles via the web interface")

if __name__ == "__main__":
    main()