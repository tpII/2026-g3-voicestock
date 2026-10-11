#!/usr/bin/env bash
# Connect one explicit Arch Linux Wi-Fi interface to the VoiceStock access
# point. Persistent NetworkManager profile voicestock-client.
# Does not select or modify the Internet Wi-Fi interface.
# See docs/setup/local-network.md and scripts/voicestock-network.conf.

set -euo pipefail

export LC_ALL=C

PROFILE="voicestock-client"
AUTOCONNECT_PRIORITY="100"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/voicestock-network.conf"

info() {
  printf '==> %s\n' "$1"
}

error() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 1
}

usage() {
  cat >&2 <<'EOF'
Usage: sudo bash scripts/setup_pc_voicestock_wifi.sh <wifi-interface>

The interface argument is required. Identify the Internet Wi-Fi interface
first (it owns the default route), then pass the other Wi-Fi interface.
This script does not choose an interface and does not modify any other one.
EOF
}

load_config() {
  if [[ ! -f "$CONFIG_FILE" ]]; then
    error "Missing ${CONFIG_FILE}."
  fi
  # shellcheck disable=SC1090
  source "$CONFIG_FILE"

  [[ "${VOICESTOCK_WIFI_SSID:-}" == "VoiceStock" ]] \
    || error "VOICESTOCK_WIFI_SSID in voicestock-network.conf must be VoiceStock."
  [[ "${VOICESTOCK_PI_ADDRESS:-}" == "192.168.50.1/24" ]] \
    || error "VOICESTOCK_PI_ADDRESS in voicestock-network.conf must be 192.168.50.1/24."
  [[ "${VOICESTOCK_PC_ADDRESS:-}" == "192.168.50.2/24" ]] \
    || error "VOICESTOCK_PC_ADDRESS in voicestock-network.conf must be 192.168.50.2/24."
  [[ "${VOICESTOCK_WIFI_SUBNET:-}" == "192.168.50.0/24" ]] \
    || error "VOICESTOCK_WIFI_SUBNET in voicestock-network.conf must be 192.168.50.0/24."
  [[ "${VOICESTOCK_WIFI_REGULATORY_DOMAIN:-}" == "AR" ]] \
    || error "VOICESTOCK_WIFI_REGULATORY_DOMAIN in voicestock-network.conf must be AR."

  local length="${#VOICESTOCK_WIFI_PSK}"
  if ((length < 8 || length > 63)); then
    error "The prototype Wi-Fi password must be 8 to 63 characters."
  fi
  if [[ "$VOICESTOCK_WIFI_PSK" == *$'\n'* ]]; then
    error "The prototype Wi-Fi password must be a single line."
  fi
}

require_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    error "${command_name} is required but was not found."
  fi
}

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    error "Administrator permissions are required. Run: sudo bash scripts/setup_pc_voicestock_wifi.sh <wifi-interface>"
  fi
}

valid_interface_name() {
  local interface_name="$1"
  [[ "$interface_name" =~ ^[A-Za-z0-9._-]+$ ]]
}

device_type() {
  local interface_name="$1"
  nmcli -g GENERAL.TYPE device show "$interface_name" 2>/dev/null || true
}

list_wifi_devices() {
  nmcli -t -f DEVICE,TYPE device status | awk -F: '
    $2 == "wifi" && $1 != "" && $1 != "--" { print $1 }
  '
}

require_two_wifi_interfaces() {
  local found=()
  local device
  while IFS= read -r device; do
    if [[ -n "$device" ]]; then
      found+=("$device")
    fi
  done < <(list_wifi_devices)

  if [[ "${#found[@]}" -lt 2 ]]; then
    error "Expected at least two Wi-Fi interfaces (Internet and VoiceStock). Found: ${found[*]:-none}. Refusing to modify the only Wi-Fi interface."
  fi
}

interface_has_default_route() {
  local interface_name="$1"
  local line escaped_name
  escaped_name="${interface_name//./\\.}"
  while IFS= read -r line; do
    if [[ "$line" =~ (^|[[:space:]])dev[[:space:]]+${escaped_name}($|[[:space:]]) ]]; then
      return 0
    fi
  done < <(ip -4 route show default)
  return 1
}

