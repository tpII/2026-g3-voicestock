#!/usr/bin/env bash
# Hostapd access-point installer checks. No root, no live interfaces.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
script="${repo_root}/scripts/setup_pi_access_point.sh"
failures=0

pass() { printf 'PASS: %s\n' "$1"; }
fail() { printf 'FAIL: %s\n' "$1" >&2; failures=$((failures + 1)); }

if [[ ! -f "$script" ]]; then
  printf 'FAIL: missing %s\n' "$script" >&2
  exit 1
fi

if grep -Fq 'VoiceStock-Prototype' "$script"; then
  fail "setup script contains the prototype passphrase"
else
  pass "setup script does not embed the prototype passphrase"
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

cat >"${tmp}/voicestock-network.conf" <<'EOF'
VOICESTOCK_WIFI_SSID="VoiceStock"
VOICESTOCK_WIFI_PSK="unit-test-psk"
VOICESTOCK_WIFI_SUBNET="192.168.50.0/24"
VOICESTOCK_PI_ADDRESS="192.168.50.1/24"
VOICESTOCK_PC_ADDRESS="192.168.50.2/24"
VOICESTOCK_WIFI_REGULATORY_DOMAIN="AR"
EOF

# shellcheck disable=SC1090
source "$script"
CONFIG_FILE="${tmp}/voicestock-network.conf"
load_config

install_tree() {
  local root="$1"
  VOICESTOCK_CONFIG_ROOT="$root"
  install_access_point_files wlan0 /usr/sbin/hostapd
  verify_generated_tree wlan0 /usr/sbin/hostapd
}

root_a="${tmp}/root-a"
if install_tree "$root_a" >/dev/null; then
  pass "generated access-point tree verifies"
else
  fail "generated access-point tree verifies"
fi

conf="${root_a}/etc/hostapd/voicestock.conf"
helper="${root_a}/usr/local/lib/voicestock/ap-address.sh"
unit="${root_a}/etc/systemd/system/voicestock-hostapd.service"
address_unit="${root_a}/etc/systemd/system/voicestock-ap-address.service"
unmanaged="${root_a}/etc/NetworkManager/conf.d/voicestock-unmanaged.conf"

mode="$(file_mode "$conf")"
case "$(uname -s)" in
  Linux*)
    if [[ "$mode" == "600" ]]; then
      pass "hostapd configuration mode is 600"
    else
      fail "hostapd configuration mode is ${mode}, expected 600"
    fi
    ;;
  *)
    if grep -Fq 'write_private_file 600' "$script"; then
      pass "hostapd configuration requests mode 600 (stat on this OS reports ${mode})"
    else
      fail "installer does not request mode 600"
    fi
    ;;
esac

if grep -Fq 'unit-test-psk' "$helper" "$unit" "$address_unit" "$unmanaged"; then
  fail "passphrase leaked outside the hostapd configuration"
else
  pass "passphrase stays in the hostapd configuration"
fi

if grep -Fxq 'wpa_passphrase=unit-test-psk' "$conf" \
  && [[ "$(grep -c '^wpa_passphrase=' "$conf")" == "1" ]] \
  && ! grep -Fq 'wpa_passphrase="' "$conf" \
  && grep -Fq 'ieee80211w=0' "$conf" \
  && grep -Fq 'wpa=2' "$conf" \
  && grep -Fq 'wpa_key_mgmt=WPA-PSK' "$conf" \
  && grep -Fq 'rsn_pairwise=CCMP' "$conf"; then
  pass "WPA2 passphrase matches the source with no added quotes"
else
  fail "WPA2 passphrase line does not match the source value"
fi

if grep -Fq '192.168.50.1/24' "$address_unit" && ! grep -Fq '192.168.50.1/24' "$conf"; then
  pass "static address is on the address unit, not in hostapd"
else
  fail "static address placement"
fi

cp -a "$root_a" "${tmp}/root-a-copy"
if install_tree "$root_a" >/dev/null && diff -ru "${tmp}/root-a-copy" "$root_a" >/dev/null; then
  pass "second install does not change generated files"
else
  fail "second install changed generated files"
fi

python_break="$(mktemp)"
cp "$conf" "$python_break"
# A broken security line must fail verification without echoing the passphrase.
sed 's/^wpa=2$/wpa=0/' "$conf" >"${conf}.broken"
mv "${conf}.broken" "$conf"
if verify_generated_tree wlan0 /usr/sbin/hostapd >/dev/null 2>&1; then
  fail "open or non-WPA2 configuration was accepted"
else
  pass "non-WPA2 configuration is rejected"
fi
mv "$python_break" "$conf"
rm -f "$python_break"

