# Solar Miner Home Assistant Integration

A comprehensive Home Assistant integration for managing Antminer S19j Pro+ and S21+ miners running LuxOS with advanced solar mining capabilities.

## Features

### Mining Control
- **Pause/Resume**: Instantly disable/enable all hashboards
- **Solar Max**: Set 4200W and enable miner for maximum solar power utilization
- **Eco Mode**: Set 1500W for energy-efficient mining
- **Emergency Stop**: Immediate shutdown of all mining operations

### Power Profiles
- **Max Power**: +2 overclock profile for peak performance
- **Balanced**: Default profile for optimal efficiency
- **Ultra Eco**: -2 underclock profile for minimal power consumption

### Hashboard Control
- **Individual Board Toggle**: Control boards 0, 1, and 2 independently
- **Real-time Status**: Monitor temperature, frequency, voltage per board
- **Smart Automation**: Automatic board management based on solar power

### Real-time Monitoring
- **Auto-refresh**: Updates every 30-60 seconds
- **State Colors**: Visual status indicators
- **Performance Metrics**: Hashrate, power consumption, efficiency
- **Temperature Monitoring**: Per-board and overall temperature tracking

### Solar Integration
- **Manual Power Input**: Set available solar power (0-50000W)
- **Sun Curve Mode**: Automatic power adjustment following sun patterns
- **Solar Efficiency Gauge**: Visual feedback on solar utilization
- **Peak Solar Mode**: 120% power during maximum sun availability

### Night Operations
- **Night Mode (30%)**: Quiet operation at 30% power
- **Night Mode (15%)**: Ultra-quiet operation at 15% power
- **Standby Mode**: Complete shutdown for silent nights

### Smart Automation
- **10-minute Intervals**: Automatic solar power adjustments
- **Auto Standby**: Automatic shutdown when solar power drops below threshold
- **Auto Restart**: Automatic restart when solar power exceeds set point
- **Temperature Protection**: Auto-underclock at 75°C

### Advanced Controls
- **Performance Scaling**: 50% to 130% performance adjustment
- **Custom Power Limits**: Set specific wattage limits
- **Pool Management**: Switch between mining pools
- **Mobile Dashboard**: Full control from mobile devices

## Installation

### Method 1: HACS (Recommended)

1. Open HACS in your Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/yourusername/ha-solarminer`
6. Select "Integration" as the category
7. Click "Add"
8. Search for "Solar Miner" and install

### Method 2: Manual Installation

1. Download this repository
2. Copy the `solarminer` folder to your `custom_components` directory:
   ```
   <config>/custom_components/solarminer/
   ```
3. Restart Home Assistant

## Configuration

### Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Solar Miner"
4. Enter your miner details:
   - **IP Address**: Your miner's IP (e.g., 192.168.1.210 or 192.168.1.212)
   - **Port**: Usually 80 (default)
   - **Username**: Optional, if authentication is enabled
   - **Password**: Optional, if authentication is enabled

### Multiple Miners

For multiple miners, add each one separately:
- Antminer S19j Pro+: 192.168.1.210
- Antminer S21+: 192.168.1.212

## Entities Created

### Sensors
- `sensor.solar_miner_[ip]_hashrate` - Total hashrate in TH/s
- `sensor.solar_miner_[ip]_power` - Power consumption in watts
- `sensor.solar_miner_[ip]_temperature` - Maximum temperature
- `sensor.solar_miner_[ip]_efficiency` - Efficiency in J/TH
- `sensor.solar_miner_[ip]_board_[0-2]` - Individual board hashrates
- `sensor.solar_miner_[ip]_solar_power` - Available solar power
- `sensor.solar_miner_[ip]_solar_efficiency` - Solar utilization percentage

### Switches
- `switch.solar_miner_[ip]_board_[0-2]` - Individual hashboard controls
- `switch.solar_miner_[ip]_mining` - Main mining switch
- `switch.solar_miner_[ip]_solar_mode` - Solar automation mode
- `switch.solar_miner_[ip]_auto_standby` - Auto standby when low solar

### Buttons
- `button.solar_miner_[ip]_pause` - Pause all mining
- `button.solar_miner_[ip]_resume` - Resume all mining
- `button.solar_miner_[ip]_solar_max` - Set 4200W mode
- `button.solar_miner_[ip]_eco_mode` - Set 1500W mode
- `button.solar_miner_[ip]_max_power` - Apply +2 overclock
- `button.solar_miner_[ip]_balanced` - Apply default profile
- `button.solar_miner_[ip]_ultra_eco` - Apply -2 underclock
- `button.solar_miner_[ip]_night_mode_30` - 30% power mode
- `button.solar_miner_[ip]_night_mode_15` - 15% power mode
- `button.solar_miner_[ip]_standby` - Standby mode
- `button.solar_miner_[ip]_peak_solar` - 120% power mode

### Number Inputs
- `number.solar_miner_[ip]_solar_power` - Solar power input (0-50000W)
- `number.solar_miner_[ip]_power_limit` - Power limit setting
- `number.solar_miner_[ip]_minimum_power` - Auto standby threshold
- `number.solar_miner_[ip]_temp_protection` - Temperature protection threshold
- `number.solar_miner_[ip]_performance` - Performance level (50-130%)
- `number.solar_miner_[ip]_automation_interval` - Automation interval (minutes)

### Select Inputs
- `select.solar_miner_[ip]_solar_mode` - Manual/Sun Curve mode
- `select.solar_miner_[ip]_night_mode` - Night mode selection
- `select.solar_miner_[ip]_power_profile` - Power profile selection
- `select.solar_miner_[ip]_pool` - Mining pool selection

## Services

### solarminer.set_solar_power
Set available solar power in watts
```yaml
service: solarminer.set_solar_power
target:
  entity_id: sensor.solar_miner_192_168_1_210_hashrate
