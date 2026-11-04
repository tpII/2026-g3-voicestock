# ADR-0012: Evaluate hostapd for the VoiceStock access point

## Status

Proposed. Not accepted. This record does not supersede
[ADR-0010](0010-use-isolated-raspberry-pi-wifi-access-point.md). The
isolated Wi-Fi topology in ADR-0010 stays in force: the Raspberry Pi is
the access point of `VoiceStock`, the PC uses a second Wi-Fi interface,
addresses stay `192.168.50.1/24` and `192.168.50.2/24`, and the cell has
no DHCP, DNS, gateway, NAT, forwarding, or bridge.

No migration has been implemented. No campaign case has passed on this
proposal.

## Context

ADR-0010 fixes the network shape and leaves the access-point software
unspecified. The implementation that reached the hardware campaign was
NetworkManager on both machines (`scripts/setup_pi_access_point.sh` and
`scripts/setup_pc_voicestock_wifi.sh`).

[EX-TC-NET-001-20261103-01](../testing/raspberry-validation/executions/EX-TC-NET-001-20261103-01.md)
failed because the Pi script treated NetworkManager state `100 (connected)`
as unmanaged. That Pi check was corrected later. The correction is not
re-stated here as a new architecture.

[EX-TC-NET-001-20261103-02](../testing/raspberry-validation/executions/EX-TC-NET-001-20261103-02.md)
ran the updated Pi script. State detection, AP capability, the AR domain,
profile creation, and deactivation of the old client connection succeeded.
WPA2 activation did not. NetworkManager reported `supplicant-timeout`.
The Broadcom `brcmfmac` path reported a vendor-IE error `-52`, a key-setting
validation failure, and `AP-DISABLED`.

With PMF disabled, the NetworkManager profile activated, and the Arch
client still failed the 4-way handshake: the RSN element in message 3/4
advertised an additional WPA-PSK-SHA256 AKM suite that the Beacon did not.
The internal Broadcom cause is not identified. A smartphone password
warning is recorded only as an authentication symptom.

An experiment outside the repository stopped NetworkManager on `wlan0` and
ran `hostapd` (WPA2-PSK, CCMP, 2.4 GHz, channel 11, country AR, PMF
disabled). The smartphone and the Arch USB client authenticated. `wlan0`
had no address until a manual `ip addr add 192.168.50.1/24`. The operator
then confirmed ICMP. That ping is not TC-NET-002. Ethernet remained
connected, so isolation was not shown.

The evidence note is
[hostapd-evaluation.md](../testing/raspberry-validation/hostapd-evaluation.md).
A draft procedure for a later execution is
[TC-NET-001 procedure version 2 (proposal)](../testing/raspberry-validation/test-cases/TC-NET-001-procedure-v2-PROPOSAL.md).
Procedure version 1 is unchanged.

## Decision

No decision is accepted in this file.

The proposal, if it is later accepted, is:

- Keep ADR-0010's topology and addresses.
- Run the Raspberry Pi access point with `hostapd`, not with a
  NetworkManager hotspot profile.
- Keep NetworkManager from managing `wlan0` while `hostapd` owns it.
- Apply `192.168.50.1/24` with a persistent configuration that survives
  the start of `hostapd` and a reboot, with no gateway, no DNS, and no
  default route on `wlan0`.
- Leave the PC client on NetworkManager, after the PC script stops writing
  a transient MAC into `802-11-wireless.mac-address` and stops matching
  unmanaged state with the pattern `10*`.
- Treat PMF disabled as a known limit of the 3 November 2026 experiment,
  not as a silent default of the architecture. An accepted revision has
  to choose the PMF mode on purpose.
- Require new TC-NET-001, TC-NET-002, and TC-NET-003 executions. The manual
  experiment does not close them.

Until this status moves to Accepted, implementers keep the current
NetworkManager scripts, and the campaign keeps procedure version 1 for any
execution of those scripts.

## Alternatives considered

- **Stay on a NetworkManager hotspot only.** Attempt 02 did not produce a
  client that could complete WPA2 against that hotspot on this Pi. The
  alternative stays available if a later driver or profile change removes
  the RSN mismatch. It is not the path the experiment showed working.
- **Replace the isolated cell** (Ethernet, upstream client mode, NAT).
  Rejected here because ADR-0010 already rejected those shapes. This
  proposal does not reopen them.
- **Leave addressing as a manual `ip addr add`.** Rejected as an
  operational design. The experiment needed that command because nothing
  persistent configured the interface. A dedicated AP process does not
  assign the VoiceStock address by itself.

## Consequences

### If the proposal is accepted later

- AP mode and client mode are different programs. NetworkManager remains
  the PC client and must not also be the Pi access point on `wlan0`.
- Boot has to start `hostapd` and the static address without the operator
  sequence used on 3 November 2026.
- Campaign procedure version 1 cannot be reused as the pass procedure.
- PMF, channel, and regulatory domain become explicit `hostapd` settings
  with their own regression notes.

### What is true now

- ADR-0010 is the network decision.
- TC-NET-001 has two failed executions and is not closed.
- `hostapd` is a demonstrated diagnostic, not the repository setup.
- Disabled PMF, missing persistent IPv4, the PC MAC restriction, and the
  PC `10*` check are open defects or limits. They are not resolved by
  writing this ADR.

## Later campaign facts

This section does not change the status, the title, or the identifier.
This file stays **Proposed** and remains ADR-0012. It is not renumbered.
The accepted access-point process is
[ADR-0013](0013-run-the-voicestock-access-point-with-hostapd.md). That
record does not accept this proposal and does not change the failed
procedure-version-1 executions cited below.

`develop` at `485559c` (pull request #36) contains the `hostapd` installer.
[TC-NET-001](../testing/raspberry-validation/test-cases/TC-NET-001.md)
procedure version 2 is in force for new executions.
[EX-TC-NET-001-20261103-03](../testing/raspberry-validation/executions/EX-TC-NET-001-20261103-03.md)
is **PASSED_PENDING_DOCUMENTATION** for configuration only. Attempts 01 and
02 stay **FAILED** on procedure version 1.
[EX-TC-NET-002-20261103-01](../testing/raspberry-validation/executions/EX-TC-NET-002-20261103-01.md)
is **PASSED_PENDING_DOCUMENTATION** for bidirectional ICMP and IPv4
isolation. It is not closed.
[EX-TC-NET-003-20261103-01](../testing/raspberry-validation/executions/EX-TC-NET-003-20261103-01.md)
is **PASSED_PENDING_DOCUMENTATION** for reboot recovery under TC-NET-003
procedure version 2. Procedure version 1 of that case was not run. It is
not closed. The sentences under "What is true now" describe this file when
it was written. This section does not accept the proposal.
