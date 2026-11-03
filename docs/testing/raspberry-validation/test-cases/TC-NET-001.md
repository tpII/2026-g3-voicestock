# TC-NET-001 — Raspberry Pi access point configuration

- Status: DESIGNED
- Executions: [EX-TC-NET-001-20261103-01](../executions/EX-TC-NET-001-20261103-01.md) (`FAILED`, procedure version 1, not closed). Incident: [INC-EX-TC-NET-001-20261103-01-01](../executions/INC-EX-TC-NET-001-20261103-01-01.md) (`OPEN`). [EX-TC-NET-001-20261103-02](../executions/EX-TC-NET-001-20261103-02.md) (`FAILED`, procedure version 1, not closed). Incidents: [INC-EX-TC-NET-001-20261103-02-01](../executions/INC-EX-TC-NET-001-20261103-02-01.md) (`OPEN`), [INC-EX-TC-NET-001-20261103-02-02](../executions/INC-EX-TC-NET-001-20261103-02-02.md) (`OPEN`), [INC-EX-TC-NET-001-20261103-02-03](../executions/INC-EX-TC-NET-001-20261103-02-03.md) (`OPEN`). [EX-TC-NET-001-20261103-03](../executions/EX-TC-NET-001-20261103-03.md) (`PASSED_PENDING_DOCUMENTATION`; technical configuration PASSED; evidence pending; procedure version 2; review NOT_REVIEWED; not `CLOSED_PASSED`).
- Procedure version: 2

Procedure version 2 below is the procedure in force. It configures the
Raspberry Pi access point with the repository `hostapd` installer and the
PC client with NetworkManager.

Three texts are distinct. [Procedure version 1](TC-NET-001-procedure-v1.md)
is historical. Attempts 01 and 02 ran that text and stay **FAILED**. This
file is procedure version 2, and it is the procedure in force. The
[proposal](TC-NET-001-procedure-v2-PROPOSAL.md) keeps its filename and is
only the historical design artifact. It is not the specification. This
revision does not regrade attempts 01 and 02.

[ADR-0010](../../../decisions/0010-use-isolated-raspberry-pi-wifi-access-point.md)
remains the topology. The campaign file
[ADR-0012](../../../decisions/0012-evaluate-hostapd-for-the-voicestock-access-point.md)
stays **Proposed** and is not renumbered here. The installer under test
is the one merged to `develop` by pull request #36, commit `485559c`.
That product history is not copied into this ADR file.

## Objective

Bring up the documented VoiceStock cell when the Raspberry Pi access point
is `hostapd` and the PC client remains a NetworkManager profile. Record
that the local configuration matches that installer. This case does not
ping the other host.

## Test level and type

Level: hardware validation of the local network configuration.

Type: functional. Reachability is TC-NET-002. Reboot persistence is
TC-NET-003.

## Requirements and ClickUp traceability

