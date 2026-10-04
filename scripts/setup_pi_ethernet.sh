#!/usr/bin/env bash
# Configure the Raspberry Pi Ethernet port for the VoiceStock local network.
# Static address 192.168.50.1/24, no gateway, no DNS, never the default route.
# The profile is persistent in NetworkManager. See docs/setup/local-network.md.

set -euo pipefail

export LC_ALL=C

PROFILE="voicestock-ethernet"
ADDRESS="192.168.50.1/24"
AUTOCONNECT_PRIORITY="100"

info() {
  printf '==> %s\n' "$1"
}

error() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 1
}

usage() {
  printf 'Usage: sudo bash scripts/setup_pi_ethernet.sh [ethernet-interface]\n' >&2
}

require_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    error "${command_name} is required but was not found."
  fi
}

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    error "Administrator permissions are required. Run: sudo bash scripts/setup_pi_ethernet.sh"
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

list_ethernet_devices() {
  nmcli -t -f DEVICE,TYPE device status | awk -F: '
    $2 == "ethernet" && $1 != "" && $1 != "--" { print $1 }
  '
}

resolve_interface() {
  local requested="${1:-}"
  local found=()
  local device

  if [[ -n "$requested" ]]; then
    valid_interface_name "$requested" || error "Invalid interface name: ${requested}"
    if ! nmcli device show "$requested" >/dev/null 2>&1; then
      error "Network interface ${requested} was not found."
    fi
    if [[ "$(device_type "$requested")" != "ethernet" ]]; then
      error "Interface ${requested} is not Ethernet. This script does not configure Wi-Fi or other interface types."
    fi
    printf '%s\n' "$requested"
    return 0
  fi

  while IFS= read -r device; do
    if [[ -n "$device" ]]; then
      found+=("$device")
    fi
  done < <(list_ethernet_devices)

  if [[ "${#found[@]}" -eq 0 ]]; then
    error "No Ethernet interface was found. Refusing to configure Wi-Fi or any other device."
  fi
  if [[ "${#found[@]}" -gt 1 ]]; then
    error "More than one Ethernet interface was found (${found[*]}). Pass the VoiceStock interface explicitly: sudo bash scripts/setup_pi_ethernet.sh <interface>"
  fi

  printf '%s\n' "${found[0]}"
}

require_managed() {
  local interface_name="$1"
  local state
  state="$(nmcli -g GENERAL.STATE device show "$interface_name")"
  case "$state" in
    10*|unmanaged*|Unmanaged*)
      error "Ethernet interface ${interface_name} is not managed by NetworkManager."
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

apply_profile_settings() {
  local interface_name="$1"

  nmcli connection modify "$PROFILE" \
    connection.interface-name "$interface_name" \
    connection.autoconnect yes \
    connection.autoconnect-priority "$AUTOCONNECT_PRIORITY" \
    ipv4.method manual \
    ipv4.addresses "$ADDRESS" \
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

  nmcli connection modify "$PROFILE" ipv4.addresses "$ADDRESS"
  configured="$(configured_addresses)"
  IFS=',' read -r -a parts <<< "$configured"
  for part in "${parts[@]}"; do
    if [[ -n "$part" && "$part" != "$ADDRESS" ]]; then
      nmcli connection modify "$PROFILE" -ipv4.addresses "$part"
    fi
  done

  configured="$(configured_addresses)"
  if [[ "$configured" != "$ADDRESS" && ",${configured}," != *",${ADDRESS},"* ]]; then
    nmcli connection modify "$PROFILE" +ipv4.addresses "$ADDRESS"
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
      type ethernet \
      ifname "$interface_name" \
      con-name "$PROFILE" \
      connection.autoconnect no \
      connection.autoconnect-priority "$AUTOCONNECT_PRIORITY" \
      ipv4.method manual \
      ipv4.addresses "$ADDRESS" \
      ipv4.never-default yes \
      ipv6.method disabled
  else
    existing_type="$(nmcli -g connection.type connection show "$PROFILE")"
    if [[ "$existing_type" != "802-3-ethernet" ]]; then
      error "Profile ${PROFILE} exists but its type is ${existing_type}, not Ethernet. This script will not change it."
    fi
    info "Updating NetworkManager profile ${PROFILE} on ${interface_name}..."
  fi

  apply_profile_settings "$interface_name"
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
  ip -4 -o addr show dev "$interface_name" | grep -Fq "inet ${ADDRESS}"
}

profile_is_active_on() {
  local interface_name="$1"
  nmcli -t -f NAME,DEVICE connection show --active | grep -Fxq "${PROFILE}:${interface_name}"
}

interface_is_not_default_route() {
  local interface_name="$1"
  local line escaped_name
  escaped_name="${interface_name//./\\.}"
  while IFS= read -r line; do
    if [[ "$line" =~ (^|[[:space:]])dev[[:space:]]+${escaped_name}($|[[:space:]]) ]]; then
      return 1
    fi
  done < <(ip -4 route show default)
  return 0
}

verify_and_report() {
  local interface_name="$1"
  local -a failures=()

  if interface_has_address "$interface_name"; then
    info "OK: ${interface_name} has ${ADDRESS}."
  else
    printf 'FAILED: %s does not have %s.\n' "$interface_name" "$ADDRESS" >&2
    failures+=("address")
  fi

  if profile_is_active_on "$interface_name"; then
    info "OK: profile ${PROFILE} is active on ${interface_name}."
  else
    printf 'FAILED: profile %s is not active on %s.\n' "$PROFILE" "$interface_name" >&2
    failures+=("active")
  fi

  if property_is ipv4.never-default yes && interface_is_not_default_route "$interface_name"; then
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

  if property_is ipv4.method manual \
    && property_is ipv6.method disabled \
    && property_is connection.autoconnect yes \
    && property_is connection.autoconnect-priority "$AUTOCONNECT_PRIORITY" \
    && property_is connection.interface-name "$interface_name" \
    && [[ "$(configured_addresses)" == "$ADDRESS" ]]; then
    info "OK: profile settings match the VoiceStock Ethernet plan."
  else
    printf 'FAILED: profile %s does not match the required NetworkManager settings.\n' "$PROFILE" >&2
    failures+=("profile")
  fi

  if [[ "${#failures[@]}" -gt 0 ]]; then
    error "Ethernet configuration is not in the required state."
  fi

  info "VoiceStock Ethernet profile ${PROFILE} is persistent in NetworkManager."
  info "Default IPv4 route was not moved onto ${interface_name}."
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi
if [[ "$#" -gt 1 ]]; then
  usage
  error "Too many arguments."
fi

require_command nmcli
require_command ip
require_root

INTERFACE="$(resolve_interface "${1:-}")"
require_managed "$INTERFACE"
info "Using Ethernet interface ${INTERFACE}."
create_or_update_profile "$INTERFACE"
verify_and_report "$INTERFACE"
