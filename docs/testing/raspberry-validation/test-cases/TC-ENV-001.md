# TC-ENV-001 — Raspberry Pi environment and hardware baseline

- Status: DESIGNED
- Executions: [EX-TC-ENV-001-20261027-01](../executions/EX-TC-ENV-001-20261027-01.md) (`PASSED_PENDING_DOCUMENTATION`, not closed)
- Procedure version: 2

## Objective

Record the Raspberry Pi hardware, operating system, Python, Git revision,
power diagnostics, and the network configuration already present, before
this campaign changes anything. Collect the same class of facts for the PC
when the PC is available. A missing PC does not withhold closure of the Pi
baseline and does not show that the PC can be reached.

## Test level and type

Level: hardware validation.

Type: baseline. This case has no product pass/fail beyond "the record is
complete enough to reproduce the session".

## Requirements and ClickUp traceability

- ClickUp: none. Supporting check.
- Requirement: later Pi-only cases can name the board they ran on. A case
  that uses the PC still has to record that PC before it measures anything.
  An empty PC section is not a connectivity result.

## Source modules and documentation

- Documents: [campaign README](../README.md),
  [measurement methodology](../measurement-methodology.md),
  [local network setup](../../../setup/local-network.md).
- Do not run `scripts/setup_pi_access_point.sh` or
  `scripts/setup_pc_voicestock_wifi.sh` in this case.

## Preconditions and dependencies

- None. This case is first.
- The operator can open a shell on the Raspberry Pi.
- A shell on the PC is optional for this case.

## Required hardware and software

- The project Raspberry Pi 3, powered, with a shell.
- The project PC, when it is on hand. Its absence does not stop the Pi
  record.
- The button and USB microphone may be unplugged. Record whether they are
  attached. Do not wire them in this case.
- `git`, `python3`, and `ip`. `nmcli`, `iw`, and `vcgencmd` are recorded if
  they exist and their absence is a result, not a prompt to install them.

## Preparation

1. Do not install packages, do not change NetworkManager profiles, and do
   not edit the repository.
2. Note the access path (local keyboard, SSH, or serial). SSH itself is not
   part of the result.

## Execution

On the Raspberry Pi, from the VoiceStock checkout:

```bash
git rev-parse HEAD
git status --porcelain
tr -d '\0' < /proc/device-tree/model
. /etc/os-release && printf '%s\n%s\n' "$PRETTY_NAME" "$VERSION_ID"
uname -srvmo
python3 --version
ip -4 addr
ip -4 route
nmcli device status
nmcli connection show --active
iw reg get
```

If `vcgencmd` is on `PATH`:

```bash
vcgencmd get_throttled
```

If the project virtual environment exists, activate it and record:

```bash
python --version
python -m pip show voicestock gpiozero sounddevice httpx fastapi uvicorn
python -c "import sounddevice"
```

If `import sounddevice` raises, copy the exception type and message. Do not
install PortAudio in this execution.

Record the Pi power supply only from what is printed on it or visible to
the operator. Otherwise write UNKNOWN. `vcgencmd get_throttled` is the
power diagnostic. Copy the hex value. Do not treat it as a pass or a fail.

On the PC, when a shell is available in this same execution, run the same
git, OS, `uname`, `python`, `ip`, and `nmcli` commands. Do not run
`iw reg get` unless `iw` exists. If the PC is not available, write this
line and nothing else in the PC section:

```text
NOT COLLECTED — PC NOT AVAILABLE
```

Do not invent PC addresses, routes, or package versions. Do not ping the
PC from the Pi in order to fill the gap. A later case that needs the PC
collects those facts in its own execution before it starts. That later
collection is still not a connectivity pass. Connectivity is TC-NET-002.

## Observations and evidence

- One Pi transcript, redacted, referenced from the execution record.
- One PC transcript, or the single line `NOT COLLECTED — PC NOT AVAILABLE`.
- Whether `sounddevice` imports.
- The regulatory-domain line if `iw reg get` ran. Do not change it here.
- Interface names and addresses exactly as printed. Do not assume `wlan0`.

## Metrics

- None as pass limits.
- `vcgencmd get_throttled` is recorded and not judged.
- Temperature is **NOT MEASURED** unless a thermometer was read.

## Acceptance criteria

1. The execution record contains the Pi model line, OS, kernel, Python
   version, git SHA, worktree status, and the `vcgencmd get_throttled`
   value or the explicit note that the command is absent.
2. The Pi IPv4 addresses and routes are copied from the commands, including
   "no address" when that is what was printed.
3. The PC section is either a transcript of the PC commands from this
   execution or the exact line `NOT COLLECTED — PC NOT AVAILABLE`. The
   second form still allows this case to close. It does not satisfy a
   later case that needs the PC, and it is not evidence that the PC link
   works.
4. No setup script from this campaign was run during the execution.
5. Package installation, if someone did it anyway, is a deviation and this
   criterion fails.

## Failure conditions

- A required command could not be run and the gap is not written down:
  **FAILED**.
- The Pi shell is unavailable: **BLOCKED**.
- The PC is unavailable: not a failure and not a reason to block this
  case. Record `NOT COLLECTED — PC NOT AVAILABLE`.
- The worktree is dirty: the case can still pass criterion 1 only if the
  dirty status is copied verbatim. Hiding it fails the case.

## Recovery and cleanup

No configuration was changed. Close the extra shells. Do not reboot in
order to "start clean"; a reboot is a different observation and belongs to
a new execution if it happens.

## Limitations and exclusions

This record does not show that the button, the microphone, the access
point, or the application work. A clean import of `sounddevice` does not
show that a USB microphone is present. A closed Pi baseline with the PC
marked `NOT COLLECTED — PC NOT AVAILABLE` does not show that the PC is
reachable, configured, or ready for TC-NET-001 and the cases that follow
it.
