#!/usr/bin/env python3
"""Test specific LuxOS API commands to understand the API structure."""

import urllib.request
import urllib.error
import json
import socket
import sys

def test_tcp_command(host, port, command, timeout=10):
    """Test TCP command and return result."""
    result = {
        "command": command,
        "status": None,
        "error": None,
        "data": None
    }
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((host, port))
            
            # Send command
            cmd_json = json.dumps({"command": command})
            sock.send((cmd_json + '\n').encode('utf-8'))
            
            # Receive response
            response = sock.recv(8192).decode('utf-8', errors='ignore').strip()
            result["status"] = "success"
            try:
                result["data"] = json.loads(response)
            except:
                result["data"] = response
            
    except Exception as e:
        result["error"] = f"Error: {e}"
    
    return result

def test_http_command(host, port, command, timeout=10):
    """Test HTTP API command."""
    result = {
        "command": command,
        "status": None,
        "error": None,
        "data": None
    }
    
    try:
        url = f"http://{host}:{port}/api"
        data = json.dumps({"command": command}).encode('utf-8')
        req = urllib.request.Request(url, data=data)
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            result["status"] = response.getcode()
            response_data = response.read().decode('utf-8', errors='ignore')
            try:
                result["data"] = json.loads(response_data)
            except:
                result["data"] = response_data
                
    except urllib.error.HTTPError as e:
        result["status"] = e.code
        result["error"] = f"HTTP Error {e.code}: {e.reason}"
    except Exception as e:
        result["error"] = f"Error: {e}"
    
    return result

def print_result(api_type, result):
    """Print formatted result."""
    print(f"\n📝 {api_type} - Command: {result['command']}")
    if result["error"]:
        print(f"   ❌ Error: {result['error']}")
    else:
        print(f"   ✅ Success")
        if isinstance(result["data"], dict):
            # Pretty print JSON data
            print(f"   📊 Response: {json.dumps(result['data'], indent=6)}")
        else:
            print(f"   📊 Response: {result['data']}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 test_luxos_commands.py <miner_ip>")
        sys.exit(1)
    
    miner_ip = sys.argv[1]
    
    # Common LuxOS API commands to test
    commands = [
        "version",     # Get version info
        "stats",       # Get mining statistics
        "summary",     # Get summary info
        "pools",       # Get pool information
        "devs",        # Get device information
        "config",      # Get configuration
        "devdetails",  # Get device details
    ]
    
    print("="*80)
    print(f"Testing LuxOS API Commands for {miner_ip}")
    print("="*80)
    
    for command in commands:
        # Test TCP API
        tcp_result = test_tcp_command(miner_ip, 4028, command)
        print_result("TCP API", tcp_result)
        
        # Test HTTP API
        http_result = test_http_command(miner_ip, 8080, command)
        print_result("HTTP API", http_result)
    
    print("\n" + "="*80)
    print("API Command Test Complete")
    print("="*80)

if __name__ == "__main__":
    main()