#!/usr/bin/env python3
"""Simple test script to verify LuxOS API connection."""

import asyncio
import sys
import socket
import json

async def test_tcp_connection(host: str, port: int = 4028):
    """Test TCP connection to LuxOS API."""
    print(f"Testing TCP connection to {host}:{port}...")
    
    try:
        # Test TCP connection
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), 
            timeout=5
        )
        
        # Send summary command
        cmd_data = {"command": "summary"}
        cmd_json = json.dumps(cmd_data) + "\n"
        writer.write(cmd_json.encode('utf-8'))
        await writer.drain()
        
        # Read response
        response_data = await asyncio.wait_for(reader.read(8192), timeout=5)
        writer.close()
        await writer.wait_closed()
        
        # Parse response
        response_text = response_data.decode('utf-8', errors='ignore').strip()
        result = json.loads(response_text)
        
        print("✅ TCP API connection successful!")
        print(f"Miner: {result.get('SUMMARY', [{}])[0].get('Type', 'Unknown')}")
        print(f"Status: {result.get('SUMMARY', [{}])[0].get('Status', 'Unknown')}")
        return True
        
    except Exception as e:
        print(f"❌ TCP API connection failed: {e}")
        return False

async def test_version_command(host: str, port: int = 4028):
    """Test version command."""
    print(f"\nTesting version command...")
    
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), 
            timeout=5
        )
        
        # Send version command
        cmd_data = {"command": "version"}
        cmd_json = json.dumps(cmd_data) + "\n"
        writer.write(cmd_json.encode('utf-8'))
        await writer.drain()
        
        # Read response
        response_data = await asyncio.wait_for(reader.read(8192), timeout=5)
        writer.close()
        await writer.wait_closed()
        
        # Parse response
        response_text = response_data.decode('utf-8', errors='ignore').strip()
        result = json.loads(response_text)
        
        version_info = result.get('VERSION', [{}])[0]
        print("✅ Version command successful!")
        print(f"LuxOS Version: {version_info.get('LUXminer', 'Unknown')}")
        print(f"Type: {version_info.get('Type', 'Unknown')}")
        return True
        
    except Exception as e:
        print(f"❌ Version command failed: {e}")
        return False

async def main():
    """Main test function."""
    if len(sys.argv) != 2:
        print("Usage: python3 test_connection.py <miner_ip>")
        print("Example: python3 test_connection.py 192.168.1.212")
        sys.exit(1)
    
    host = sys.argv[1]
    print(f"Testing connection to {host}...")
    
    # Test TCP API
    tcp_success = await test_tcp_connection(host)
    if tcp_success:
        await test_version_command(host)
    
    # Test basic socket connection to different ports
    print(f"\nTesting socket connections...")
    for port in [4028, 8080, 80]:
        try:
            sock = socket.create_connection((host, port), timeout=2)
            sock.close()
            print(f"✅ Port {port}: Open")
        except:
            print(f"❌ Port {port}: Closed/Filtered")

if __name__ == "__main__":
    asyncio.run(main())