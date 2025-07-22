#!/bin/bash

# Solar Miner Home Assistant Integration Installation Script
# This script helps install the Solar Miner integration

set -e

echo "🌞 Solar Miner Home Assistant Integration Installer"
echo "=================================================="

# Check if Home Assistant config directory is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <home_assistant_config_directory>"
    echo "Example: $0 /config"
    echo "Example: $0 /home/homeassistant/.homeassistant"
    exit 1
fi

HA_CONFIG_DIR="$1"
CUSTOM_COMPONENTS_DIR="$HA_CONFIG_DIR/custom_components"
SOLARMINER_DIR="$CUSTOM_COMPONENTS_DIR/solarminer"

echo "📁 Home Assistant config directory: $HA_CONFIG_DIR"
echo "📦 Custom components directory: $CUSTOM_COMPONENTS_DIR"
echo "🎯 Solar Miner installation directory: $SOLARMINER_DIR"

# Check if Home Assistant config directory exists
if [ ! -d "$HA_CONFIG_DIR" ]; then
    echo "❌ Error: Home Assistant config directory '$HA_CONFIG_DIR' does not exist"
    exit 1
fi

# Create custom_components directory if it doesn't exist
if [ ! -d "$CUSTOM_COMPONENTS_DIR" ]; then
    echo "📁 Creating custom_components directory..."
    mkdir -p "$CUSTOM_COMPONENTS_DIR"
fi

# Create solarminer directory
echo "📁 Creating Solar Miner integration directory..."
mkdir -p "$SOLARMINER_DIR"

# Copy integration files
echo "📋 Copying integration files..."

files=(
    "__init__.py"
    "automation.py"
    "button.py"
    "config_flow.py"
    "const.py"
    "luxos_client.py"
    "manifest.json"
    "number.py"
    "select.py"
    "sensor.py"
    "services.yaml"
    "strings.json"
    "switch.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  📄 Copying $file..."
        cp "$file" "$SOLARMINER_DIR/"
    else
        echo "  ⚠️  Warning: $file not found in current directory"
    fi
done

# Set proper permissions
echo "🔐 Setting file permissions..."
chmod -R 644 "$SOLARMINER_DIR"/*
chmod 755 "$SOLARMINER_DIR"

# Copy dashboard examples to a documentation folder
DOCS_DIR="$HA_CONFIG_DIR/solarminer_docs"
if [ ! -d "$DOCS_DIR" ]; then
    echo "📚 Creating documentation directory..."
    mkdir -p "$DOCS_DIR"
fi

if [ -f "dashboard_s19j_pro_plus.yaml" ]; then
    echo "📋 Copying dashboard examples..."
    cp "dashboard_s19j_pro_plus.yaml" "$DOCS_DIR/"
    cp "dashboard_s21_plus.yaml" "$DOCS_DIR/"
    cp "README.md" "$DOCS_DIR/"
fi

echo ""
echo "✅ Solar Miner integration installed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Restart Home Assistant"
echo "2. Go to Settings → Devices & Services"
echo "3. Click 'Add Integration'"
echo "4. Search for 'Solar Miner'"
echo "5. Configure your miners:"
echo "   - S19j Pro+: 192.168.1.210"
echo "   - S21+: 192.168.1.212"
echo ""
echo "📚 Documentation and dashboard examples are in: $DOCS_DIR"
echo "📖 Check README.md for detailed setup instructions"
echo ""
echo "🌞 Happy solar mining!"