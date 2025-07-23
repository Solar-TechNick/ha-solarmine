#!/usr/bin/env python3
"""Test API response structure."""

import socket
import json

def get_luxos_data(host, port=4028):
    """Get actual LuxOS data to understand structure."""
    print(f"Getting data from {host}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        # Get summary
        command = json.dumps({"command": "summary"}) + "\n"
        sock.send(command.encode('utf-8'))
        response = sock.recv(8192)
        
        data = json.loads(response.decode('utf-8'))
        print(f"Summary response structure:")
        print(json.dumps(data, indent=2))
        
        sock.close()
        
        # Test devs command
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        command = json.dumps({"command": "devs"}) + "\n"
        sock.send(command.encode('utf-8'))
        response = sock.recv(8192)
        
        devs_data = json.loads(response.decode('utf-8'))
        print(f"\nDevs response structure:")
        print(json.dumps(devs_data, indent=2))
        
        sock.close()
        return data, devs_data
        
    except Exception as err:
        print(f"Error: {err}")
        return None, None

def main():
    """Test API response structure."""
    print("🔍 Testing API Response Structure")
    print("=" * 40)
    
    # Test working miner
    summary, devs = get_luxos_data("192.168.1.212")
    
    if summary:
        print(f"\n✅ S21+ API working correctly")
        print(f"Summary keys: {list(summary.keys())}")
        if "SUMMARY" in summary and summary["SUMMARY"]:
            print(f"Summary[0] keys: {list(summary['SUMMARY'][0].keys())}")
        
        if devs and "DEVS" in devs:
            print(f"Devs count: {len(devs['DEVS'])}")
            if devs["DEVS"]:
                print(f"Dev[0] keys: {list(devs['DEVS'][0].keys())}")

if __name__ == "__main__":
    main()