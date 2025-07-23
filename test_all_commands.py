#!/usr/bin/env python3
"""Test all possible LuxOS commands to find working ones."""

import socket
import json

def send_luxos_command(host, command, parameter="", port=4028):
    """Send command to LuxOS API."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        
        cmd_data = {"command": command}
        if parameter:
            cmd_data["parameter"] = parameter
            
        cmd_json = json.dumps(cmd_data) + "\n"
        
        sock.send(cmd_json.encode('utf-8'))
        response = sock.recv(8192)
        
        data = json.loads(response.decode('utf-8'))
        
        # Check if command is valid
        if "STATUS" in data and data["STATUS"]:
            status = data["STATUS"][0]
            status_code = status.get("STATUS", "E")
            msg = status.get("Msg", "")
            code = status.get("Code", 0)
            
            # Code 14 = Invalid command
            if code == 14:
                return None
            
            return {
                "command": command,
                "parameter": parameter,
                "status": status_code,
                "message": msg,
                "response": data
            }
        
        return None
        
    except Exception:
        return None
    finally:
        sock.close()

def test_cgminer_commands(host):
    """Test common CGMiner/LUXminer commands."""
    print(f"🔍 Testing CGMiner/LUXminer Commands on {host}")
    print("=" * 50)
    
    # Common CGMiner commands that might work
    commands = [
        # Basic info commands
        ("summary", "", "Get summary"),
        ("devs", "", "Get devices"),
        ("pools", "", "Get pools"),
        ("stats", "", "Get stats"),
        ("config", "", "Get config"),
        ("version", "", "Get version"),
        
        # Profile/power commands
        ("profiles", "", "List profiles"),
        ("profile", "", "Get current profile"),
        ("setprofile", "0", "Set profile 0"),
        ("setprofile", "1", "Set profile 1"),
        ("setprofile", "2", "Set profile 2"),
        
        # Frequency commands
        ("asccount", "", "Get ASC count"),
        ("asc", "0", "Get ASC 0 info"),
        ("ascenable", "0", "Enable ASC 0"),
        ("ascdisable", "0", "Disable ASC 0"),
        ("ascset", "0,freq,700", "Set ASC 0 frequency"),
        
        # Fan commands
        ("fancount", "", "Get fan count"),
        ("fan", "0", "Get fan 0 info"),
        ("fanset", "0,50", "Set fan 0 speed"),
        
        # Power commands
        ("power", "", "Get power info"),
        ("powerset", "3000", "Set power limit"),
        ("frequency", "700", "Set frequency"),
        
        # Mining commands
        ("restart", "", "Restart mining"),
        ("quit", "", "Quit (don't actually run)"),
        ("zero", "", "Zero stats"),
        
        # Pool commands
        ("addpool", "", "Add pool"),
        ("removepool", "0", "Remove pool"),
        ("switchpool", "0", "Switch to pool"),
        ("enablepool", "0", "Enable pool"),
        ("disablepool", "0", "Disable pool"),
        
        # ATM/thermal commands
        ("atm", "", "Get ATM info"),
        ("atmset", "auto,75", "Set ATM"),
        ("thermal", "", "Get thermal info"),
        
        # System commands
        ("uptime", "", "Get uptime"),
        ("coin", "", "Get coin info"),
        ("lcd", "", "Get LCD info"),
        ("notify", "", "Get notifications"),
        ("devdetails", "", "Get device details"),
        ("usbstats", "", "Get USB stats"),
        ("debug", "", "Get debug info"),
        ("setdebug", "normal", "Set debug level"),
    ]
    
    working_commands = []
    
    for command, param, desc in commands:
        # Skip dangerous commands
        if command in ["quit", "restart"]:
            print(f"⚠️  Skipping dangerous command: {command}")
            continue
            
        result = send_luxos_command(host, command, param)
        
        if result:
            status_icon = "✅" if result["status"] == "S" else "⚠️"
            print(f"{status_icon} {command:15} | {desc:25} | {result['message']}")
            working_commands.append(result)
        else:
            print(f"❌ {command:15} | {desc:25} | Invalid command")
    
    return working_commands

def main():
    """Test all available commands."""
    host = "192.168.1.212"
    
    working = test_cgminer_commands(host)
    
    print(f"\n📊 Found {len(working)} working commands")
    
    # Show working control commands
    control_commands = [cmd for cmd in working if cmd["command"] in [
        "setprofile", "ascset", "fanset", "powerset", "atmset", "frequency"
    ]]
    
    if control_commands:
        print(f"\n🎛️ Working Control Commands:")
        for cmd in control_commands:
            print(f"  • {cmd['command']} - {cmd['message']}")
    else:
        print(f"\n❌ No working control commands found")

if __name__ == "__main__":
    main()