require_not_internet_interface() {
  local interface_name="$1"
  local active gateway
  active="$(nmcli -t -f NAME,DEVICE connection show --active | awk -F: -v dev="$interface_name" '$2 == dev { print $1; exit }')"
  if [[ "$active" == "$PROFILE" ]]; then
    info "Profile ${PROFILE} is already active on ${interface_name}. Updating it in place."
    return 0
  fi
  if interface_has_default_route "$interface_name"; then
    error "Interface ${interface_name} owns the default IPv4 route. That is the Internet path. Pass the other Wi-Fi interface. Nothing was changed."
  fi
  gateway="$(nmcli -g IP4.GATEWAY device show "$interface_name")"
  if [[ -n "$gateway" && "$gateway" != "--" && "$gateway" != "0.0.0.0" ]]; then
    error "Interface ${interface_name} has IPv4 gateway ${gateway}. That looks like the Internet path. Pass the other Wi-Fi interface. Nothing was changed."
  fi
}

resolve_interface() {
  local requested="$1"
  valid_interface_name "$requested" || error "Invalid interface name: ${requested}"
  if [[ ! -d "/sys/class/net/${requested}" ]]; then
    error "Network interface ${requested} does not exist."
  fi
  if ! nmcli device show "$requested" >/dev/null 2>&1; then
    error "Network interface ${requested} is not known to NetworkManager."
  fi
  if [[ "$(device_type "$requested")" != "wifi" ]]; then
    error "Interface ${requested} is not Wi-Fi. This script does not configure Ethernet or other interface types."
  fi
  printf '%s\n' "$requested"
}

require_managed() {
  local interface_name="$1"
  local state
  state="$(nmcli -g GENERAL.STATE device show "$interface_name")"
  case "$state" in
    10* | unmanaged* | Unmanaged*)
      error "Wi-Fi interface ${interface_name} is not managed by NetworkManager."
      ;;
  esac
}

profile_count() {
  nmcli -t -f NAME connection show | grep -F -x -c "$PROFILE" || true
}

require_single_profile_if_present() {
  local count
  count="$(profile_count)"
  if [[ "$count" -gt 1 ]]; then
    error "More than one NetworkManager profile is named ${PROFILE}. Remove the extras so this script can update a single profile."
  fi
}

interface_mac() {
  local interface_name="$1"
  local mac
  mac="$(tr '[:upper:]' '[:lower:]' < "/sys/class/net/${interface_name}/address")"
  mac="${mac//$'\n'/}"
  if [[ ! "$mac" =~ ^([0-9a-f]{2}:){5}[0-9a-f]{2}$ ]]; then
    error "Could not read a Wi-Fi MAC address for ${interface_name}."
  fi
  printf '%s\n' "$mac"
}

apply_profile_settings() {
  local interface_name="$1"
  local mac
  mac="$(interface_mac "$interface_name")"

  nmcli connection modify "$PROFILE" \
    connection.interface-name "$interface_name" \
    connection.autoconnect yes \
    connection.autoconnect-priority "$AUTOCONNECT_PRIORITY" \
    802-11-wireless.mode infrastructure \
    802-11-wireless.band bg \
    802-11-wireless.ssid "$VOICESTOCK_WIFI_SSID" \
    802-11-wireless.mac-address "$mac" \
    802-11-wireless-security.key-mgmt wpa-psk \
    802-11-wireless-security.proto rsn \
    802-11-wireless-security.pairwise ccmp \
    802-11-wireless-security.group ccmp \
    802-11-wireless-security.psk "$VOICESTOCK_WIFI_PSK" \
    802-11-wireless-security.psk-flags 0 \
    ipv4.method manual \
    ipv4.addresses "$VOICESTOCK_PC_ADDRESS" \
    ipv4.never-default yes \
    ipv6.method disabled

  clear_gateways_and_dns
  remove_extra_addresses
}

clear_gateways_and_dns() {
  local gateway dns normalized server
  local -a servers

  gateway="$(nmcli -g ipv4.gateway connection show "$PROFILE")"
  if [[ -n "$gateway" && "$gateway" != "--" ]]; then
    if ! nmcli connection modify "$PROFILE" ipv4.gateway ""; then
      nmcli connection modify "$PROFILE" -ipv4.gateway "$gateway"
    fi
  fi

  dns="$(nmcli -g ipv4.dns connection show "$PROFILE")"
  if [[ -n "$dns" && "$dns" != "--" ]]; then
    nmcli connection modify "$PROFILE" ipv4.dns "" || true
    dns="$(nmcli -g ipv4.dns connection show "$PROFILE")"
    if [[ -n "$dns" && "$dns" != "--" ]]; then
      normalized="${dns// /}"
      IFS=',' read -r -a servers <<< "$normalized"
      for server in "${servers[@]}"; do
        if [[ -n "$server" ]]; then
          nmcli connection modify "$PROFILE" -ipv4.dns "$server"
        fi
      done
    fi
  fi
}

