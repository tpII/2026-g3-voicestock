# Evaluation note: hostapd as the VoiceStock access point service

Status: evidence note for the out-of-repository experiment in
[EX-TC-NET-001-20261103-02](executions/EX-TC-NET-001-20261103-02.md).
That experiment is still a diagnostic. It is not a pass of procedure
version 1, and it is not
[EX-TC-NET-001-20261103-03](executions/EX-TC-NET-001-20261103-03.md).

Procedure version 2 is now the in-force text of
[TC-NET-001](test-cases/TC-NET-001.md). The installer attempt 03 ran is on
`develop` at `485559c` (pull request #36). This note is not rewritten to
describe that installer. ADR numbering on this branch is unchanged. The
campaign file
[ADR-0012](../../decisions/0012-evaluate-hostapd-for-the-voicestock-access-point.md)
stays **Proposed**.

The isolated cell is still the decision in
[ADR-0010](../../decisions/0010-use-isolated-raspberry-pi-wifi-access-point.md):
SSID `VoiceStock`, Pi `192.168.50.1/24`, PC `192.168.50.2/24`, no DHCP,
DNS, gateway, NAT, forwarding, or bridge, and the PC default route kept
on the Internet interface. This note does not replace that decision.

The proposed record, still **Proposed** on this branch, is
[ADR-0012](../../decisions/0012-evaluate-hostapd-for-the-voicestock-access-point.md).
The observations in this note are
[EX-TC-NET-001-20261103-02](executions/EX-TC-NET-001-20261103-02.md).

## Original approach

Procedure version 1 of [TC-NET-001](test-cases/TC-NET-001.md) configures
both ends with NetworkManager:

- `scripts/setup_pi_access_point.sh` creates `voicestock-ap` in AP mode.
- `scripts/setup_pc_voicestock_wifi.sh` creates `voicestock-client` on a
  dedicated Wi-Fi interface.

Attempt 01 never reached activation. The Pi script treated
`100 (connected)` as unmanaged. Attempt 02 ran after the operator reported
that correction on `develop`. The script passed that check.

## What failed under NetworkManager

Activation of `voicestock-ap` failed with `supplicant-timeout`. The
Broadcom `brcmfmac` path reported `brcmf_vif_set_mgmt_ie: vndr ie set
error : -52`, `key setting validation failed`, and `AP-DISABLED`.

Disabling PMF (`802-11-wireless-security.pmf 1`) let the NetworkManager
profile come up at `192.168.50.1/24` with WPA2-PSK, no gateway, and no
DNS. The Arch client still disconnected during the 4-way handshake.
Message 3/4 carried an extra WPA-PSK-SHA256 AKM suite that the Beacon RSN
element did not advertise (`IE_DIFFERENT`, reason 17). A smartphone
reported an incorrect password. That report is an authentication symptom,
not proof of a wrong passphrase. Disabling PMF on the client did not
repair the handshake.

The exact fault inside the Broadcom driver or firmware is not identified.

## What the hostapd experiment showed

Outside the repository, with NetworkManager off `wlan0`, a foreground
`hostapd` process using WPA2-PSK, CCMP, 2.4 GHz, channel 11, regulatory
domain AR, and PMF disabled reached `AP-ENABLED`. The smartphone completed
`EAPOL-4WAY-HS-COMPLETED`. The Arch USB client (`rtl8xxxu` on
`wlp0s20f0u4`) authenticated as well. Both stations were authorized,
authenticated, and associated.

`wlan0` had no IPv4 address until:

```bash
sudo ip addr add 192.168.50.1/24 dev wlan0
```

The operator then confirmed that ping succeeded. No RTT or loss series was
recorded. Ethernet `eth0` was still up, so isolation was not proven.

## Why a dedicated access-point service is under consideration

NetworkManager's hotspot activation and its WPA2 element negotiation did
not produce a client that could join this radio, even after the
state-detection fix and after PMF was disabled. `hostapd` completed the
same WPA2-PSK policy with the clients that failed against NetworkManager.
The team is therefore considering `hostapd` as the process that owns AP
mode, while the addressing rules of ADR-0010 stay in place.

That consideration was not an implemented migration when this note was
written. The later installer on `develop` at `485559c` is a different
artifact. This section does not describe it.

## Responsibilities

| Concern | Owner under the experiment | What must become persistent |
| --- | --- | --- |
| Beacon, WPA2-PSK, CCMP, channel, country, PMF | `hostapd` | A configuration owned by the product, not a file left only under `/run`. |
| `wlan0` not claimed by a NetworkManager Wi-Fi profile at the same time | NetworkManager unmanaged, or an equivalent explicit split | The setup must apply this split on boot without a manual sequence. |
| `192.168.50.1/24`, no gateway, no DNS, no default route on `wlan0` | Address configuration beside `hostapd` | The experiment needed a manual `ip addr add`. A reboot-safe method is still required. |
| PC client at `192.168.50.2/24`, default route unchanged | NetworkManager on the PC | The PC script still has the transient-MAC restriction and the `10*` state check. |
| Internet isolation | Not owned by the access-point process | Ethernet must be absent, and TC-NET-002 must measure it. |

PMF disabled is a limit of every association in attempt 02, including the
successful `hostapd` run. This note does not accept disabled PMF as the
final security setting. A later decision has to say whether PMF stays off
and which clients that choice excludes.

## Remaining risks

- The Broadcom failure mode is not root-caused. `hostapd` succeeded once,
  in a foreground session, on one channel.
- The passphrase and the temporary `hostapd` file were not archived. The
  next implementation must keep the passphrase out of the campaign records.
- Static IPv4 was not persistent.
- Two clients authenticated. ICMP was operator-confirmed only, with no
  measured both-direction series.
- Isolation was not tested.
- Reboot behavior was not tested.
- The PC script can still reject `100 (connected)` and can still pin
  `802-11-wireless.mac-address` to a temporary MAC.

## Regression required before a pass

A future execution, under a procedure that names `hostapd` and that is
not procedure version 1, has to show at least:

1. The Pi script or unit path does not treat state `100` as unmanaged, and
   the PC script does not either.
2. The PC profile binds the interface without a permanent-MAC restriction
   taken from a temporary address.
3. `hostapd` reaches `AP-ENABLED` with the documented country and channel
   policy, and NetworkManager is not also mastering `wlan0`.
4. `192.168.50.1/24` is present without a manual `ip addr add` after the
   service starts, with empty gateway and DNS and with no default route on
   `wlan0`.
5. The Arch USB client and, when used, a second client complete WPA2.
6. PMF is whatever the adopted procedure requires, recorded explicitly.
7. TC-NET-002 and TC-NET-003 are run as their own cases. A manual ping in
   this note does not substitute for them.

[Procedure version 2](test-cases/TC-NET-001.md) is in force for executions
from attempt 03 onward. The proposal file is retained as the draft that
was adopted. It does not regrade attempt 02.
[EX-TC-NET-001-20261103-03](executions/EX-TC-NET-001-20261103-03.md) is the
configuration execution of the repository installer. It does not replace
the observations in this note, it does not measure ICMP, and it does not
run TC-NET-002 or TC-NET-003.
[EX-TC-NET-002-20261103-01](executions/EX-TC-NET-002-20261103-01.md) is a
later execution of TC-NET-002. It does not rewrite this note.
