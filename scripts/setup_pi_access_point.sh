#!/usr/bin/env bash
# Configure the Raspberry Pi 3 Wi-Fi interface as the isolated VoiceStock
# access point. Persistent NetworkManager profile voicestock-ap.
# See docs/setup/local-network.md and scripts/voicestock-network.conf.

set -euo pipefail

export LC_ALL=C

PROFILE="voicestock-ap"
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
  printf 'Usage: sudo bash scripts/setup_pi_access_point.sh [wifi-interface]\n' >&2
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
    error "Administrator permissions are required. Run: sudo bash scripts/setup_pi_access_point.sh"
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

resolve_interface() {
  local requested="${1:-}"
  local found=()
  local device

  if [[ -n "$requested" ]]; then
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
    return 0
  fi

  while IFS= read -r device; do
    if [[ -n "$device" ]]; then
      found+=("$device")
    fi
  done < <(list_wifi_devices)

  if [[ "${#found[@]}" -eq 0 ]]; then
    error "No Wi-Fi interface was found. Pass the VoiceStock interface explicitly. Refusing to configure Ethernet or any other device."
  fi
  if [[ "${#found[@]}" -gt 1 ]]; then
    error "More than one Wi-Fi interface was found (${found[*]}). Pass the access-point interface explicitly: sudo bash scripts/setup_pi_access_point.sh <interface>"
  fi

  printf '%s\n' "${found[0]}"
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

require_ap_capable() {
  local interface_name="$1"
  local reported phy

  reported="$(nmcli -g WIFI-PROPERTIES.AP device show "$interface_name" 2>/dev/null || true)"
  reported="$(printf '%s' "$reported" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
  case "$reported" in
    yes*)
      info "OK: ${interface_name} reports Access Point mode."
      return 0
      ;;
    no*)
      error "Interface ${interface_name} does not support Access Point mode."
      ;;
  esac

  phy="$(iw dev "$interface_name" info 2>/dev/null | awk '/wiphy/ { print $2; exit }')"
  if [[ -z "$phy" ]]; then
    error "Could not verify Access Point support on ${interface_name}. Refusing to guess."
  fi

  if iw phy "phy${phy}" info 2>/dev/null | awk '
    BEGIN { found = 0; inmodes = 0 }
    /Supported interface modes:/ { inmodes = 1; next }
    inmodes && /^[[:space:]]+\*/ {
      if ($2 == "AP") found = 1
      next
    }
    inmodes && !/^[[:space:]]/ { inmodes = 0 }
    END { exit(found ? 0 : 1) }
  '; then
    info "OK: ${interface_name} supports Access Point mode."
    return 0
  fi

  error "Interface ${interface_name} does not list Access Point mode. Refusing to configure it."
}

