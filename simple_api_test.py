#!/usr/bin/env python3
"""Simple test script to identify correct LuxOS API endpoints using standard library."""

import urllib.request
import urllib.error
import json
import socket
import sys
import time

def test_http_endpoint(url, timeout=10):
    """Test HTTP endpoint and return result info."""
    result = {
        "url": url,
        "status": None,
        "error": None,
        "data_preview": None,
        "content_type": None
    }
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            result["status"] = response.getcode()
            result["content_type"] = response.headers.get('Content-Type', '')
            
            data = response.read()
            if data:
                try:
                    # Try to decode as text
                    text = data.decode('utf-8', errors='ignore')
                    result["data_preview"] = text[:200] + "..." if len(text) > 200 else text
                except:
                    result["data_preview"] = f"Binary data ({len(data)} bytes)"
            
    except urllib.error.HTTPError as e:
        result["status"] = e.code
        result["error"] = f"HTTP Error {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        result["error"] = f"URL Error: {e.reason}"
    except Exception as e:
        result["error"] = f"Error: {e}"
    
    return result

def test_http_post(url, data, timeout=10):
    """Test HTTP POST endpoint."""
    result = {
        "url": url,
        "method": "POST",
        "status": None,
        "error": None,
        "data_preview": None,
        "content_type": None
    }
    
    try:
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=json_data)
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            result["status"] = response.getcode()
            result["content_type"] = response.headers.get('Content-Type', '')
            
            response_data = response.read()
            if response_data:
                try:
                    text = response_data.decode('utf-8', errors='ignore')
                    result["data_preview"] = text[:200] + "..." if len(text) > 200 else text
                except:
                    result["data_preview"] = f"Binary data ({len(response_data)} bytes)"
            
    except urllib.error.HTTPError as e:
        result["status"] = e.code
        result["error"] = f"HTTP Error {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        result["error"] = f"URL Error: {e.reason}"
    except Exception as e:
        result["error"] = f"Error: {e}"
    
    return result

def test_tcp_connection(host, port, command='{"command":"version"}', timeout=10):
    """Test TCP connection (for LuxOS API on port 4028)."""
    result = {
        "host": host,
        "port": port,
        "command": command,
        "status": None,
        "error": None,
        "data_preview": None
    }
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((host, port))
            
            # Send command
            sock.send((command + '\n').encode('utf-8'))
            
            # Receive response
            response = sock.recv(4096).decode('utf-8', errors='ignore')
            result["status"] = "success"
            result["data_preview"] = response[:200] + "..." if len(response) > 200 else response
            
    except Exception as e:
        result["error"] = f"TCP Error: {e}"
    
    return result

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 simple_api_test.py <miner_ip>")
        print("Example: python3 simple_api_test.py 192.168.1.212")
        sys.exit(1)
    
    miner_ip = sys.argv[1]
    base_url = f"http://{miner_ip}"
    
    print("="*80)
    print(f"Testing LuxOS API endpoints for {miner_ip}")
    print("="*80)
    
    # Test endpoints to try
    endpoints = [
        # LuxOS HTTP API (port 8080) - POST
        (f"http://{miner_ip}:8080/api", "POST", {"command": "version"}),
        
        # Standard Antminer CGI endpoints
        (f"{base_url}/cgi-bin/minerStatus.cgi", "GET", None),
        (f"{base_url}/cgi-bin/minerConfiguration.cgi", "GET", None),
        (f"{base_url}/cgi-bin/get_miner_status.cgi", "GET", None),
        (f"{base_url}/cgi-bin/minerAdvanced.cgi", "GET", None),
        
        # Original failing endpoints
        (f"{base_url}/cgi-bin/luci/admin/miner/api/summary", "GET", None),
        (f"{base_url}/cgi-bin/luci/admin/miner/api/pools", "GET", None),
        (f"{base_url}/cgi-bin/luci/admin/miner/api/devs", "GET", None),
        
        # Alternative API patterns
        (f"{base_url}/api/v1/summary", "GET", None),
        (f"{base_url}/api/summary", "GET", None),
        (f"{base_url}/cgi-bin/api/summary", "GET", None),
        (f"{base_url}/miner/api/summary", "GET", None),
    ]
    
    successful_endpoints = []
    
    # Test TCP API first (port 4028)
    print(f"\n🔍 Testing TCP API (port 4028)...")
    tcp_result = test_tcp_connection(miner_ip, 4028)
    if tcp_result["error"]:
        print(f"❌ TCP API: {tcp_result['error']}")
    else:
        print(f"✅ TCP API: Connected successfully")
        print(f"   Preview: {tcp_result['data_preview']}")
        successful_endpoints.append(("TCP API", f"{miner_ip}:4028", "TCP"))
    
    # Test HTTP endpoints
    for url, method, post_data in endpoints:
        print(f"\n🔍 Testing {method} {url}")
        
        if method == "POST" and post_data:
            result = test_http_post(url, post_data)
        else:
            result = test_http_endpoint(url)
        
        if result["error"]:
            print(f"❌ Error: {result['error']}")
        elif result["status"] == 200:
            print(f"✅ Status: {result['status']}")
            if result["content_type"]:
                print(f"   Content-Type: {result['content_type']}")
            if result["data_preview"]:
                print(f"   Preview: {result['data_preview']}")
            successful_endpoints.append(("HTTP", url, method))
        else:
            print(f"⚠️  Status: {result['status']}")
            if result["data_preview"]:
                print(f"   Preview: {result['data_preview']}")
    
    # Summary
    print(f"\n" + "="*80)
    print(f"SUMMARY: {len(successful_endpoints)} successful endpoints found")
    print("="*80)
    
    if successful_endpoints:
        print("\n✅ Working API endpoints:")
        for api_type, endpoint, method in successful_endpoints:
            print(f"  • {api_type}: {endpoint} ({method})")
    else:
        print("\n❌ No working API endpoints found")
        print("\nPossible issues:")
        print("  • Miner may be using different firmware")
        print("  • API may be disabled")
        print("  • Authentication may be required")
        print("  • Different port configuration")
    
    print(f"\n💡 Recommendations:")
    if any(endpoint[0] == "TCP API" for endpoint in successful_endpoints):
        print("  • Use TCP API on port 4028 (most reliable for LuxOS)")
    if any(endpoint[2] == "POST" for endpoint in successful_endpoints):
        print("  • Use HTTP API on port 8080 with POST requests")
    if any(endpoint[2] == "GET" and "cgi-bin" in endpoint[1] for endpoint in successful_endpoints):
        print("  • Standard Antminer CGI endpoints are available")

if __name__ == "__main__":
    main()