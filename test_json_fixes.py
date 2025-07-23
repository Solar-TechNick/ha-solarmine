#!/usr/bin/env python3
"""Test JSON parsing fixes for LuxOS API."""

import socket
import json

def test_large_response_handling():
    """Test handling of large JSON responses from LuxOS."""
    print("🔍 Testing Large Response Handling")
    print("=" * 40)
    
    host = "192.168.1.212"
    
    def get_response_with_buffer_handling(command):
        """Get response with improved buffer handling."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(15)  # Longer timeout for large responses
            sock.connect((host, 4028))
            
            cmd_data = {"command": command}
            cmd_json = json.dumps(cmd_data) + "\n"
            sock.send(cmd_json.encode('utf-8'))
            
            # Read response in chunks like the fixed client
            response_data = b""
            while True:
                chunk = sock.recv(8192)
                if not chunk:
                    break
                response_data += chunk
                
                # Check if we have a complete JSON response
                try:
                    response_text = response_data.decode('utf-8', errors='ignore')
                    if response_text.strip().endswith('}'):
                        break
                except UnicodeDecodeError:
                    continue
            
            response_text = response_data.decode('utf-8', errors='ignore').strip()
            
            # Handle potential truncation
            if not response_text:
                return None, "Empty response"
            
            if not response_text.endswith('}'):
                print(f"⚠️  Response appears truncated")
                print(f"   Length: {len(response_text)} characters")
                print(f"   Ends with: '{response_text[-20:]}'")
                
                # Try to fix truncation
                last_brace = response_text.rfind('}')
                if last_brace > 0:
                    response_text = response_text[:last_brace + 1]
                    print(f"   Fixed by truncating to last complete brace")
                else:
                    return None, "Severely truncated"
            
            # Parse JSON
            try:
                result = json.loads(response_text)
                return result, "Success"
            except json.JSONDecodeError as err:
                return None, f"JSON Error: {err}"
                
        except Exception as err:
            return None, f"Connection Error: {err}"
        finally:
            sock.close()
    
    # Test commands that might have large responses
    test_commands = [
        ("summary", "Basic summary data"),
        ("devs", "Device data"),
        ("stats", "Statistics data"),
        ("profiles", "Profile data (large)"),
        ("config", "Configuration data"),
    ]
    
    results = {}
    
    for command, desc in test_commands:
        print(f"\n--- Testing {command} ({desc}) ---")
        result, status = get_response_with_buffer_handling(command)
        
        if result:
            # Analyze response
            response_size = len(json.dumps(result))
            print(f"✅ {status}")
            print(f"   Response size: {response_size:,} characters")
            
            if command == "profiles" and "PROFILES" in result:
                profile_count = len(result["PROFILES"])
                print(f"   Profiles found: {profile_count}")
                
            results[command] = {
                "success": True,
                "size": response_size,
                "data": result
            }
        else:
            print(f"❌ {status}")
            results[command] = {
                "success": False,
                "error": status
            }
    
    return results

def analyze_profile_data(results):
    """Analyze profile data structure."""
    print(f"\n🔍 Profile Data Analysis")
    print("=" * 30)
    
    if "profiles" in results and results["profiles"]["success"]:
        profiles_data = results["profiles"]["data"]
        
        if "PROFILES" in profiles_data:
            profiles = profiles_data["PROFILES"]
            print(f"✅ Found {len(profiles)} profiles")
            
            # Show first few profiles
            for i, profile in enumerate(profiles[:3]):
                name = profile.get("Profile Name", "Unknown")
                step = profile.get("Step", "?")
                watts = profile.get("Watts", "?")
                hashrate = profile.get("Hashrate", "?")
                freq = profile.get("Frequency", "?")
                
                print(f"   Profile {i+1}: {name}")
                print(f"     Step: {step}, Freq: {freq}MHz")
                print(f"     Power: {watts}W, Hashrate: {hashrate} TH/s")
        else:
            print(f"❌ No PROFILES key in response")
    else:
        print(f"❌ Profile data failed to load")
        if "profiles" in results:
            print(f"   Error: {results['profiles'].get('error', 'Unknown')}")

def show_fixes_summary():
    """Show what fixes were implemented."""
    print(f"\n🔧 JSON Parsing Fixes Summary")
    print("=" * 35)
    
    print("PROBLEMS IDENTIFIED:")
    print("  ❌ JSON responses getting truncated around char 1365-1369")
    print("  ❌ 8192 byte buffer too small for large profile data")
    print("  ❌ No handling for incomplete JSON responses")
    print("  ❌ Poor error messages for debugging")
    
    print("\nFIXES IMPLEMENTED:")
    print("  ✅ Chunked reading with completion detection")
    print("  ✅ Automatic truncation repair (find last })")
    print("  ✅ Better error logging with response snippets")
    print("  ✅ Fallback handling in coordinator")
    print("  ✅ Defensive programming in new sensors")
    print("  ✅ Longer timeout for large responses")
    
    print("\nRESULT:")
    print("  🎉 Large profile data should now load correctly")
    print("  🎉 Better error messages for debugging")
    print("  🎉 Integration continues working even if some data fails")

def main():
    """Test the JSON parsing fixes."""
    print("🚀 Testing JSON Parsing Fixes")
    print("=" * 40)
    
    results = test_large_response_handling()
    analyze_profile_data(results)
    show_fixes_summary()
    
    # Summary
    successful_commands = sum(1 for r in results.values() if r["success"])
    total_commands = len(results)
    
    print(f"\n📊 Results: {successful_commands}/{total_commands} commands successful")
    
    if successful_commands == total_commands:
        print("🎉 All API calls working correctly!")
    else:
        print("⚠️  Some API calls still having issues")
        failed = [cmd for cmd, result in results.items() if not result["success"]]
        print(f"   Failed commands: {', '.join(failed)}")

if __name__ == "__main__":
    main()