configured_addresses() {
  local configured
  configured="$(nmcli -g ipv4.addresses connection show "$PROFILE")"
  configured="${configured//$'\n'/,}"
  configured="${configured// /}"
  printf '%s' "$configured"
}

remove_extra_addresses() {
  local configured part
  local -a parts

  nmcli connection modify "$PROFILE" ipv4.addresses "$VOICESTOCK_PC_ADDRESS"
  configured="$(configured_addresses)"
  IFS=',' read -r -a parts <<< "$configured"
  for part in "${parts[@]}"; do
    if [[ -n "$part" && "$part" != "$VOICESTOCK_PC_ADDRESS" ]]; then
      nmcli connection modify "$PROFILE" -ipv4.addresses "$part"
    fi
  done

  configured="$(configured_addresses)"
  if [[ "$configured" != "$VOICESTOCK_PC_ADDRESS" && ",${configured}," != *",${VOICESTOCK_PC_ADDRESS},"* ]]; then
    nmcli connection modify "$PROFILE" +ipv4.addresses "$VOICESTOCK_PC_ADDRESS"
  fi
}

create_or_update_profile() {
  local interface_name="$1"
  local count existing_type

  require_single_profile_if_present
  count="$(profile_count)"

  if [[ "$count" -eq 0 ]]; then
    info "Creating NetworkManager profile ${PROFILE} on ${interface_name}..."
    nmcli connection add \
      type wifi \
      ifname "$interface_name" \
      con-name "$PROFILE" \
      connection.autoconnect no \
      connection.autoconnect-priority "$AUTOCONNECT_PRIORITY" \
      ssid "$VOICESTOCK_WIFI_SSID" \
      802-11-wireless.mode infrastructure \
      802-11-wireless.band bg \
      802-11-wireless.mac-address "$(interface_mac "$interface_name")" \
      802-11-wireless-security.key-mgmt wpa-psk \
      802-11-wireless-security.proto rsn \
      802-11-wireless-security.psk "$VOICESTOCK_WIFI_PSK" \
      802-11-wireless-security.psk-flags 0 \
      ipv4.method manual \
      ipv4.addresses "$VOICESTOCK_PC_ADDRESS" \
      ipv4.never-default yes \
      ipv6.method disabled
  else
    existing_type="$(nmcli -g connection.type connection show "$PROFILE")"
    if [[ "$existing_type" != "802-11-wireless" ]]; then
      error "Profile ${PROFILE} exists but its type is ${existing_type}, not Wi-Fi. This script will not change it."
    fi
    info "Updating NetworkManager profile ${PROFILE} on ${interface_name}..."
  fi

  apply_profile_settings "$interface_name"
  info "Activating ${PROFILE} on ${interface_name} only..."
  nmcli connection up "$PROFILE" ifname "$interface_name"
}

