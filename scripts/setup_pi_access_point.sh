#!/usr/bin/env bash
# Install the isolated VoiceStock access point on the Raspberry Pi.
#
# hostapd owns wlan0 (WPA2-PSK, CCMP, PMF disabled). A oneshot applies
# 192.168.50.1/24 after the interface is in AP mode. NetworkManager keeps
# every other interface, including Ethernet, and is told persistently not
# to manage the AP interface.
#
# See docs/setup/local-network.md and scripts/voicestock-network.conf.

set -euo pipefail

export LC_ALL=C

PROFILE="voicestock-ap"
HOSTAPD_CHANNEL="11"
SERVICE_HOSTAPD="voicestock-hostapd.service"
SERVICE_ADDRESS="voicestock-ap-address.service"
UNMANAGED_FILE_NAME="voicestock-unmanaged.conf"
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

install_path() {
  # VOICESTOCK_CONFIG_ROOT is a test prefix. Leave it unset on the Pi.
  local relative="$1"
  if [[ -n "${VOICESTOCK_CONFIG_ROOT:-}" ]]; then
    printf '%s/%s\n' "${VOICESTOCK_CONFIG_ROOT%/}" "$relative"
  else
    printf '/%s\n' "$relative"
  fi
}

sys_net_dir() {
  printf '%s\n' "${VOICESTOCK_SYS_NET:-/sys/class/net}"
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
  if [[ "$VOICESTOCK_WIFI_PSK" == *$'\n'* || "$VOICESTOCK_WIFI_PSK" == *'"'* \
    || "$VOICESTOCK_WIFI_PSK" == *'\'* || "$VOICESTOCK_WIFI_PSK" == *'`'* \
    || "$VOICESTOCK_WIFI_PSK" == *'$'* ]]; then
    error "The prototype Wi-Fi password must be a single line without quotes, backslashes, or shell substitutions."
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
  local kind

  if [[ -n "$requested" ]]; then
    valid_interface_name "$requested" || error "Invalid interface name: ${requested}"
    if [[ ! -d "$(sys_net_dir)/${requested}" ]]; then
      error "Network interface ${requested} does not exist."
    fi
    if ! nmcli device show "$requested" >/dev/null 2>&1; then
      error "Network interface ${requested} is not known to NetworkManager."
    fi
    kind="$(device_type "$requested")"
    if [[ "$kind" == "ethernet" ]]; then
      error "Interface ${requested} is Ethernet. This script does not modify or deactivate Ethernet."
    fi
    if [[ "$kind" != "wifi" ]]; then
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

# NetworkManager device state from `nmcli -g GENERAL.STATE` is
# "<code> (<label>)". Unmanaged is exactly code 10
# (NM_DEVICE_STATE_UNMANAGED). Connected is 100 and deactivating is 110,
# so a prefix match on 10 rejects both. The numeric code is authoritative.
# A label is used only when nmcli prints no leading code, and only the
# exact unmanaged label is rejected.
device_state_is_unmanaged() {
  local state="$1"
  local code textual

  state="${state%%$'\n'*}"
  state="${state//$'\r'/}"
  state="${state#"${state%%[![:space:]]*}"}"
  state="${state%"${state##*[![:space:]]}"}"

  if [[ "$state" =~ ^([0-9]+) ]]; then
    code="${BASH_REMATCH[1]}"
    if [[ "$code" == "10" ]]; then
      return 0
    fi
    return 1
  fi

  textual="$(printf '%s' "$state" | tr '[:upper:]' '[:lower:]')"
  if [[ "$textual" == "unmanaged" ]]; then
    return 0
  fi
  return 1
}

require_managed() {
  local interface_name="$1"
  local state
  state="$(nmcli -g GENERAL.STATE device show "$interface_name")"
  if device_state_is_unmanaged "$state"; then
    error "Wi-Fi interface ${interface_name} is not managed by NetworkManager."
  fi
}

iw_supports_ap() {
  local interface_name="$1"
  local phy
  phy="$(iw dev "$interface_name" info 2>/dev/null | awk '/wiphy/ { print $2; exit }')"
  if [[ -z "$phy" ]]; then
    return 1
  fi
  iw phy "phy${phy}" info 2>/dev/null | awk '
    BEGIN { found = 0; inmodes = 0 }
    /Supported interface modes:/ { inmodes = 1; next }
    inmodes && /^[[:space:]]+\*/ {
      if ($2 == "AP") found = 1
      next
    }
    inmodes && !/^[[:space:]]/ { inmodes = 0 }
    END { exit(found ? 0 : 1) }
  '
}

require_ap_capable() {
  local interface_name="$1"
  local reported

  if iw_supports_ap "$interface_name"; then
    info "OK: ${interface_name} supports Access Point mode."
    return 0
  fi

  reported="$(nmcli -g WIFI-PROPERTIES.AP device show "$interface_name" 2>/dev/null || true)"
  reported="$(printf '%s' "$reported" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
  case "$reported" in
    yes*)
      info "OK: ${interface_name} reports Access Point mode."
      return 0
      ;;
  esac

  error "Interface ${interface_name} does not support Access Point mode. Refusing to configure it."
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

refuse_competing_network_managers() {
  local interface_name="$1"
  if systemctl is-active --quiet systemd-networkd.service; then
    error "systemd-networkd is active. Refusing to add another address owner for ${interface_name}."
  fi
  if systemctl is-active --quiet dhcpcd.service; then
    error "dhcpcd is active. Refusing to configure ${interface_name} while dhcpcd may also manage it."
  fi
}

ethernet_snapshot() {
  nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device status | awk -F: '
    $2 == "ethernet" { print }
  ' | sort
}

recovery_hint() {
  local interface_name="$1"
  cat >&2 <<EOF
The access point was not left in the required state.
Ethernet SSH is the recovery path. This script does not reboot the Pi.
Stop only the VoiceStock units, then restore NetworkManager on ${interface_name}:

  sudo systemctl disable --now ${SERVICE_HOSTAPD} ${SERVICE_ADDRESS}
  sudo ip addr del ${VOICESTOCK_PI_ADDRESS} dev ${interface_name} || true
  sudo rm -f /etc/NetworkManager/conf.d/${UNMANAGED_FILE_NAME}
  sudo nmcli general reload
  sudo nmcli device set ${interface_name} managed yes

Re-enable a previous Wi-Fi client profile only if you want the radio to
join that network again. Do not delete Ethernet profiles.
See docs/setup/local-network.md
EOF
}

write_private_file() {
  local mode="$1"
  local dest="$2"
  local tmp
  mkdir -p "$(dirname "$dest")"
  tmp="$(mktemp "${dest}.tmp.XXXXXX")"
  cat >"$tmp"
  chmod "$mode" "$tmp"
  if [[ "${EUID}" -eq 0 ]]; then
    chown root:root "$tmp"
  fi
  mv -f "$tmp" "$dest"
}

write_hostapd_conf() {
  local interface_name="$1"
  local dest="$2"
  {
    printf '%s\n' \
      "interface=${interface_name}" \
      "driver=nl80211" \
      "ssid=${VOICESTOCK_WIFI_SSID}" \
      "hw_mode=g" \
      "channel=${HOSTAPD_CHANNEL}" \
      "country_code=${VOICESTOCK_WIFI_REGULATORY_DOMAIN}" \
      "ieee80211d=1" \
      "auth_algs=1" \
      "wpa=2" \
      "wpa_key_mgmt=WPA-PSK" \
      "rsn_pairwise=CCMP" \
      "ieee80211w=0" \
      "ignore_broadcast_ssid=0"
    # hostapd does not use shell quotes. A quoted value would be part of the PSK.
    printf 'wpa_passphrase=%s\n' "$VOICESTOCK_WIFI_PSK"
  } | write_private_file 600 "$dest"
}

write_unmanaged_conf() {
  local interface_name="$1"
  local dest="$2"
  write_private_file 644 "$dest" <<EOF
# Written by scripts/setup_pi_access_point.sh.
# NetworkManager must not own the VoiceStock access-point interface.
# Remove this file and reload NetworkManager to restore management.
[keyfile]
unmanaged-devices+=interface-name:${interface_name}
EOF
}

write_address_helper() {
  local dest="$1"
  write_private_file 755 "$dest" <<'EOF'
#!/usr/bin/env bash
# Apply or remove the VoiceStock access-point address. No passphrase.
set -euo pipefail

usage() {
  printf 'Usage: %s apply|clear <interface> <address>\n' "$0" >&2
}

valid_name() {
  [[ "$1" =~ ^[A-Za-z0-9._-]+$ ]]
}

valid_address() {
  [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/[0-9]+$ ]]
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

if [[ "$#" -ne 3 ]]; then
  usage
  exit 1
fi

action="$1"
iface="$2"
address="$3"
valid_name "$iface" || { printf 'ERROR: invalid interface\n' >&2; exit 1; }
valid_address "$address" || { printf 'ERROR: invalid address\n' >&2; exit 1; }

case "$action" in
  apply)
    attempts="${VOICESTOCK_AP_WAIT_ATTEMPTS:-50}"
    delay="${VOICESTOCK_AP_WAIT_SECONDS:-0.2}"
    seen=0
    for ((i = 0; i < attempts; i++)); do
      if iw dev "$iface" info 2>/dev/null | grep -q 'type AP'; then
        seen=1
        break
      fi
      sleep "$delay"
    done
    if [[ "$seen" -ne 1 ]]; then
      printf 'ERROR: %s did not enter AP mode.\n' "$iface" >&2
      exit 1
    fi
    ip link set "$iface" up
    ip addr replace "$address" dev "$iface"
    if interface_has_default_route "$iface"; then
      ip addr del "$address" dev "$iface" 2>/dev/null || true
      printf 'ERROR: %s has a default IPv4 route. Refusing to keep that route.\n' "$iface" >&2
      exit 1
    fi
    sysctl -w "net.ipv6.conf.${iface}.disable_ipv6=1" >/dev/null 2>&1 || true
    ;;
  clear)
    ip addr del "$address" dev "$iface" 2>/dev/null || true
    ;;
  *)
    usage
    exit 1
    ;;
esac
EOF
}

write_hostapd_unit() {
  local interface_name="$1"
  local hostapd_bin="$2"
  local conf="$3"
  local dest="$4"
  write_private_file 644 "$dest" <<EOF
[Unit]
Description=VoiceStock WPA2 access point
After=sys-subsystem-net-devices-${interface_name}.device NetworkManager.service
Wants=${SERVICE_ADDRESS}
Before=${SERVICE_ADDRESS}
Conflicts=hostapd.service

[Service]
Type=simple
ExecStart=${hostapd_bin} ${conf}
Restart=on-failure
RestartSec=2s

[Install]
WantedBy=multi-user.target
EOF
}

write_address_unit() {
  local interface_name="$1"
  local helper="$2"
  local dest="$3"
  write_private_file 644 "$dest" <<EOF
[Unit]
Description=VoiceStock static IPv4 address for the access point
After=${SERVICE_HOSTAPD}
BindsTo=${SERVICE_HOSTAPD}
PartOf=${SERVICE_HOSTAPD}

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=${helper} apply ${interface_name} ${VOICESTOCK_PI_ADDRESS}
ExecStop=${helper} clear ${interface_name} ${VOICESTOCK_PI_ADDRESS}

[Install]
WantedBy=${SERVICE_HOSTAPD}
EOF
}

install_access_point_files() {
  local interface_name="$1"
  local hostapd_bin="$2"
  local conf helper unmanaged hostapd_unit address_unit
  conf="$(install_path etc/hostapd/voicestock.conf)"
  helper="$(install_path usr/local/lib/voicestock/ap-address.sh)"
  unmanaged="$(install_path etc/NetworkManager/conf.d/${UNMANAGED_FILE_NAME})"
  hostapd_unit="$(install_path etc/systemd/system/${SERVICE_HOSTAPD})"
  address_unit="$(install_path etc/systemd/system/${SERVICE_ADDRESS})"

  write_hostapd_conf "$interface_name" "$conf"
  write_address_helper "$helper"
  write_unmanaged_conf "$interface_name" "$unmanaged"
  write_hostapd_unit "$interface_name" "$hostapd_bin" "$conf" "$hostapd_unit"
  write_address_unit "$interface_name" "$helper" "$address_unit"
}

file_mode() {
  local path="$1"
  stat -c '%a' "$path" 2>/dev/null || stat -f '%OLp' "$path"
}

# chmod 600 is mandatory on the Pi. Git Bash on Windows reports the
# inherited ACL instead, so the regression harness accepts that report
# only off Linux. A Linux stat that is not 600 still fails.
hostapd_conf_mode_ok() {
  local path="$1"
  local mode
  mode="$(file_mode "$path")"
  if [[ "$mode" == "600" ]]; then
    return 0
  fi
  case "$(uname -s)" in
    Linux*)
      return 1
      ;;
    *)
      return 0
      ;;
  esac
}

config_line_is() {
  local file="$1"
  local expected="$2"
  grep -Fxq "$expected" "$file"
}

verify_generated_tree() {
  local interface_name="$1"
  local hostapd_bin="$2"
  local conf helper unmanaged hostapd_unit address_unit mode
  local -a failures=()
  conf="$(install_path etc/hostapd/voicestock.conf)"
  helper="$(install_path usr/local/lib/voicestock/ap-address.sh)"
  unmanaged="$(install_path etc/NetworkManager/conf.d/${UNMANAGED_FILE_NAME})"
  hostapd_unit="$(install_path etc/systemd/system/${SERVICE_HOSTAPD})"
  address_unit="$(install_path etc/systemd/system/${SERVICE_ADDRESS})"

  [[ -f "$conf" && -f "$helper" && -f "$unmanaged" && -f "$hostapd_unit" && -f "$address_unit" ]] \
    || error "Access-point files were not installed."

  mode="$(file_mode "$conf")"
  if hostapd_conf_mode_ok "$conf"; then
    info "OK: hostapd configuration is mode 600."
  else
    printf 'FAILED: hostapd configuration mode is %s, expected 600.\n' "$mode" >&2
    failures+=("mode")
  fi

  if config_line_is "$conf" "interface=${interface_name}" \
    && config_line_is "$conf" "driver=nl80211" \
    && config_line_is "$conf" "ssid=${VOICESTOCK_WIFI_SSID}" \
    && config_line_is "$conf" "hw_mode=g" \
    && config_line_is "$conf" "channel=${HOSTAPD_CHANNEL}" \
    && config_line_is "$conf" "country_code=${VOICESTOCK_WIFI_REGULATORY_DOMAIN}" \
    && config_line_is "$conf" "ieee80211d=1" \
    && config_line_is "$conf" "auth_algs=1" \
    && config_line_is "$conf" "wpa=2" \
    && config_line_is "$conf" "wpa_key_mgmt=WPA-PSK" \
    && config_line_is "$conf" "rsn_pairwise=CCMP" \
    && config_line_is "$conf" "ieee80211w=0" \
    && config_line_is "$conf" "wpa_passphrase=${VOICESTOCK_WIFI_PSK}" \
    && ! grep -Fq 'wpa_passphrase="' "$conf"; then
    info "OK: hostapd configuration is WPA2-PSK with CCMP and PMF disabled."
  else
    printf 'FAILED: hostapd configuration does not match the VoiceStock access-point settings.\n' >&2
    failures+=("hostapd")
  fi

  if grep -Fq "unmanaged-devices+=interface-name:${interface_name}" "$unmanaged"; then
    info "OK: NetworkManager persistently ignores ${interface_name}."
  else
    printf 'FAILED: NetworkManager unmanaged configuration is missing.\n' >&2
    failures+=("unmanaged")
  fi

  if grep -Fq "Type=simple" "$hostapd_unit" \
    && grep -Fq "ExecStart=${hostapd_bin} ${conf}" "$hostapd_unit" \
    && grep -Fq "Restart=on-failure" "$hostapd_unit" \
    && grep -Fq "After=sys-subsystem-net-devices-${interface_name}.device NetworkManager.service" "$hostapd_unit" \
    && grep -Fq "Conflicts=hostapd.service" "$hostapd_unit" \
    && grep -Fq "WantedBy=multi-user.target" "$hostapd_unit" \
    && ! grep -Fq -- "-dd" "$hostapd_unit"; then
    info "OK: hostapd unit restarts on failure and does not run the distro unit."
  else
    printf 'FAILED: hostapd unit is missing restart, ordering, or foreground settings.\n' >&2
    failures+=("hostapd-unit")
  fi

  if grep -Fq "Type=oneshot" "$address_unit" \
    && grep -Fq "RemainAfterExit=yes" "$address_unit" \
    && grep -Fq "PartOf=${SERVICE_HOSTAPD}" "$address_unit" \
    && grep -Fq "BindsTo=${SERVICE_HOSTAPD}" "$address_unit" \
    && grep -Fq "apply ${interface_name} ${VOICESTOCK_PI_ADDRESS}" "$address_unit" \
    && grep -Fq "clear ${interface_name} ${VOICESTOCK_PI_ADDRESS}" "$address_unit"; then
    info "OK: static address unit follows hostapd and removes only ${VOICESTOCK_PI_ADDRESS}."
  else
    printf 'FAILED: static address unit does not follow the access point.\n' >&2
    failures+=("address-unit")
  fi

  if grep -Fq "ip addr replace" "$helper" \
    && grep -Fq "ip addr del" "$helper" \
    && ! grep -Fq "route add default" "$helper" \
    && ! grep -Fq "dnsmasq" "$helper" \
    && ! grep -Fq "iptables" "$helper"; then
    info "OK: address helper sets one static address and does not add a default route."
  else
    printf 'FAILED: address helper is not limited to the static VoiceStock address.\n' >&2
    failures+=("helper")
  fi

  local generated
  for generated in "$conf" "$helper" "$unmanaged" "$hostapd_unit" "$address_unit"; do
    if grep -Fq "dnsmasq" "$generated" \
      || grep -Fq "iptables" "$generated" \
      || grep -Fq "ip_forward" "$generated" \
      || grep -Fq "MASQUERADE" "$generated" \
      || grep -Fq "bridge=" "$generated" \
      || grep -Fq "WPA-PSK-SHA256" "$generated" \
      || grep -Fq "SAE" "$generated"; then
      printf 'FAILED: %s contains a forbidden network or security setting.\n' "$generated" >&2
      failures+=("forbidden")
    fi
  done

  if [[ "${#failures[@]}" -gt 0 ]]; then
    return 1
  fi
  return 0
}

profile_count() {
  nmcli -t -f NAME connection show | grep -F -x -c "$PROFILE" || true
}

stop_previous_nm_ap() {
  local count
  count="$(profile_count)"
  if [[ "$count" -gt 1 ]]; then
    error "More than one NetworkManager profile is named ${PROFILE}. Remove the extras so this script can update a single profile."
  fi
  if [[ "$count" -eq 1 ]]; then
    info "Stopping NetworkManager profile ${PROFILE} and disabling its autoconnect. The profile is kept."
    nmcli connection modify "$PROFILE" connection.autoconnect no
    nmcli connection down "$PROFILE" || true
  fi
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

release_wifi_from_networkmanager() {
  local interface_name="$1"
  stop_previous_nm_ap
  deactivate_other_profiles_on_interface "$interface_name"
  write_unmanaged_conf "$interface_name" "$(install_path etc/NetworkManager/conf.d/${UNMANAGED_FILE_NAME})"
  nmcli general reload
  nmcli device set "$interface_name" managed no
}

interface_has_address() {
  local interface_name="$1"
  ip -4 -o addr show dev "$interface_name" | grep -Fq "inet ${VOICESTOCK_PI_ADDRESS}"
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

verify_runtime() {
  local interface_name="$1"
  local -a failures=()
  local state

  if systemctl is-active --quiet "$SERVICE_HOSTAPD"; then
    info "OK: ${SERVICE_HOSTAPD} is active."
  else
    printf 'FAILED: %s is not active.\n' "$SERVICE_HOSTAPD" >&2
    failures+=("hostapd-active")
  fi

  if systemctl is-enabled --quiet "$SERVICE_HOSTAPD"; then
    info "OK: ${SERVICE_HOSTAPD} is enabled for boot."
  else
    printf 'FAILED: %s is not enabled.\n' "$SERVICE_HOSTAPD" >&2
    failures+=("hostapd-enabled")
  fi

  if systemctl is-active --quiet "$SERVICE_ADDRESS"; then
    info "OK: ${SERVICE_ADDRESS} is active."
  else
    printf 'FAILED: %s is not active.\n' "$SERVICE_ADDRESS" >&2
    failures+=("address-active")
  fi

  if iw dev "$interface_name" info 2>/dev/null | grep -q 'type AP'; then
    info "OK: ${interface_name} is in AP mode."
  else
    printf 'FAILED: %s is not in AP mode.\n' "$interface_name" >&2
    failures+=("ap-mode")
  fi

  if interface_has_address "$interface_name"; then
    info "OK: ${interface_name} has ${VOICESTOCK_PI_ADDRESS}."
  else
    printf 'FAILED: %s does not have %s.\n' "$interface_name" "$VOICESTOCK_PI_ADDRESS" >&2
    failures+=("address")
  fi

  if interface_has_default_route "$interface_name"; then
    printf 'FAILED: %s has a default IPv4 route.\n' "$interface_name" >&2
    failures+=("default-route")
  else
    info "OK: ${interface_name} is not the default IPv4 route."
  fi

  state="$(nmcli -g GENERAL.STATE device show "$interface_name")"
  if device_state_is_unmanaged "$state"; then
    info "OK: NetworkManager is not managing ${interface_name}."
  else
    printf 'FAILED: NetworkManager still manages %s (%s).\n' "$interface_name" "$state" >&2
    failures+=("managed")
  fi

  if [[ "${#failures[@]}" -gt 0 ]]; then
    return 1
  fi
  return 0
}

disable_distro_hostapd() {
  if systemctl cat hostapd.service >/dev/null 2>&1; then
    systemctl disable --now hostapd.service || true
  fi
}

activate_services() {
  systemctl daemon-reload
  disable_distro_hostapd
  systemctl enable "$SERVICE_HOSTAPD" "$SERVICE_ADDRESS"
  systemctl restart "$SERVICE_HOSTAPD"
  systemctl start "$SERVICE_ADDRESS"
}

main() {
  local interface_name hostapd_bin ethernet_before ethernet_after
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
  require_command systemctl
  require_root
  hostapd_bin="$(command -v hostapd || true)"
  if [[ -z "$hostapd_bin" ]]; then
    error "hostapd is required but was not found. Install it with: sudo apt-get install hostapd"
  fi

  interface_name="$(resolve_interface "${1:-}")"
  require_ap_capable "$interface_name"
  require_regulatory_domain
  refuse_competing_network_managers "$interface_name"
  ethernet_before="$(ethernet_snapshot)"

  info "Using Wi-Fi interface ${interface_name} as the VoiceStock access point."
  install_access_point_files "$interface_name" "$hostapd_bin"
  if ! verify_generated_tree "$interface_name" "$hostapd_bin"; then
    recovery_hint "$interface_name"
    error "Generated access-point files are not valid."
  fi

  release_wifi_from_networkmanager "$interface_name"
  activate_services

  if ! verify_runtime "$interface_name"; then
    recovery_hint "$interface_name"
    error "Access-point configuration is not in the required state."
  fi

  ethernet_after="$(ethernet_snapshot)"
  if [[ "$ethernet_before" != "$ethernet_after" ]]; then
    recovery_hint "$interface_name"
    error "Ethernet device state changed while configuring Wi-Fi. This script must not modify Ethernet."
  fi

  info "VoiceStock access point is running under hostapd."
  info "${interface_name} has ${VOICESTOCK_PI_ADDRESS} with no gateway, DNS, DHCP, NAT, or default route from this setup."
  info "NetworkManager remains in service for Ethernet and other devices."
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
