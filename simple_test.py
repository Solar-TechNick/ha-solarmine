#!/usr/bin/env python3
"""Simple connectivity test without dependencies."""

import socket
import json
import time

def test_tcp_connection(host, port=4028):
    """Test basic TCP connection to LuxOS API."""
    print(f"Testing TCP connection to {host}:{port}...")
    
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        # Connect
        result = sock.connect_ex((host, port))
        
        if result == 0:
            print(f"✅ TCP connection to {host}:{port} successful")
            
            # Try sending a simple command
            try:
                command = json.dumps({"command": "summary"}) + "\n"
                sock.send(command.encode('utf-8'))
                
                # Read response
                response = sock.recv(4096)
                if response:
                    print(f"✅ Received response: {len(response)} bytes")
                    try:
                        data = json.loads(response.decode('utf-8'))
                        print(f"✅ Valid JSON response with keys: {list(data.keys())}")
                        return True
                    except json.JSONDecodeError:
                        print(f"❌ Invalid JSON response: {response[:100]}...")
                        return False
                else:
                    print("❌ No response received")
                    return False
                    
            except Exception as cmd_err:
                print(f"❌ Command failed: {cmd_err}")
                return False
        else:
            print(f"❌ TCP connection to {host}:{port} failed: {result}")
            return False
            
    except Exception as err:
        print(f"❌ Connection error: {err}")
        return False
    finally:
        sock.close()

def test_http_connection(host, port=8080):
    """Test basic HTTP connection."""
    import urllib.request
    import urllib.error
    
    url = f"http://{host}:{port}/api"
    print(f"Testing HTTP connection to {url}...")
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps({"command": "summary"}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = response.read()
            print(f"✅ HTTP connection successful: {len(data)} bytes")
            
            try:
                json_data = json.loads(data.decode('utf-8'))
                print(f"✅ Valid JSON response with keys: {list(json_data.keys())}")
                return True
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {data[:100]}...")
                return False
                
    except urllib.error.URLError as err:
        print(f"❌ HTTP connection failed: {err}")
        return False
    except Exception as err:
        print(f"❌ HTTP error: {err}")
        return False

def main():
    """Main test function."""
    print("🔍 Simple Miner Connectivity Test")
    print("=" * 40)
    
    miners = [
        ("192.168.1.210", "S19j Pro+"),
        ("192.168.1.212", "S21+")
    ]
    
    success_count = 0
    
    for host, name in miners:
        print(f"\n=== Testing {name} ({host}) ===")
        
        tcp_success = test_tcp_connection(host, 4028)
        http_success = test_http_connection(host, 8080)
        
        if tcp_success or http_success:
            success_count += 1
            print(f"✅ {name} is reachable")
        else:
            print(f"❌ {name} is not reachable")
    
    print(f"\n📊 Results: {success_count}/{len(miners)} miners reachable")
    
    if success_count == 0:
        print("\n🚨 Troubleshooting steps:")
        print("1. Check if miners are powered on")
        print("2. Verify IP addresses: ping 192.168.1.210 and ping 192.168.1.212")
        print("3. Check if LuxOS firmware is running")
        print("4. Try accessing http://192.168.1.210:8080 in browser")

if __name__ == "__main__":
    main()