- ClickUp: [LocalNetworkInfra-04](https://app.clickup.com/t/86e3jutyu).
- Requirement: the Pi is an isolated access point at `192.168.50.1/24` and
  the PC's dedicated Wi-Fi interface is `192.168.50.2/24`, as specified in
  [ADR-0010](../../../decisions/0010-use-isolated-raspberry-pi-wifi-access-point.md).
  The access-point process is the `hostapd` installer on `develop` at
  `485559c`, not a NetworkManager hotspot and not a file left under `/run`.

## Source modules and documentation

- `scripts/setup_pi_access_point.sh` on the revision under test.
- `scripts/setup_pc_voicestock_wifi.sh` on the revision under test.
- `scripts/voicestock-network.conf` (do not print the passphrase).
- The setup guide on that same revision. On `485559c` the guide's
  verification section names `voicestock-hostapd.service`,
  `voicestock-ap-address.service`, and an unmanaged `wlan0`. The copy of
  the guide on this documentation branch can still describe the older
  NetworkManager hotspot. Execute the guide that belongs to the checkout
  under test.

## Preconditions and dependencies

- [TC-ENV-001](TC-ENV-001.md) has recorded `nmcli`, `ip`, and `iw reg get`
  before any script from this case runs.
- Raspberry Pi OS with NetworkManager, `iw`, `systemd`, and the `hostapd`
  package already installed. This execution does not install packages and
  does not change the regulatory domain.
- The PC is Arch Linux with NetworkManager and two Wi-Fi interfaces. If
  the lab PC is not that machine, stop and mark **BLOCKED**.
- Country on the Pi is `AR`. If it is not, stop at **BLOCKED**.
- Ethernet may exist for SSH. If it does, write that down. Do not treat
  the run as an isolation pass. Isolation is TC-NET-002.
- The distribution `hostapd` service must not be left running as a second
  access point. The installer disables that unit. A masked unit is an
  observation to record, not a second procedure.

## Required hardware and software

- Raspberry Pi 3 built-in Wi-Fi. The interface name comes from
  `nmcli device status`, not from an assumption that it is `wlan0`.
- PC with the Internet Wi-Fi already associated, and a second Wi-Fi
  interface that does not own the default route.
- `sudo` on both machines for the setup scripts.
- The same repository revision on both machines so both scripts read the
  same `scripts/voicestock-network.conf`. Record each machine's
  `git rev-parse HEAD`. If one SHA was not captured, write NOT RECORDED.
  Do not copy the other machine's SHA into that blank.

## Preparation

On the PC, before any VoiceStock script:

```bash
nmcli device status
ip -4 route
```

Write down which interface owns the `default` route. That interface is the
Internet interface. It must not be passed to
`setup_pc_voicestock_wifi.sh`.

On the Pi, record `iw reg get` again if the baseline is not from the same
session. Still do not change the country in this execution.

## Execution

1. On the Pi, from the repository root, run the access-point installer
   only after the country check passes. Pass the Wi-Fi interface name:

```bash
sudo bash scripts/setup_pi_access_point.sh <PI_WIFI_INTERFACE>
```

The installer must keep NetworkManager from owning that interface, start
`voicestock-hostapd.service` with WPA2-PSK and CCMP, 2.4 GHz, channel 11,
country `AR`, and `ieee80211w=0`, and assign `192.168.50.1/24` through
`voicestock-ap-address.service`. It must not require a later manual
`ip addr add`.

2. On the Pi, record the read-only checks. Do not print
`/etc/hostapd/voicestock.conf`.

```bash
systemctl is-active voicestock-hostapd.service voicestock-ap-address.service
systemctl is-enabled voicestock-hostapd.service
iw dev <PI_WIFI_INTERFACE> info
ip -4 addr
ip -4 route
nmcli device status
```

A non-secret view of the generated access-point file, when it is
collected, omits `wpa_passphrase`:

```bash
sudo awk -F= '$1 != "wpa_passphrase" { print }' /etc/hostapd/voicestock.conf
```

3. On the PC, run:

```bash
sudo bash scripts/setup_pc_voicestock_wifi.sh <PC_VOICESTOCK_INTERFACE>
```

The script must not store a temporary MAC in
`802-11-wireless.mac-address`, and it must not treat NetworkManager state
`100 (connected)` as unmanaged.

4. On the PC:

```bash
nmcli device status
nmcli connection show --active
ip -4 addr
ip -4 route show default
nmcli -g ipv4.gateway,ipv4.dns,ipv4.never-default connection show voicestock-client
```

Do not ping. Do not enable DHCP, NAT, forwarding, or a bridge. If a
script prints `FAILED`, keep the transcript and stop. A corrected rerun
is a new execution id.

## Observations and evidence

- Both transcripts with secrets redacted. Do not add `nmcli connection
  show` without a field filter if it would print the passphrase.
- Interface names actually used.
- The PMF mode in use. Procedure version 2 requires `ieee80211w=0`
  because that is the setting the adopted installer writes. Record it.
  Attempt 02 did not pre-approve that setting for procedure version 1.
- A diagnostic that a stopped profile was not active, or that the
  distribution `hostapd` unit is masked, is an observation. It is not by
  itself a failure of this case.

## Metrics

No RTT in this case. Persistence across reboot is TC-NET-003. Recovery
after a failed unit is not a criterion of this case.

## Acceptance criteria

1. The repository Pi installer, not a hand-started `hostapd` and not a
   follow-up `ip addr add`, is the access point. `voicestock-hostapd.service`
   is active and its log reports `AP-ENABLED`. The Wi-Fi interface is in
   AP mode at `192.168.50.1/24`. There is no default route via that
   interface. NetworkManager reports that interface unmanaged and is not
   connected to a Wi-Fi profile on it.
2. `ip -4 route` contains `192.168.50.0/24` on that interface. If Ethernet
   is up, its address is recorded and is not the VoiceStock subnet. That
   Ethernet route does not satisfy isolation.
3. PC: `voicestock-client` is active on the interface that was passed,
   that interface has `192.168.50.2/24`, gateway and DNS are empty,
   `ipv4.never-default` is `yes`, and the profile is bound to that
   interface name. The run does not fail with a device/connection MAC
   mismatch, and it does not fail by treating state `100 (connected)` as
   unmanaged.
4. PC: `ip -4 route show default` still names the Internet interface
   recorded in preparation, not the VoiceStock interface.
5. The PMF mode recorded for the access point is `ieee80211w=0`
   (disabled), which is the mode this procedure requires. No ping or
   application check is recorded as a pass of this case.

## Failure conditions

- A script exits with a failure: **FAILED**, with the transcript. Do not
  rerun with a different interface and overwrite the record. A corrected
  rerun is a new execution.
- The operator has to unmanaged the device by hand, edit a file under
  `/run`, or add the address with `ip addr add` after the installer:
  **FAILED**. Those steps were diagnostics in attempt 02.
- Country is not `AR`: **BLOCKED**.
- Fewer than two Wi-Fi interfaces on the PC: **BLOCKED**.
- The only way to continue is to pass the Internet interface: **FAILED**
  if the script was run that way; **BLOCKED** if the operator stopped.
- A pass of procedure version 2 claimed against attempt 01 or attempt 02:
  invalid. Those runs stay on procedure version 1.

## Recovery and cleanup

If the wrong PC interface was configured, follow the recovery in the setup
guide of the revision under test. Do not delete the prototype passphrase
from the repository as part of the test.

Previous incidents stay open until the campaign's review and retest
process closes them. A pass of this procedure does not close them.

## Limitations and exclusions

Local profiles do not prove that the PC and the Pi can see each other.
They do not prove Internet isolation, reboot persistence, recovery after
a failed unit, or long-term connection reliability. Reachability and
IPv4 isolation are TC-NET-002. Reboot is TC-NET-003. A technical pass of
this case is not **CLOSED_PASSED** while evidence or review is still open.