require_regulatory_domain() {
  local country
  country="$(iw reg get | awk '/^country / { print $2; exit }')"
  country="${country%%:*}"
  if [[ "$country" != "$VOICESTOCK_WIFI_REGULATORY_DOMAIN" ]]; then
    cat >&2 <<EOF
ERROR: Wi-Fi regulatory domain is '${country:-unset}', not ${VOICESTOCK_WIFI_REGULATORY_DOMAIN}.
This script does not change the system regulatory domain.
On Raspberry Pi OS, set Argentina, reboot, and run this script again:

  sudo raspi-config nonint do_wifi_country ${VOICESTOCK_WIFI_REGULATORY_DOMAIN}
  sudo reboot

Check with: iw reg get
The first country line must be ${VOICESTOCK_WIFI_REGULATORY_DOMAIN}.
See docs/setup/local-network.md.
EOF
    exit 1
  fi
  info "OK: Wi-Fi regulatory domain is ${VOICESTOCK_WIFI_REGULATORY_DOMAIN}."
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

apply_profile_settings() {
  local interface_name="$1"

  nmcli connection modify "$PROFILE" \
    connection.interface-name "$interface_name" \
    connection.autoconnect yes \
    connection.autoconnect-priority "$AUTOCONNECT_PRIORITY" \
    802-11-wireless.mode ap \
    802-11-wireless.band bg \
    802-11-wireless.ssid "$VOICESTOCK_WIFI_SSID" \
    802-11-wireless.hidden no \
    802-11-wireless-security.key-mgmt wpa-psk \
    802-11-wireless-security.proto rsn \
    802-11-wireless-security.pairwise ccmp \
    802-11-wireless-security.group ccmp \
    802-11-wireless-security.psk "$VOICESTOCK_WIFI_PSK" \
    802-11-wireless-security.psk-flags 0 \
    ipv4.method manual \
    ipv4.addresses "$VOICESTOCK_PI_ADDRESS" \
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

  nmcli connection modify "$PROFILE" ipv4.addresses "$VOICESTOCK_PI_ADDRESS"
  configured="$(configured_addresses)"
  IFS=',' read -r -a parts <<< "$configured"
  for part in "${parts[@]}"; do
    if [[ -n "$part" && "$part" != "$VOICESTOCK_PI_ADDRESS" ]]; then
      nmcli connection modify "$PROFILE" -ipv4.addresses "$part"
    fi
  done

  configured="$(configured_addresses)"
  if [[ "$configured" != "$VOICESTOCK_PI_ADDRESS" && ",${configured}," != *",${VOICESTOCK_PI_ADDRESS},"* ]]; then
    nmcli connection modify "$PROFILE" +ipv4.addresses "$VOICESTOCK_PI_ADDRESS"
  fi
}

quiesce_other_wifi_profiles() {
  local line name type autoconnect
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    type="${line##*:}"
    name="${line%:*}"
    [[ "$type" == "802-11-wireless" ]] || continue
    [[ "$name" == "$PROFILE" ]] && continue
    autoconnect="$(nmcli -g connection.autoconnect connection show "$name")"
    if [[ "$autoconnect" != "no" ]]; then
      info "Disabling autoconnect on Wi-Fi profile ${name} so the Raspberry Pi does not join another network."
      nmcli connection modify "$name" connection.autoconnect no
    fi
  done < <(nmcli -t -f NAME,TYPE connection show)
}

deactivate_other_profiles_on_interface() {
  local interface_name="$1"
  local line name device
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    device="${line##*:}"
    name="${line%:*}"
    [[ "$device" == "$interface_name" ]] || continue
    [[ "$name" == "$PROFILE" ]] && continue
    info "Deactivating ${name} on ${interface_name}. The profile is kept."
    nmcli connection down "$name" || true
  done < <(nmcli -t -f NAME,DEVICE connection show --active)
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
      802-11-wireless.mode ap \
      802-11-wireless.band bg \
      802-11-wireless-security.key-mgmt wpa-psk \
      802-11-wireless-security.proto rsn \
      802-11-wireless-security.psk "$VOICESTOCK_WIFI_PSK" \
      802-11-wireless-security.psk-flags 0 \
      ipv4.method manual \
      ipv4.addresses "$VOICESTOCK_PI_ADDRESS" \
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
  quiesce_other_wifi_profiles
  deactivate_other_profiles_on_interface "$interface_name"
  info "Activating ${PROFILE}..."
  nmcli connection up "$PROFILE"
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
  ip -4 -o addr show dev "$interface_name" | grep -Fq "inet ${VOICESTOCK_PI_ADDRESS}"
}

profile_is_active_on() {
  local interface_name="$1"
  nmcli -t -f NAME,DEVICE connection show --active | grep -Fxq "${PROFILE}:${interface_name}"
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

stored_psk_matches() {
  local stored
  stored="$(nmcli --show-secrets -g 802-11-wireless-security.psk connection show "$PROFILE")"
  stored="${stored#"${stored%%[![:space:]]*}"}"
  stored="${stored%"${stored##*[![:space:]]}"}"
  [[ "$stored" == "$VOICESTOCK_WIFI_PSK" ]]
}

verify_and_report() {
  local interface_name="$1"
  local -a failures=()
  local psk_flags

  if interface_has_address "$interface_name"; then
    info "OK: ${interface_name} has ${VOICESTOCK_PI_ADDRESS}."
  else
    printf 'FAILED: %s does not have %s.\n' "$interface_name" "$VOICESTOCK_PI_ADDRESS" >&2
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
  if property_is 802-11-wireless.mode ap \
    && property_is 802-11-wireless.band bg \
    && property_is 802-11-wireless.ssid "$VOICESTOCK_WIFI_SSID" \
    && property_is 802-11-wireless-security.key-mgmt wpa-psk \
    && property_is 802-11-wireless-security.proto rsn \
    && property_is ipv4.method manual \
    && [[ "$psk_flags" == 0* ]] \
    && stored_psk_matches; then
    info "OK: ${PROFILE} is a 2.4 GHz WPA2-PSK access point for ${VOICESTOCK_WIFI_SSID}."
  else
    printf 'FAILED: profile %s does not match the VoiceStock access-point settings.\n' "$PROFILE" >&2
    failures+=("wifi")
  fi

  if property_is ipv6.method disabled \
    && property_is connection.autoconnect yes \
    && property_is connection.autoconnect-priority "$AUTOCONNECT_PRIORITY" \
    && property_is connection.interface-name "$interface_name" \
    && [[ "$(configured_addresses)" == "$VOICESTOCK_PI_ADDRESS" ]]; then
    info "OK: profile settings match the VoiceStock access-point plan."
  else
    printf 'FAILED: profile %s does not match the required NetworkManager settings.\n' "$PROFILE" >&2
    failures+=("profile")
  fi

  if [[ "${#failures[@]}" -gt 0 ]]; then
    error "Access-point configuration is not in the required state."
  fi

  info "VoiceStock access-point profile ${PROFILE} is persistent in NetworkManager."
  info "No gateway, DNS, DHCP, NAT, or default route was added on ${interface_name}."
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi
if [[ "$#" -gt 1 ]]; then
  usage
  error "Too many arguments."
fi

load_config
require_command nmcli
require_command ip
require_command iw
require_root

INTERFACE="$(resolve_interface "${1:-}")"
require_managed "$INTERFACE"
require_ap_capable "$INTERFACE"
require_regulatory_domain
info "Using Wi-Fi interface ${INTERFACE} as the VoiceStock access point."
create_or_update_profile "$INTERFACE"
verify_and_report "$INTERFACE"