(
  iw() {
    if [[ "$1" == "reg" ]]; then
      printf 'country US: DFS-FCC\n'
    fi
  }
  require_regulatory_domain
) >/dev/null 2>&1 && fail "non-AR regulatory domain was accepted" || pass "non-AR regulatory domain is rejected"

(
  iw() {
    if [[ "$1" == "reg" ]]; then
      printf 'country AR: DFS-FCC\n'
    fi
  }
  require_regulatory_domain
) >/dev/null && pass "AR regulatory domain is accepted" || fail "AR regulatory domain was rejected"

(
  iw() {
    if [[ "$1" == "dev" ]]; then
      printf 'wiphy 0\n'
    elif [[ "$1" == "phy" ]]; then
      printf 'Supported interface modes:\n\t * AP\n\t * managed\n'
    fi
  }
  require_ap_capable wlan0
) >/dev/null && pass "AP mode from iw is accepted" || fail "AP mode from iw was rejected"

(
  iw() {
    if [[ "$1" == "dev" ]]; then
      printf 'wiphy 0\n'
    elif [[ "$1" == "phy" ]]; then
      printf 'Supported interface modes:\n\t * managed\n'
    fi
  }
  nmcli() { printf '\n'; }
  require_ap_capable wlan0
) >/dev/null 2>&1 && fail "interface without AP mode was accepted" || pass "interface without AP mode is rejected"

sys_root="${tmp}/sys"
mkdir -p "${sys_root}/eth0" "${sys_root}/wlan0"
(
  VOICESTOCK_SYS_NET="$sys_root"
  nmcli() {
    if [[ "$1" == "device" && "$2" == "show" ]]; then
      return 0
    fi
    if [[ "$1" == "-g" && "$2" == "GENERAL.TYPE" ]]; then
      printf 'ethernet\n'
      return 0
    fi
    return 0
  }
  resolve_interface eth0
) >/dev/null 2>&1 && fail "Ethernet interface was accepted" || pass "Ethernet interface is rejected"

(
  VOICESTOCK_SYS_NET="$sys_root"
  nmcli() {
    if [[ "$1" == "-t" ]]; then
      printf 'wlan0:wifi:connected:keep\n'
      return 0
    fi
    if [[ "$1" == "device" ]]; then
      return 0
    fi
    if [[ "$1" == "-g" && "$2" == "GENERAL.TYPE" ]]; then
      printf 'wifi\n'
      return 0
    fi
    return 0
  }
  chosen="$(resolve_interface)"
  [[ "$chosen" == "wlan0" ]]
) && pass "single Wi-Fi interface is selected" || fail "single Wi-Fi interface was not selected"

mkdir -p "${sys_root}/wlan1"
(
  VOICESTOCK_SYS_NET="$sys_root"
  nmcli() {
    if [[ "$1" == "-t" ]]; then
      printf 'wlan0:wifi:connected:a\nwlan1:wifi:disconnected:\n'
      return 0
    fi
    return 0
  }
  resolve_interface
) >/dev/null 2>&1 && fail "ambiguous Wi-Fi list was accepted" || pass "ambiguous Wi-Fi list is rejected"

(
  systemctl() {
    if [[ "$1" == "is-active" && "$3" == "systemd-networkd.service" ]]; then
      return 0
    fi
    return 1
  }
  refuse_competing_network_managers wlan0
) >/dev/null 2>&1 && fail "active systemd-networkd was accepted" || pass "active systemd-networkd is rejected"

(
  systemctl() { return 1; }
  refuse_competing_network_managers wlan0
) && pass "inactive extra network managers are accepted" || fail "inactive extra network managers were rejected"

