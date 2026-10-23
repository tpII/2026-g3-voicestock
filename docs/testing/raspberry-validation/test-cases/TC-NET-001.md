# TC-NET-001 — Raspberry Pi access point configuration

- Status: DESIGNED
- Executions: none
- Procedure version: 1

## Objective

Bring up the documented VoiceStock Wi-Fi profiles and record that the local
configuration matches the setup guide. This case does not ping the other
host.

## Test level and type

Level: hardware validation of the local network configuration.

Type: functional. Reachability is TC-NET-002.

## Requirements and ClickUp traceability

- ClickUp: [LocalNetworkInfra-04](https://app.clickup.com/t/86e3jutyu).
- Requirement: the Pi is an isolated access point at `192.168.50.1/24` and
  the PC's dedicated Wi-Fi interface is `192.168.50.2/24`, as specified in
  [local network setup](../../../setup/local-network.md) and
  [ADR-0010](../../../decisions/0010-use-isolated-raspberry-pi-wifi-access-point.md).

## Source modules and documentation

- `scripts/setup_pi_access_point.sh`.
- `scripts/setup_pc_voicestock_wifi.sh`.
- `scripts/voicestock-network.conf` (do not print the passphrase).
- The setup guide's verification section. This case is the execution of
  that section after a baseline, not a second copy of the script manual.

## Preconditions and dependencies

- [TC-ENV-001](TC-ENV-001.md) has recorded `nmcli`, `ip`, and `iw reg get`
  before any script from this case runs.
- Raspberry Pi OS with NetworkManager and `iw`.
- The PC is Arch Linux with NetworkManager and two Wi-Fi interfaces, which
  is the guide's stated PC. If the lab PC is not that machine, stop and
  mark **BLOCKED**. Do not adapt the scripts inside the execution.
- Regulatory domain procedure: if `iw reg get` on the Pi does not show
  country `AR`, do not run the access-point script. The guide's
  `raspi-config` change and reboot are a separate execution that starts
  from a new baseline note. This execution records the country and stops
  at **BLOCKED** when it is not `AR`.

## Required hardware and software

- Raspberry Pi 3 built-in Wi-Fi. The interface name comes from
  `nmcli device status`, not from an assumption that it is `wlan0`.
- PC with the Internet Wi-Fi already associated, and a second Wi-Fi
  interface that does not own the default route.
- `sudo` on both machines for the setup scripts.
- Repository checkout on both machines so both scripts read the same
  `scripts/voicestock-network.conf`.

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

1. On the Pi, from the repository root, run the access-point script only
   after the country check passes. Pass the Wi-Fi interface name when the
   script requires it:

```bash
sudo bash scripts/setup_pi_access_point.sh
```

or:

```bash
sudo bash scripts/setup_pi_access_point.sh <PI_WIFI_INTERFACE>
```

2. On the Pi, run the read-only checks from the setup guide:

```bash
nmcli device status
nmcli connection show --active
ip -4 addr
ip -4 route
nmcli -g ipv4.gateway,ipv4.dns,ipv4.method,802-11-wireless.mode connection show voicestock-ap
```

3. On the PC, run:

```bash
sudo bash scripts/setup_pc_voicestock_wifi.sh <PC_VOICESTOCK_INTERFACE>
```

4. On the PC:

```bash
nmcli device status
nmcli connection show --active
ip -4 addr
ip -4 route
nmcli -g ipv4.gateway,ipv4.dns,ipv4.method,ipv4.never-default,connection.interface-name connection show voicestock-client
ip -4 route show default
```

Do not ping. Do not enable DHCP, NAT, forwarding, or a bridge. The scripts
themselves refuse several of those mistakes; if a script prints `FAILED`,
keep the transcript and stop.

## Observations and evidence

- Both transcripts with secrets redacted. The `-g` field lists above do
  not include the PSK. Do not add `nmcli connection show` without a field
  filter if it would print the passphrase.
- Interface names actually used.

## Metrics

No RTT in this case. Persistence across reboot is TC-NET-003.

## Acceptance criteria

1. Pi: `voicestock-ap` is the active profile on the Wi-Fi interface,
   `192.168.50.1/24` is on that interface, the `-g` query reports an empty
   gateway, an empty DNS list, method `manual`, and mode `ap`.
2. Pi: `ip -4 route` contains `192.168.50.0/24` on that interface and does
   not contain a default route via that interface.
3. PC: `voicestock-client` is active on the interface that was passed,
   that interface has `192.168.50.2/24`, the `-g` query reports an empty
   gateway, an empty DNS list, method `manual`, `never-default` `yes`, and
   the same interface name.
4. PC: `ip -4 route show default` still names the Internet interface
   recorded in preparation, not the VoiceStock interface.
5. No ping or application check is recorded as a pass of this case.

## Failure conditions

- A script exits with a failure: **FAILED**, with the transcript. Do not
  rerun with a different interface and overwrite the record. A corrected
  rerun is a new execution.
- Country is not `AR`: **BLOCKED**.
- Fewer than two Wi-Fi interfaces on the PC: **BLOCKED**.
- The only way to continue is to pass the Internet interface: **FAILED**
  if the script was run that way; **BLOCKED** if the operator stopped.

## Recovery and cleanup

If the wrong PC interface was configured, follow the recovery in the setup
guide (`nmcli connection down voicestock-client`, restore Internet, rerun
in a new execution). Do not delete the prototype passphrase from the
repository as part of the test.

## Limitations and exclusions

Local profiles do not prove that the PC and the Pi can see each other.
The setup guide states that explicitly. Isolation under traffic is
TC-NET-002.
