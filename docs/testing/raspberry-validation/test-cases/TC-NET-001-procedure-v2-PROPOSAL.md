# TC-NET-001 procedure version 2 — proposal

- Status: **ADOPTED**
- In force: no. The in-force wording is [TC-NET-001](TC-NET-001.md), procedure version 2.
- First execution of that adopted procedure: [EX-TC-NET-001-20261103-03](../executions/EX-TC-NET-001-20261103-03.md)
- Applies to EX-TC-NET-001-20261103-01 and EX-TC-NET-001-20261103-02: no

This file is the proposal as it was written. It is kept so the adoption
does not erase the draft. The specification that attempt 03 ran is
[TC-NET-001](TC-NET-001.md) at procedure version 2.
[Procedure version 1](TC-NET-001-procedure-v1.md) remains the procedure
attempts 01 and 02 ran. Do not regrade them with this file. Do not edit
version 1 so that it describes `hostapd`.

The adoption happened after the `hostapd` installer was on `develop` at
`485559c` (pull request #36). TC-NET-001 is not closed by that adoption.

This draft exists because attempt 02 showed that the NetworkManager
access-point path did not yield a working WPA2 cell, and because a manual
`hostapd` session did authenticate two clients. The write-up is
[hostapd-evaluation.md](../hostapd-evaluation.md). The topology proposal
is [ADR-0012](../../../decisions/0012-evaluate-hostapd-for-the-voicestock-access-point.md),
which is also **Proposed** and does not supersede
[ADR-0010](../../../decisions/0010-use-isolated-raspberry-pi-wifi-access-point.md).

## Objective

Bring up the documented VoiceStock cell when the Raspberry Pi access point
is `hostapd` and the PC client remains a NetworkManager profile. Record
that the local configuration matches the adopted setup. This case still
does not ping the other host. Reachability stays TC-NET-002.

## Preconditions

- [TC-ENV-001](TC-ENV-001.md) has recorded `nmcli`, `ip`, and `iw reg get`.
- Country on the Pi is `AR`. If it is not, stop at **BLOCKED**. Do not
  change the country inside the execution.
- The PC is Arch Linux with two Wi-Fi interfaces. Otherwise **BLOCKED**.
- The implementation under test is the one named by the adopted ADR, not
  an untracked file in `/run`.
- `hostapd` is not left enabled as a distribution service that races
  NetworkManager. The product unit, whatever it is named, is the one the
  procedure starts.
- Ethernet may exist for SSH. If it does, write that down. Do not treat
  the run as an isolation pass. Isolation is TC-NET-002.

## Execution outline

1. On the Pi, run the adopted access-point setup for `wlan0` (or the
   interface `nmcli` actually shows). The setup must:
   - keep NetworkManager from owning that interface while `hostapd` is the
     access point;
   - start `hostapd` with WPA2-PSK and CCMP, 2.4 GHz, the documented
     channel, regulatory domain AR, and the PMF mode the adopted ADR
     requires;
   - assign `192.168.50.1/24` by the persistent method, not by a manual
     `ip addr add` typed after a failure;
   - leave gateway and DNS empty and leave no default route on `wlan0`.
2. Record `hostapd` reaching `AP-ENABLED`, then the read-only address and
   route checks. Do not print the PSK.
3. On the PC, run the adopted client setup on the dedicated interface
   (`wlp0s20f0u4` in attempt 02; take the live name from `nmcli`). The
   script must not store a temporary MAC in `802-11-wireless.mac-address`,
   and it must not treat NetworkManager state `100 (connected)` as
   unmanaged.
4. Record the client profile fields required by version 1 criterion 3,
   and record that the default route is still the Internet interface.

Do not ping. If a script exits with a failure, keep the transcript and
stop. A corrected rerun is a new execution id.

## Acceptance criteria (draft)

1. The adopted Pi setup, not a hand-edited NetworkManager hotspot, is the
   active access point. `192.168.50.1/24` is on the Wi-Fi interface without
   a follow-up manual address command. Gateway and DNS are empty. There is
   no default route via that interface. `hostapd` reports `AP-ENABLED`.
   NetworkManager is not connected to a Wi-Fi profile on that interface.
2. The PC client profile is active on the dedicated interface at
   `192.168.50.2/24`, with empty gateway, empty DNS, method `manual`,
   `never-default` `yes`, and no `802-11-wireless.mac-address` taken from
   a temporary interface address.
3. The PC default route still names the Internet interface recorded before
   the script.
4. The PMF mode in use is the mode the adopted procedure requires, written
   in the execution. Attempt 02 does not pre-approve "disabled".
5. No ping is recorded as a pass of this case.

## Failure conditions (draft)

- The adopted setup exits with a failure: **FAILED**.
- The operator has to unmanaged the device by hand, edit `/run`, or add
  the address with `ip addr add` after the setup: **FAILED**. Those steps
  were diagnostics in attempt 02, not the procedure.
- Country is not `AR`, or the PC lacks a second Wi-Fi interface:
  **BLOCKED**.
- A pass of this proposal is claimed against attempt 01 or attempt 02:
  invalid. Those runs stay on procedure version 1.

## What this proposal does not do

- It does not close TC-NET-001. Adoption of procedure version 2 does not
  close it either.
- It does not execute TC-NET-002 or TC-NET-003.
- It does not change product scripts. The installer it assumed is the one
  already on `develop` at `485559c`. This campaign branch does not carry
  that code.
- It does not move the campaign status of attempt 01 or attempt 02 off
  **FAILED**.