data:
  power_watts: 5000
```

### solarminer.apply_sun_curve
Enable/disable automatic sun curve following
```yaml
service: solarminer.apply_sun_curve
target:
  entity_id: sensor.solar_miner_192_168_1_210_hashrate
data:
  enable: true
```

### solarminer.set_hashboard_power
Control individual hashboards
```yaml
service: solarminer.set_hashboard_power
target:
  entity_id: sensor.solar_miner_192_168_1_210_hashrate
data:
  board: 0
  enabled: false
```

### solarminer.emergency_stop
Emergency stop all mining operations
```yaml
service: solarminer.emergency_stop
target:
  entity_id: sensor.solar_miner_192_168_1_210_hashrate
```

## Dashboard Examples

### Basic Solar Mining Dashboard

```yaml
type: grid
cards:
  - type: entity
    entity: sensor.solar_miner_192_168_1_210_hashrate
    name: "S19j Pro+ Hashrate"
  - type: entity
    entity: sensor.solar_miner_192_168_1_210_power
    name: "Power Consumption"
  - type: entity
    entity: number.solar_miner_192_168_1_210_solar_power
    name: "Solar Power Available"
  - type: entities
    title: "Mining Controls"
    entities:
      - button.solar_miner_192_168_1_210_pause
      - button.solar_miner_192_168_1_210_resume
      - button.solar_miner_192_168_1_210_solar_max
      - button.solar_miner_192_168_1_210_eco_mode
  - type: entities
    title: "Power Profiles"
    entities:
      - button.solar_miner_192_168_1_210_max_power
      - button.solar_miner_192_168_1_210_balanced
      - button.solar_miner_192_168_1_210_ultra_eco
  - type: entities
    title: "Hashboard Control"
    entities:
      - switch.solar_miner_192_168_1_210_board_0
      - switch.solar_miner_192_168_1_210_board_1
      - switch.solar_miner_192_168_1_210_board_2
```

### Solar Efficiency Gauge

```yaml
type: gauge
entity: sensor.solar_miner_192_168_1_210_solar_efficiency
name: "Solar Efficiency"
min: 0
max: 100
severity:
  green: 80
  yellow: 60
  red: 0
```

### Temperature Monitoring

```yaml
type: history-graph
entities:
  - sensor.solar_miner_192_168_1_210_temperature
  - sensor.solar_miner_192_168_1_212_temperature
hours_to_show: 24
refresh_interval: 60
```

## Automation Examples

### Automatic Solar Power Adjustment

```yaml
alias: "Solar Mining Automation"
trigger:
  - platform: time_pattern
    minutes: "/10"  # Every 10 minutes
condition:
  - condition: state
    entity_id: switch.solar_miner_192_168_1_210_solar_mode
    state: "on"
action:
  - service: solarminer.update_automation
    target:
      entity_id: sensor.solar_miner_192_168_1_210_hashrate
```

### Temperature Protection

```yaml
alias: "Miner Temperature Protection"
trigger:
  - platform: numeric_state
    entity_id: sensor.solar_miner_192_168_1_210_temperature
    above: 75
action:
  - service: button.press
    target:
      entity_id: button.solar_miner_192_168_1_210_ultra_eco
  - service: notify.mobile_app
    data:
      message: "Miner temperature high - switched to Ultra Eco mode"
```

### Night Mode Automation

```yaml
alias: "Night Mode Automation"
trigger:
  - platform: sun
    event: sunset
action:
  - service: select.select_option
    target:
      entity_id: select.solar_miner_192_168_1_210_night_mode
    data:
      option: "Night Mode (15%)"
```

## Troubleshooting

### Connection Issues
1. Verify miner IP address and network connectivity
2. Check if LuxOS web interface is accessible
3. Ensure no firewall blocking Home Assistant

### API Errors
1. Check LuxOS firmware version compatibility
2. Verify API endpoints are enabled in LuxOS
3. Check authentication credentials if required

### Performance Issues
1. Increase update interval for slower networks
2. Monitor Home Assistant system resources
3. Check miner response times

## Support

For issues and feature requests, please use the GitHub repository:
- **Issues**: Report bugs and problems
- **Feature Requests**: Suggest new features
- **Discussions**: General questions and help

## Contributing

Contributions are welcome! Please read the contributing guidelines and submit pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This integration is not officially supported by Bitmain or Luxor. Use at your own risk and always monitor your mining equipment. The developers are not responsible for any damage to equipment or loss of mining revenue.