release_log="${tmp}/nmcli.log"
: >"$release_log"
(
  nmcli() {
    printf '%q ' "$@" >>"$release_log"
    printf '\n' >>"$release_log"
    if [[ "$1" == "-t" && "$3" == "NAME" ]]; then
      printf 'voicestock-ap\nnetplan-eth0\nnetplan-wlan0-WiFi-Arriba\nother-lan\n'
      return 0
    fi
    if [[ "$1" == "-t" && "$3" == "NAME,TYPE" ]]; then
      printf '%s\n' \
        'voicestock-ap:802-11-wireless' \
        'netplan-eth0:802-3-ethernet' \
        'netplan-wlan0-WiFi-Arriba:802-11-wireless' \
        'other-lan:802-11-wireless'
      return 0
    fi
    if [[ "$1" == "-t" && "$3" == "NAME,DEVICE" ]]; then
      printf '%s\n' \
        'voicestock-ap:wlan0' \
        'netplan-eth0:eth0' \
        'netplan-wlan0-WiFi-Arriba:wlan0' \
        'other-lan:wlan1'
      return 0
    fi
    if [[ "$1" == "-g" && "$2" == "connection.autoconnect" ]]; then
      printf 'yes\n'
      return 0
    fi
    return 0
  }
  VOICESTOCK_CONFIG_ROOT="${tmp}/release-root"
  release_wifi_from_networkmanager wlan0
  cp -a "${tmp}/release-root/etc/NetworkManager/conf.d/voicestock-unmanaged.conf" "${tmp}/unmanaged-first"
  release_wifi_from_networkmanager wlan0
)
if grep -Fq 'connection modify voicestock-ap connection.autoconnect no' "$release_log" \
  && grep -Fq 'connection down voicestock-ap' "$release_log" \
  && grep -Fq 'connection down netplan-wlan0-WiFi-Arriba' "$release_log" \
  && ! grep -Fq 'connection modify netplan-wlan0-WiFi-Arriba' "$release_log" \
  && ! grep -Fq 'other-lan' "$release_log" \
  && grep -Fq 'general reload' "$release_log" \
  && grep -Fq 'device set wlan0 managed no' "$release_log" \
  && grep -Fq 'unmanaged-devices+=interface-name:wlan0' "${tmp}/release-root/etc/NetworkManager/conf.d/voicestock-unmanaged.conf" \
  && cmp -s "${tmp}/unmanaged-first" "${tmp}/release-root/etc/NetworkManager/conf.d/voicestock-unmanaged.conf" \
  && ! grep -Fq 'netplan-eth0' "$release_log" \
  && ! grep -Fq 'device set eth0' "$release_log"; then
  pass "release keeps unrelated profiles and stays idempotent"
else
  fail "release changed an unrelated profile or skipped the AP interface"
fi

mock_bin="${tmp}/bin"
mkdir -p "$mock_bin"
cat >"${mock_bin}/iw" <<'EOF'
#!/bin/sh
if [ "$1" = "dev" ]; then
  cat "${IW_INFO:?}"
fi
exit 0
EOF
cat >"${mock_bin}/ip" <<'EOF'
#!/bin/sh
printf '%s\n' "$*" >> "${IP_LOG:?}"
if [ "$1" = "-4" ] && [ "$2" = "route" ]; then
  if [ -n "${IP_DEFAULT_ROUTE:-}" ] && [ -f "$IP_DEFAULT_ROUTE" ]; then
    cat "$IP_DEFAULT_ROUTE"
  fi
fi
exit 0
EOF
cat >"${mock_bin}/sysctl" <<'EOF'
#!/bin/sh
exit 0
EOF
cat >"${mock_bin}/sleep" <<'EOF'
#!/bin/sh
exit 0
EOF
chmod +x "${mock_bin}/iw" "${mock_bin}/ip" "${mock_bin}/sysctl" "${mock_bin}/sleep"

export PATH="${mock_bin}:${PATH}"
export IW_INFO="${tmp}/iw-info"
export IP_LOG="${tmp}/ip.log"
export IP_DEFAULT_ROUTE="${tmp}/default.route"
printf 'Interface wlan0\n\ttype AP\n' >"$IW_INFO"
: >"$IP_LOG"
: >"$IP_DEFAULT_ROUTE"
if VOICESTOCK_AP_WAIT_ATTEMPTS=2 VOICESTOCK_AP_WAIT_SECONDS=0 \
  "$helper" apply wlan0 192.168.50.1/24; then
  pass "address helper applies 192.168.50.1/24 in AP mode"
else
  fail "address helper did not apply the address"
fi
if grep -Fq 'addr replace 192.168.50.1/24 dev wlan0' "$IP_LOG" \
  && ! grep -Fq 'route add default' "$IP_LOG"; then
  pass "address helper does not install a default route"
else
  fail "address helper route commands were unexpected"
fi

printf 'type managed\n' >"$IW_INFO"
if VOICESTOCK_AP_WAIT_ATTEMPTS=2 VOICESTOCK_AP_WAIT_SECONDS=0 \
  "$helper" apply wlan0 192.168.50.1/24 >/dev/null 2>&1; then
  fail "address helper applied an address before AP mode"
else
  pass "address helper waits for AP mode"
fi

printf 'Interface wlan0\n\ttype AP\n' >"$IW_INFO"
printf 'default via 192.168.1.1 dev wlan0 proto dhcp\n' >"$IP_DEFAULT_ROUTE"
: >"$IP_LOG"
if VOICESTOCK_AP_WAIT_ATTEMPTS=1 VOICESTOCK_AP_WAIT_SECONDS=0 \
  "$helper" apply wlan0 192.168.50.1/24 >/dev/null 2>&1; then
  fail "address helper kept a default route on wlan0"
else
  pass "address helper rejects a default route on wlan0"
fi

if [[ "$failures" -ne 0 ]]; then
  printf 'FAIL: %s check(s) failed\n' "$failures" >&2
  exit 1
fi
printf 'OK: hostapd access-point regression passed\n'
