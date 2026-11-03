#!/usr/bin/env bash
# Arch client setup checks. No root, no live interfaces.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
script="${repo_root}/scripts/setup_pc_voicestock_wifi.sh"
failures=0

pass() { printf 'PASS: %s\n' "$1"; }
fail() { printf 'FAIL: %s\n' "$1" >&2; failures=$((failures + 1)); }

if [[ ! -f "$script" ]]; then
  printf 'FAIL: missing %s\n' "$script" >&2
  exit 1
fi

if grep -Fq '10*' "$script"; then
  fail "PC setup script still contains the 10* glob"
else
  pass "PC setup script does not use a 10* glob"
fi

if grep -Fq '/address' "$script" || grep -Fq 'interface_mac' "$script"; then
  fail "PC setup script still reads a transient MAC"
else
  pass "PC setup script does not read a transient MAC"
fi

if grep -Fq 'VoiceStock-Prototype' "$script"; then
  fail "PC setup script contains the prototype passphrase"
else
  pass "PC setup script does not embed the prototype passphrase"
fi

# shellcheck disable=SC1090
source "$script"

run_require_managed() {
  local stderr_file rc
  NMCLI_DEVICE_STATE="$1"
  stderr_file="$(mktemp)"
  set +e
  (
    nmcli() {
      if [[ "$1" == "-g" && "$2" == "GENERAL.STATE" && "$5" == "wlp0s20f0u4" ]]; then
        printf '%s\n' "$NMCLI_DEVICE_STATE"
        return 0
      fi
      printf 'unexpected nmcli: %s\n' "$*" >&2
      return 97
    }
    require_managed wlp0s20f0u4
  ) 2>"$stderr_file"
  rc=$?
  set -e
  printf '%s\n' "$rc"
  cat "$stderr_file" >&2
  rm -f "$stderr_file"
}

assert_rejected() {
  local state="$1" description="$2" stderr_file rc
  stderr_file="$(mktemp)"
  set +e
  rc="$(run_require_managed "$state" 2>"$stderr_file")"
  set -e
  if [[ "$rc" == "1" ]] && grep -Fq "is not managed by NetworkManager." "$stderr_file"; then
    pass "$description"
  else
    fail "${description}: exit ${rc}"
  fi
  rm -f "$stderr_file"
}

assert_accepted() {
  local state="$1" description="$2" stderr_file rc
  stderr_file="$(mktemp)"
  set +e
  rc="$(run_require_managed "$state" 2>"$stderr_file")"
  set -e
  if [[ "$rc" == "0" ]] && ! grep -Fq "not managed by NetworkManager" "$stderr_file"; then
    pass "$description"
  else
    fail "${description}: exit ${rc}"
  fi
  rm -f "$stderr_file"
}

assert_rejected "10 (unmanaged)" "10 (unmanaged) is rejected"
assert_accepted "100 (connected)" "100 (connected) is accepted"
assert_accepted "30 (disconnected)" "30 (disconnected) is accepted"
assert_rejected "unmanaged" "textual unmanaged is rejected"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
sys_root="${tmp}/sys"
mkdir -p "${sys_root}/wlo1" "${sys_root}/wlp0s20f0u4"
printf '02:00:00:11:22:33\n' >"${sys_root}/wlp0s20f0u4/address"

cat >"${tmp}/voicestock-network.conf" <<'EOF'
VOICESTOCK_WIFI_SSID="VoiceStock"
VOICESTOCK_WIFI_PSK="unit-test-psk"
VOICESTOCK_WIFI_SUBNET="192.168.50.0/24"
VOICESTOCK_PI_ADDRESS="192.168.50.1/24"
VOICESTOCK_PC_ADDRESS="192.168.50.2/24"
VOICESTOCK_WIFI_REGULATORY_DOMAIN="AR"
EOF
CONFIG_FILE="${tmp}/voicestock-network.conf"
load_config

(
  nmcli() {
    if [[ "$1" == "-t" ]]; then
      printf 'wlo1:wifi:connected:lan\n'
      return 0
    fi
    return 0
  }
  require_two_wifi_interfaces
) >/dev/null 2>&1 && fail "one Wi-Fi interface was accepted" || pass "one Wi-Fi interface is rejected"

(
  nmcli() {
    if [[ "$1" == "-t" ]]; then
      printf 'wlo1:wifi:connected:lan\nwlp0s20f0u4:wifi:disconnected:\n'
      return 0
    fi
    return 0
  }
  require_two_wifi_interfaces
) && pass "two Wi-Fi interfaces are accepted" || fail "two Wi-Fi interfaces were rejected"

