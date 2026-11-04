# TC-NET-003 — Reboot persistence of the isolated cell

- Status: DESIGNED
- Executions: [EX-TC-NET-003-20261103-01](../executions/EX-TC-NET-003-20261103-01.md) (`PASSED_PENDING_DOCUMENTATION`; technical reboot recovery PASSED; evidence pending; procedure version 2; review NOT_REVIEWED; not `CLOSED_PASSED`)
- Procedure version: 2

Procedure version 2 below is the procedure in force. The Raspberry Pi
access point returns through `voicestock-hostapd.service` and
`voicestock-ap-address.service`. The Arch client returns through the
NetworkManager profile `voicestock-client`.

[Procedure version 1](TC-NET-003-procedure-v1.md) is historical. It names
the NetworkManager hotspot `voicestock-ap`. No execution ran that text.
This file does not regrade it.

## Objective

Show that the VoiceStock cell returns after a reboot of each machine
without running the setup scripts again. The Raspberry access point and
the Arch client must recover, the IPv4 addresses must be the documented
ones, the Arch Internet route must stay on the Internet interface, the
Raspberry must keep IPv4 isolation, and the two hosts must answer each
other.

## Test level and type

Level: hardware validation.

Type: functional. One reboot of each machine, not a timing benchmark and
not a long-term availability test.

## Requirements and ClickUp traceability

- ClickUp: [LocalNetworkInfra-04](https://app.clickup.com/t/86e3jutyu).
- Requirement: the enabled VoiceStock units and the Arch client profile
  survive reboot, as set by the installer under test. Reboot survival is
  not demonstrated by TC-NET-001 or TC-NET-002.

## Source modules and documentation

- [Local network setup](../../../setup/local-network.md) on the revision
  under test. On `develop` at `485559c` the reboot check is the two
  VoiceStock units and an unmanaged `wlan0`, not an active
  `voicestock-ap` profile.
- [TC-NET-002](TC-NET-002.md).

## Preconditions and dependencies

- [TC-NET-002](TC-NET-002.md) met its reachability criteria on this
  configuration. A prerequisite that is **PASSED_PENDING_DOCUMENTATION**
  is not **CLOSED_PASSED**. Record that status. Do not treat it as formal
  closure.
- The operator has a way back to a shell if Wi-Fi does not return. If the
  only path to the Pi is the VoiceStock cell, do not reboot the Pi until a
  fallback console is available. Otherwise the case is **BLOCKED** when
  the operator cannot tell whether the Pi booted.

## Required hardware and software

- Same cell as TC-NET-002.
- Physical access to power or a local console.
- `hostapd` already installed. This case does not install it and does not
  run `scripts/setup_pi_access_point.sh` or
  `scripts/setup_pc_voicestock_wifi.sh`.

## Preparation

Record, without rerunning the setup scripts:

- Pi boot id, unit states, `wlan0` address, and whether a default IPv4
  route exists.
- PC boot id, active connections, both addresses, and the default route.
- Whether Ethernet is connected. If it is disconnected, write that down.
  Do not treat an unused Ethernet port as a connected recovery path.

## Execution

1. Reboot only the Raspberry Pi. Leave the PC associated. Ethernet stays
   in the state recorded above.
2. After the Pi is back, from the PC run one ping of ten echoes to
   `192.168.50.1`. On the Pi, record the new boot id,
   `systemctl is-active` for `voicestock-hostapd.service` and
   `voicestock-ap-address.service`, `iw` for SSID and AP mode, the
   `wlan0` address, `ip -4 route`, and NetworkManager's view of `wlan0`.
   The ten echoes are a functional check of return, not a new RTT
   baseline. Zero replies fails. A non-zero loss allowance stays
   **TO BE DEFINED**, as in TC-NET-002.
3. Reboot only the PC after the Pi is stable. Do not run the client script
   and do not activate `voicestock-client` by hand. Confirm the new boot
   id, that `voicestock-client` is connected on the dedicated interface,
   that `192.168.50.2/24` is present, and that the default route is the
   Internet interface.
4. From the PC, ping `192.168.50.1` ten times again. Confirm one successful
   probe of `1.1.1.1` that does not use the VoiceStock interface. From the
   Pi, ping the PC ten times, then confirm that the Pi has no default IPv4
   route and that `1.1.1.1` does not answer.
5. Do not run the setup scripts between the reboot and the checks. If a
   unit or profile did not return and the operator runs a script or a
   manual activation to repair it, that repair is a new execution and this
   one stays **FAILED**.

An immediate `Network is unreachable` on the Pi is a failure to reach
`1.1.1.1`. It is not a three-packet loss rate. Do not invent that rate.
IPv6 and tunnel isolation are not this criterion.

## Observations and evidence

- Boot ids before and after each reboot.
- Timestamps of each reboot command and of the first successful ping, when
  captured. If they were not captured, write NOT RECORDED. Do not estimate
  them from a ten-packet ping elapsed time.
- The time from power-on to first ping is user-observed and **TO BE
  DEFINED** as a gate. Record it when it was measured. Do not fail the
  case on that duration alone, and do not fail it because the duration was
  not supplied.
- Unit names, profile names, and addresses after each reboot.

No separate warm-up echo is required. Do not discard one of the ten
functional replies as a warm-up that was not run.

## Metrics

| Metric | Rule |
| --- | --- |
| Pi units and address return without the script | Pass or fail |
| PC profile returns without the script | Pass or fail |
| Time to first successful ping | Recorded when measured. Limit **TO BE DEFINED**. Not estimated. |
| Isolation after reboot | Same IPv4 rules as TC-NET-002 |

Supplementary mean, median, and sample standard deviation may be computed
from the printed reply lines. They do not replace ping's own summary, and
ping's `mdev` is not that sample standard deviation. They are not a new
latency baseline.

## Acceptance criteria

1. The Pi boot id changes. After that reboot, both VoiceStock units are
   active without anyone rerunning the Pi script. `wlan0` is the access
   point at `192.168.50.1/24`, NetworkManager is not managing it, there is
   no default IPv4 route, and the PC receives at least one ping reply.
2. The PC boot id changes. After that reboot, `voicestock-client` is
   connected on the same dedicated interface, the address is
   `192.168.50.2/24`, the default route is not the VoiceStock interface,
   and no client script or manual activation was used.
3. The PC still reaches `1.1.1.1` without using the VoiceStock interface.
   If it does not, isolation is **BLOCKED**, not passed.
4. After both reboots the Pi receives at least one ping reply from the PC,
   still has no default IPv4 route, and still does not reach `1.1.1.1`.
   That isolation claim is IPv4 only.

## Failure conditions

- A unit or profile is absent after reboot until a script or a manual
  activation is run: **FAILED**.
- The PC default route moves to the VoiceStock interface: **FAILED**.
- Zero ping replies from the peer after a reboot: **FAILED**.
- No fallback and the operator cannot tell whether the Pi booted:
  **BLOCKED**.

## Recovery and cleanup

Use the setup guide's troubleshooting only after this execution is closed
as **FAILED** or **BLOCKED**. Restoring service is a later execution.

## Limitations and exclusions

One reboot of each host does not measure long-term drift, power loss during
association, startup latency, or a second access point with the same SSID.
It does not prove IPv6 isolation or the absence of every tunnel. Those are
follow-ups, not silent extensions of this case.
