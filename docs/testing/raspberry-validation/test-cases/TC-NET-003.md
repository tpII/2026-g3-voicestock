# TC-NET-003 — Reboot persistence of the isolated cell

- Status: DESIGNED
- Executions: none
- Procedure version: 1

## Objective

Show that `voicestock-ap` and `voicestock-client` return after a reboot
without running the setup scripts again, and that the PC default route is
still the Internet interface.

## Test level and type

Level: hardware validation.

Type: functional. One reboot of each machine, not a timing benchmark.

## Requirements and ClickUp traceability

- ClickUp: [LocalNetworkInfra-04](https://app.clickup.com/t/86e3jutyu).
- Requirement: autoconnect of the two profiles, as set by the setup
  scripts. The setup guide lists reboot survival as not yet demonstrated.

## Source modules and documentation

- [Local network setup](../../../setup/local-network.md), troubleshooting
  "voicestock-ap is inactive after reboot".
- [TC-NET-002](TC-NET-002.md).

## Preconditions and dependencies

- [TC-NET-002](TC-NET-002.md) met its reachability criteria on this
  configuration.
- The operator has a way back to a shell if Wi-Fi does not return (local
  console on the Pi, and local or Internet access on the PC). If the only
  path to the Pi is the VoiceStock cell, do not reboot the Pi until a
  fallback console is available. Otherwise the case is **BLOCKED**.

## Required hardware and software

- Same cell as TC-NET-002.
- Physical access to power or a local console.

## Preparation

Record active profiles and addresses with the same read-only commands as
TC-NET-001. Do not rerun the setup scripts.

## Execution

1. Reboot only the Raspberry Pi. Leave the PC associated.
2. After the Pi is back, from the PC run one ping of ten echoes to
   `192.168.50.1` and the Pi-side read-only checks (`nmcli`, `ip`, the
   `-g` query for `voicestock-ap`). The ping sample is a functional check
   of return, not a new RTT baseline. Zero replies fails. A non-zero loss
   allowance stays **TO BE DEFINED**, as in TC-NET-002.
3. Reboot only the PC after the Pi is stable. Confirm from the local
   console or from the returning session that `voicestock-client` is
   active, `192.168.50.2/24` is present, and the default route is the
   Internet interface.
4. From the Pi, ping the PC ten times. From the PC, confirm one successful
   probe of `1.1.1.1` that does not use the VoiceStock interface, and from
   the Pi confirm that `1.1.1.1` still does not answer.
5. Do not run the setup scripts between the reboot and the checks. If a
   profile did not return and the operator runs a script to repair it,
   that repair is a new execution and this one stays **FAILED**.

## Observations and evidence

- Timestamps of each reboot command and of the first successful ping.
- The time from power-on to first ping is user-observed and **TO BE
  DEFINED** as a gate. Record it. Do not fail the case on that duration
  alone.
- Profile names and addresses after each reboot.

## Metrics

| Metric | Rule |
| --- | --- |
| Pi profile returns without the script | Pass or fail |
| PC profile returns without the script | Pass or fail |
| Time to first successful ping | Recorded, limit **TO BE DEFINED** |
| Isolation after reboot | Same rules as TC-NET-002 |

## Acceptance criteria

1. After the Pi reboot, `voicestock-ap` is active, the address is
   `192.168.50.1/24`, there is still no default route on the Pi, and the
   PC receives at least one ping reply without anyone rerunning the Pi
   script.
2. After the PC reboot, `voicestock-client` is active on the same
   interface, the address is `192.168.50.2/24`, `never-default` behavior
   still holds (default route is not the VoiceStock interface), and the
   Pi receives at least one ping reply.
3. The PC still reaches `1.1.1.1` without using the VoiceStock interface.
   If it does not, isolation is **BLOCKED**, not passed.
4. The Pi still does not reach `1.1.1.1`.

## Failure conditions

- A profile is absent after reboot until a script is run: **FAILED**.
- The PC default route moves to the VoiceStock interface: **FAILED**.
- No fallback console and the operator cannot tell whether the Pi booted:
  **BLOCKED**.

## Recovery and cleanup

Use the setup guide's troubleshooting only after this execution is closed
as **FAILED** or **BLOCKED**. Restoring service is a later execution.

## Limitations and exclusions

One reboot of each host does not measure long-term drift, power loss during
association, or a second access point with the same SSID. Those are
follow-ups, not silent extensions of this case.