(
  ip() {
    printf 'default via 192.168.1.1 dev wlo1 proto dhcp src 192.168.1.87 metric 600\n'
  }
  nmcli() {
    if [[ "$1" == "-t" ]]; then
      printf 'lan:wlo1\n'
      return 0
    fi
    if [[ "$1" == "-g" && "$2" == "IP4.GATEWAY" ]]; then
      printf '192.168.1.1\n'
      return 0
    fi
    return 0
  }
  require_not_internet_interface wlo1
) >/dev/null 2>&1 && fail "Internet interface was accepted" || pass "Internet interface is rejected"

(
  ip() { printf '\n'; }
  nmcli() {
    if [[ "$1" == "-t" ]]; then
      printf '\n'
      return 0
    fi
    if [[ "$1" == "-g" && "$2" == "IP4.GATEWAY" ]]; then
      printf '\n'
      return 0
    fi
    return 0
  }
  require_not_internet_interface wlp0s20f0u4
) && pass "dedicated interface without a default route is accepted" || fail "dedicated interface was rejected"

(
  ip() { printf '\n'; }
  nmcli() {
    if [[ "$1" == "-t" ]]; then
      printf 'voicestock-client:wlp0s20f0u4\n'
      return 0
    fi
    if [[ "$1" == "-g" && "$2" == "IP4.GATEWAY" ]]; then
      printf '\n'
      return 0
    fi
    return 0
  }
  require_not_internet_interface wlp0s20f0u4
) && pass "active VoiceStock profile without a route or gateway is accepted" || fail "active VoiceStock profile was rejected"

(
  ip() {
    printf 'default via 192.168.1.1 dev wlp0s20f0u4 proto static\n'
  }
  nmcli() {
    if [[ "$1" == "-t" ]]; then
      printf 'voicestock-client:wlp0s20f0u4\n'
      return 0
    fi
    return 0
  }
  require_not_internet_interface wlp0s20f0u4
) >/dev/null 2>&1 && fail "active VoiceStock profile on the default route was accepted" || pass "active VoiceStock profile on the default route is rejected"

(
  ip() { printf '\n'; }
  nmcli() {
    if [[ "$1" == "-t" ]]; then
      printf 'voicestock-client:wlp0s20f0u4\n'
      return 0
    fi
    if [[ "$1" == "-g" && "$2" == "IP4.GATEWAY" ]]; then
      printf '192.168.1.1\n'
      return 0
    fi
    return 0
  }
  require_not_internet_interface wlp0s20f0u4
) >/dev/null 2>&1 && fail "active VoiceStock profile with a gateway was accepted" || pass "active VoiceStock profile with a gateway is rejected"

log="${tmp}/nmcli.log"
: >"$log"
profile_exists=0
nmcli() {
  printf '%q ' "$@" >>"$log"
  printf '\n' >>"$log"
  if [[ "$1" == "-t" && "$3" == "NAME" ]]; then
    if [[ "$profile_exists" == 1 ]]; then
      printf 'voicestock-client\n'
    fi
    return 0
  fi
  if [[ "$1" == "-g" && "$2" == "connection.type" ]]; then
    printf '802-11-wireless\n'
    return 0
  fi
  if [[ "$1" == "-g" && "$2" == "ipv4.gateway" ]]; then
    printf '\n'
    return 0
  fi
  if [[ "$1" == "-g" && "$2" == "ipv4.dns" ]]; then
    printf '\n'
    return 0
  fi
  if [[ "$1" == "-g" && "$2" == "ipv4.addresses" ]]; then
    printf '192.168.50.2/24\n'
    return 0
  fi
  if [[ "$1" == "connection" && "$2" == "add" ]]; then
    profile_exists=1
    return 0
  fi
  return 0
}

VOICESTOCK_SYS_NET="$sys_root"
create_or_update_profile wlp0s20f0u4
create_or_update_profile wlp0s20f0u4

add_count="$(grep -c 'connection add ' "$log" || true)"
if [[ "$add_count" == "1" ]]; then
  pass "profile is created once and then updated"
else
  fail "connection add ran ${add_count} times"
fi

if grep -Fq '02:00:00:11:22:33' "$log"; then
  fail "randomized MAC was written into the profile"
else
  pass "randomized MAC is not a profile restriction"
fi

if grep -Fq "802-11-wireless.mac-address ''" "$log" \
  && grep -Fq 'connection.interface-name wlp0s20f0u4' "$log" \
  && grep -Fq 'ipv4.addresses 192.168.50.2/24' "$log" \
  && grep -Fq 'ipv4.never-default yes' "$log" \
  && grep -Fq 'ipv6.method disabled' "$log" \
  && ! grep -Fq 'wlo1' "$log" \
  && ! grep -Fq 'ipv4.gateway 192.168.1.1' "$log"; then
  pass "client profile binds the interface, clears MAC, and keeps static addressing"
else
  fail "client profile settings were not recorded as required"
fi

if [[ "$failures" -ne 0 ]]; then
  printf 'FAIL: %s check(s) failed\n' "$failures" >&2
  exit 1
fi
printf 'OK: Arch client regression passed\n'
