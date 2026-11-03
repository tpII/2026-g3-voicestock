#!/usr/bin/env bash
# Regression for require_managed in scripts/setup_pi_access_point.sh.
#
# NetworkManager prints GENERAL.STATE as "<code> (<label>)". The previous
# check used the glob 10*, which matches both "10 (unmanaged)" and
# "100 (connected)". These cases call the script function with a mocked
# nmcli. They do not need root, Wi-Fi hardware, or a live NetworkManager.

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
script="${repo_root}/scripts/setup_pi_access_point.sh"

if [[ ! -f "$script" ]]; then
  printf 'FAIL: missing %s\n' "$script" >&2
  exit 1
fi

failures=0

pass() {
  printf 'PASS: %s\n' "$1"
}

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  failures=$((failures + 1))
}

# Historical check, kept only to show why state 100 was rejected.
legacy_glob_rejects_as_unmanaged() {
  local state="$1"
  case "$state" in
    10* | unmanaged* | Unmanaged*)
      return 0
      ;;
  esac
  return 1
}

# Exit status 0 means require_managed accepted the interface.
# Exit status 1 means it rejected the interface as unmanaged.
# Any other status is a harness or script failure.
run_require_managed() {
  local stderr_file rc
  # require_managed declares its own local "state". Bash dynamic scope
  # would hide a mock variable of that same name, so the canned nmcli
  # response uses a name the script does not declare.
  NMCLI_DEVICE_STATE="$1"
  stderr_file="$(mktemp)"
  set +e
  (
    nmcli() {
      if [[ "$1" == "-g" && "$2" == "GENERAL.STATE" && "$3" == "device" && "$4" == "show" && "$5" == "wlan0" ]]; then
        printf '%s\n' "$NMCLI_DEVICE_STATE"
        return 0
      fi
      printf 'unexpected nmcli invocation: %s\n' "$*" >&2
      return 97
    }
    # shellcheck disable=SC1090
    source "$script"
    require_managed wlan0
  ) 2>"$stderr_file"
  rc=$?
  set -e
  printf '%s\n' "$rc"
  cat "$stderr_file" >&2
  rm -f "$stderr_file"
}

assert_rejected() {
  local state="$1"
  local description="$2"
  local stderr_file rc
  stderr_file="$(mktemp)"
  set +e
  rc="$(run_require_managed "$state" 2>"$stderr_file")"
  set -e
  if [[ "$rc" != "1" ]]; then
    printf '%s\n' "$(cat "$stderr_file")" >&2
    rm -f "$stderr_file"
    fail "${description}: expected unmanaged rejection, got exit ${rc}"
    return
  fi
  if ! grep -F -q "ERROR: Wi-Fi interface wlan0 is not managed by NetworkManager." "$stderr_file"; then
    printf '%s\n' "$(cat "$stderr_file")" >&2
    rm -f "$stderr_file"
    fail "${description}: rejection did not use the unmanaged error"
    return
  fi
  rm -f "$stderr_file"
  pass "$description"
}

assert_accepted() {
  local state="$1"
  local description="$2"
  local stderr_file rc
  stderr_file="$(mktemp)"
  set +e
  rc="$(run_require_managed "$state" 2>"$stderr_file")"
  set -e
  if [[ "$rc" != "0" ]]; then
    printf '%s\n' "$(cat "$stderr_file")" >&2
    rm -f "$stderr_file"
    fail "${description}: expected the managed-state check to accept it, got exit ${rc}"
    return
  fi
  if grep -F -q "not managed by NetworkManager" "$stderr_file"; then
    printf '%s\n' "$(cat "$stderr_file")" >&2
    rm -f "$stderr_file"
    fail "${description}: accepted state still printed the unmanaged error"
    return
  fi
  rm -f "$stderr_file"
  pass "$description"
}

if grep -F -q '10*' "$script"; then
  fail "setup script still contains the 10* glob"
else
  pass "setup script no longer uses a 10* glob"
fi

assert_rejected "10 (unmanaged)" "10 (unmanaged) is rejected"
assert_accepted "100 (connected)" "100 (connected) is accepted"
assert_accepted "30 (disconnected)" "30 (disconnected) is accepted"
assert_accepted "50 (connecting (prepare))" "50 (connecting (prepare)) is not unmanaged"
assert_accepted "20 (unavailable)" "20 (unavailable) is not unmanaged"
assert_rejected "unmanaged" "textual unmanaged is rejected"
assert_rejected "Unmanaged" "textual Unmanaged is rejected"

if legacy_glob_rejects_as_unmanaged "100 (connected)"; then
  pass "historical 10* glob matches 100 (connected)"
else
  fail "historical 10* glob no longer matches 100 (connected); the regression no longer demonstrates the defect"
fi

if legacy_glob_rejects_as_unmanaged "10 (unmanaged)"; then
  pass "historical 10* glob still matches 10 (unmanaged)"
else
  fail "historical 10* glob should match 10 (unmanaged)"
fi

if [[ "$failures" -ne 0 ]]; then
  printf 'FAIL: %s check(s) failed\n' "$failures" >&2
  exit 1
fi

printf 'OK: require_managed state regression passed\n'
