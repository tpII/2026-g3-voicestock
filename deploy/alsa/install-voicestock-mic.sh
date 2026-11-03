#!/usr/bin/env bash
# Install or remove the Logitech G435 VoiceStock ALSA plug profile.
# This script is an explicit setup step. VoiceStock does not run it at startup.
# See docs/setup/alsa-microphone.md.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SNIPPET_FILE="${SCRIPT_DIR}/voicestock-mic-g435.asoundrc"
BEGIN_MARK="# >>> voicestock_mic G435 >>>"
END_MARK="# <<< voicestock_mic G435 <<<"
PCM_NAME="pcm.voicestock_mic"

usage() {
  cat <<'EOF'
Usage: bash deploy/alsa/install-voicestock-mic.sh [--remove] [--file PATH]

Installs the versioned Logitech G435 plug profile into ~/.asoundrc.
An existing file is never replaced wholesale. Only the marked VoiceStock
block is added, refreshed, or removed. Other ALSA settings stay in place.

  --remove     Remove the marked block. The rest of the file is kept.
  --file PATH  Target file. Default: ~/.asoundrc
  --help       Show this help.
EOF
}

info() {
  printf '==> %s\n' "$1"
}

error() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 1
}

TARGET="${HOME}/.asoundrc"
ACTION="install"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remove)
      ACTION="remove"
      shift
      ;;
    --file)
      [[ $# -ge 2 ]] || error "--file requires a path."
      TARGET="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      usage >&2
      error "Unknown argument: $1"
      ;;
  esac
done

[[ -n "$TARGET" ]] || error "The target path is empty."
[[ -f "$SNIPPET_FILE" ]] || error "Missing ALSA snippet: ${SNIPPET_FILE}"
[[ ! -L "$TARGET" ]] || error "Refusing to replace a symlink: ${TARGET}"
[[ ! -d "$TARGET" ]] || error "Target is a directory: ${TARGET}"

SNIPPET="$(<"$SNIPPET_FILE")"
# Trim trailing newlines so the marked block has a stable body.
SNIPPET="${SNIPPET%"${SNIPPET##*[![:space:]]}"}"
[[ -n "$SNIPPET" ]] || error "The ALSA snippet is empty."
[[ "$SNIPPET" != *"$BEGIN_MARK"* && "$SNIPPET" != *"$END_MARK"* ]] \
  || error "The ALSA snippet must not contain the installer markers."

BLOCK="${BEGIN_MARK}
${SNIPPET}
${END_MARK}
"

backup_once() {
  local backup="${TARGET}.voicestock.bak"
  if [[ -f "$TARGET" && ! -e "$backup" ]]; then
    cp -p "$TARGET" "$backup"
    info "Saved a one-time backup at ${backup}"
  fi
}

write_file() {
  local contents="$1"
  local directory
  directory="$(dirname "$TARGET")"
  [[ -d "$directory" ]] || error "Directory does not exist: ${directory}"
  local temporary
  temporary="$(mktemp "${TARGET}.tmp.XXXXXX")"
  printf '%s' "$contents" >"$temporary"
  mv "$temporary" "$TARGET"
}

extract_block_body() {
  local contents="$1"
  local begin_count end_count
  begin_count="$(grep -Fxc "$BEGIN_MARK" <<<"$contents" || true)"
  end_count="$(grep -Fxc "$END_MARK" <<<"$contents" || true)"
  if [[ "$begin_count" -ne "$end_count" ]]; then
    error "Malformed VoiceStock markers in ${TARGET}. Edit the file by hand; nothing was changed."
  fi
  if [[ "$begin_count" -gt 1 ]]; then
    error "More than one VoiceStock block in ${TARGET}. Edit the file by hand; nothing was changed."
  fi
  if [[ "$begin_count" -eq 0 ]]; then
    printf '%s' ""
    return
  fi
  awk -v begin="$BEGIN_MARK" -v end="$END_MARK" '
    $0 == begin { capturing = 1; next }
    $0 == end { capturing = 0; next }
    capturing { print }
  ' <<<"$contents"
}

normalized() {
  local value="$1"
  printf '%s' "${value%"${value##*[![:space:]]}"}"
}

if [[ "$ACTION" == "remove" ]]; then
  if [[ ! -e "$TARGET" ]]; then
    info "No ALSA file at ${TARGET}; nothing to remove."
    exit 0
  fi
  CURRENT="$(<"$TARGET")"
  BODY="$(extract_block_body "$CURRENT")"
  if [[ -z "$BODY" ]]; then
    if grep -Fq "$PCM_NAME" <<<"$CURRENT"; then
      error "${TARGET} defines ${PCM_NAME} without VoiceStock markers. Remove that definition by hand; nothing was changed."
    fi
    info "No VoiceStock block in ${TARGET}; nothing to remove."
    exit 0
  fi
  UPDATED="$(awk -v begin="$BEGIN_MARK" -v end="$END_MARK" '
    $0 == begin { capturing = 1; next }
    $0 == end { capturing = 0; next }
    !capturing { print }
  ' <<<"$CURRENT")"
  UPDATED="$(normalized "$UPDATED")"
  backup_once
  if [[ -z "$UPDATED" ]]; then
    rm -f "$TARGET"
    info "Removed the VoiceStock block and deleted the now-empty ${TARGET}"
  else
    write_file "${UPDATED}
"
    info "Removed the VoiceStock block from ${TARGET}"
  fi
  exit 0
fi

if [[ ! -e "$TARGET" ]]; then
  write_file "$BLOCK"
  info "Created ${TARGET} with the VoiceStock G435 profile."
  exit 0
fi

CURRENT="$(<"$TARGET")"
BODY="$(extract_block_body "$CURRENT")"
if [[ -n "$BODY" ]]; then
  if [[ "$(normalized "$BODY")" == "$(normalized "$SNIPPET")" ]]; then
    info "VoiceStock G435 profile is already installed in ${TARGET}"
    exit 0
  fi
  UPDATED="$(awk -v begin="$BEGIN_MARK" -v end="$END_MARK" -v block="$BLOCK" '
    $0 == begin { capturing = 1; if (!replaced) { printf "%s", block; replaced = 1 } next }
    $0 == end { capturing = 0; next }
    !capturing { print }
  ' <<<"$CURRENT")"
  backup_once
  if [[ "$UPDATED" != *$'\n' ]]; then
    UPDATED="${UPDATED}
"
  fi
  write_file "$UPDATED"
  info "Updated the VoiceStock block in ${TARGET}"
  exit 0
fi

if grep -Fq "$PCM_NAME" <<<"$CURRENT"; then
  error "${TARGET} already defines ${PCM_NAME} outside the VoiceStock markers. Nothing was changed. Remove or rename that definition, then run this script again."
fi

if [[ -n "$CURRENT" && "$CURRENT" != *$'\n' ]]; then
  CURRENT="${CURRENT}
"
fi
backup_once
write_file "${CURRENT}${BLOCK}"
info "Appended the VoiceStock G435 profile to ${TARGET}"
