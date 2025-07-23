"""Constants for the Solar Miner integration."""

DOMAIN = "solarminer"

# Default configuration
DEFAULT_SCAN_INTERVAL = 10
DEFAULT_TIMEOUT = 10

# Miner models
MINER_S19J_PRO_PLUS = "s19j_pro_plus"
MINER_S21_PLUS = "s21_plus"

# Power profiles
POWER_PROFILES = {
    "max_power": {"name": "Max Power", "overclock": 2},
    "balanced": {"name": "Balanced", "overclock": 0},
    "ultra_eco": {"name": "Ultra Eco", "overclock": -2},
}

# Solar modes
SOLAR_MODES = {
    "manual": "Manual",
    "sun_curve": "Sun Curve",
}

# Night modes
NIGHT_MODES = {
    "30_percent": {"name": "Night Mode (30%)", "power_percent": 30},
    "15_percent": {"name": "Night Mode (15%)", "power_percent": 15},
    "standby": {"name": "Standby Mode (0%)", "power_percent": 0},
}

# Mining presets
MINING_PRESETS = {
    "solar_max": {"name": "Solar Max", "power_watts": 4200},
    "eco_mode": {"name": "Eco Mode", "power_watts": 1500},
}

# Temperature thresholds
TEMP_PROTECTION_THRESHOLD = 75.0
AUTO_REFRESH_INTERVAL = 30

# LuxOS API configuration
LUXOS_TCP_PORT = 4028  # Primary LuxOS TCP API port (recommended)
LUXOS_HTTP_PORT = 8080  # LuxOS HTTP API port (alternative)

# LuxOS API commands (used with both TCP and HTTP APIs)
LUXOS_COMMANDS = {
    "summary": "summary",
    "pools": "pools", 
    "devs": "devs",
    "stats": "stats",
    "config": "config",
    "version": "version",
    "devdetails": "devdetails",
    # Configuration commands
    "profileset": "profileset",
    "atmset": "atmset",
    "reboot": "reboot",
}