property_is() {
  local property="$1"
  local expected="$2"
  local actual
  actual="$(nmcli -g "$property" connection show "$PROFILE")"
  actual="${actual#"${actual%%[![:space:]]*}"}"
  actual="${actual%"${actual##*[![:space:]]}"}"
  [[ "$actual" == "$expected" ]]
}

property_is_empty() {
  local property="$1"
  local actual
  actual="$(nmcli -g "$property" connection show "$PROFILE")"
  [[ -z "$actual" || "$actual" == "--" ]]
}

device_property_is_empty() {
  local property="$1"
  local interface_name="$2"
  local actual
  actual="$(nmcli -g "$property" device show "$interface_name" 2>/dev/null || true)"
  [[ -z "$actual" || "$actual" == "--" ]]
}

interface_has_address() {
  local interface_name="$1"
  ip -4 -o addr show dev "$interface_name" | grep -Fq "inet ${VOICESTOCK_PC_ADDRESS}"
}

profile_is_active_on() {
  local interface_name="$1"
  nmcli -t -f NAME,DEVICE connection show --active | grep -Fxq "${PROFILE}:${interface_name}"
}

stored_psk_matches() {
  local stored
  stored="$(nmcli --show-secrets -g 802-11-wireless-security.psk connection show "$PROFILE")"
  stored="${stored#"${stored%%[![:space:]]*}"}"
  stored="${stored%"${stored##*[![:space:]]}"}"
  [[ "$stored" == "$VOICESTOCK_WIFI_PSK" ]]
}

mac_matches() {
  local interface_name="$1"
  local actual expected
  actual="$(nmcli -g 802-11-wireless.mac-address connection show "$PROFILE" | tr '[:upper:]' '[:lower:]')"
  actual="${actual// /}"
  expected="$(interface_mac "$interface_name")"
  [[ "$actual" == "$expected" ]]
}

verify_and_report() {
  local interface_name="$1"
  local -a failures=()
  local psk_flags

  if interface_has_address "$interface_name"; then
    info "OK: ${interface_name} has ${VOICESTOCK_PC_ADDRESS}."
  else
    printf 'FAILED: %s does not have %s.\n' "$interface_name" "$VOICESTOCK_PC_ADDRESS" >&2
    failures+=("address")
  fi

  if profile_is_active_on "$interface_name"; then
    info "OK: profile ${PROFILE} is active on ${interface_name}."
  else
    printf 'FAILED: profile %s is not active on %s.\n' "$PROFILE" "$interface_name" >&2
    failures+=("active")
  fi

  if property_is ipv4.never-default yes && ! interface_has_default_route "$interface_name"; then
    info "OK: ${PROFILE} is not the default IPv4 route."
  else
    printf 'FAILED: %s is, or could become, the default IPv4 route.\n' "$PROFILE" >&2
    failures+=("default-route")
  fi

  if property_is_empty ipv4.gateway && device_property_is_empty IP4.GATEWAY "$interface_name"; then
    info "OK: no IPv4 gateway on ${PROFILE}."
  else
    printf 'FAILED: an IPv4 gateway is set on %s.\n' "$PROFILE" >&2
    failures+=("gateway")
  fi

  if property_is_empty ipv4.dns && device_property_is_empty IP4.DNS "$interface_name"; then
    info "OK: no IPv4 DNS on ${PROFILE}."
  else
    printf 'FAILED: an IPv4 DNS server is set on %s.\n' "$PROFILE" >&2
    failures+=("dns")
  fi

  psk_flags="$(nmcli -g 802-11-wireless-security.psk-flags connection show "$PROFILE")"
  if property_is 802-11-wireless.mode infrastructure \
    && property_is 802-11-wireless.band bg \
    && property_is 802-11-wireless.ssid "$VOICESTOCK_WIFI_SSID" \
    && property_is 802-11-wireless-security.key-mgmt wpa-psk \
    && property_is 802-11-wireless-security.proto rsn \
    && property_is ipv4.method manual \
    && property_is connection.interface-name "$interface_name" \
    && mac_matches "$interface_name" \
    && [[ "$psk_flags" == 0* ]] \
    && stored_psk_matches; then
    info "OK: ${PROFILE} is a 2.4 GHz WPA2-PSK client for ${VOICESTOCK_WIFI_SSID} on ${interface_name}."
  else
    printf 'FAILED: profile %s does not match the VoiceStock client settings.\n' "$PROFILE" >&2
    failures+=("wifi")
  fi

  if property_is ipv6.method disabled \
    && property_is connection.autoconnect yes \
    && property_is connection.autoconnect-priority "$AUTOCONNECT_PRIORITY" \
    && [[ "$(configured_addresses)" == "$VOICESTOCK_PC_ADDRESS" ]]; then
    info "OK: profile settings match the VoiceStock client plan."
  else
    printf 'FAILED: profile %s does not match the required NetworkManager settings.\n' "$PROFILE" >&2
    failures+=("profile")
  fi

  if [[ "${#failures[@]}" -gt 0 ]]; then
    error "VoiceStock Wi-Fi configuration is not in the required state."
  fi

  info "VoiceStock client profile ${PROFILE} is persistent in NetworkManager."
  info "No gateway, DNS, or default route was added on ${interface_name}."
  info "Other Wi-Fi interfaces were not modified. Confirm the default route is still the Internet interface: ip -4 route"
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi
if [[ "$#" -ne 1 ]]; then
  usage
  error "The VoiceStock Wi-Fi interface is required. This script does not choose one."
fi

load_config
require_command nmcli
require_command ip
require_root

require_two_wifi_interfaces
INTERFACE="$(resolve_interface "$1")"
require_managed "$INTERFACE"
require_not_internet_interface "$INTERFACE"
info "Using Wi-Fi interface ${INTERFACE} for VoiceStock only."
create_or_update_profile "$INTERFACE"
verify_and_report "$INTERFACE"
