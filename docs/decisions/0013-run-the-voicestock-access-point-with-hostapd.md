# ADR-0013: Run the VoiceStock access point with hostapd

## Status

Accepted. Numbered ADR-0013 on 4 November 2026. This file was first added
as a second ADR-0012, beside the historical evaluation
[ADR-0012](0012-evaluate-hostapd-for-the-voicestock-access-point.md), which
stays **Proposed**. The decision, the rationale, and the consequences below
are otherwise unchanged.

This does not supersede
[ADR-0010](0010-use-isolated-raspberry-pi-wifi-access-point.md). The isolated
cell is unchanged: SSID `VoiceStock`, Raspberry Pi `192.168.50.1/24`, PC
`192.168.50.2/24`, no DHCP, DNS, gateway, NAT, forwarding, or bridge.

Physical validation of this installer is still pending. The manual session
below is the evidence that selected the configuration. It is not a closed
campaign result.

## Context

ADR-0010 fixes the topology and does not name the access-point program.
The first implementation used NetworkManager on the Pi
(`scripts/setup_pi_access_point.sh` creating `voicestock-ap`) and
NetworkManager on the PC.

On 3 November 2026 the NetworkManager access point did not produce a
working WPA2 cell on the project Raspberry Pi 3 (Broadcom `brcmfmac`).
Activation failed with a supplicant timeout. Kernel text included
`brcmf_vif_set_mgmt_ie: vndr ie set error : -52` and
`AP-DISABLED`. With PMF disabled, the profile came up, and the Arch client
still stopped during the 4-way handshake. The supplicant reported that the
RSN element in message 3/4 did not match the beacon. The handshake element
added a WPA-PSK-SHA256 AKM suite that the beacon did not advertise. The
component inside the Broadcom driver or firmware that inserts that suite
was not identified. A phone reported an incorrect password; that report
matches an authentication failure and does not show that the passphrase
differed.

An out-of-repository `hostapd` process then authenticated both the phone
and the Arch USB client (TP-Link TL-WN823N, `rtl8xxxu`). The working
configuration was WPA2-PSK, CCMP, 2.4 GHz, channel 11, country `AR`, and
PMF disabled (`ieee80211w=0`). `wlan0` had no IPv4 address until
`ip addr add 192.168.50.1/24`. The operator then confirmed that ping
succeeded. Ethernet stayed connected for SSH, so isolation was not shown.
No loss or RTT series was recorded.

The PC script also stored the USB adapter's temporary MAC in
`802-11-wireless.mac-address`. NetworkManager matches that property
against the permanent address, so the profile did not activate. The same
script still treated NetworkManager state `100 (connected)` as unmanaged.

## Decision

`hostapd` is the access-point process on the Raspberry Pi Wi-Fi interface.
NetworkManager must not manage that interface. NetworkManager stays in
service for Ethernet and for every other interface.

The static address `192.168.50.1/24` is applied by a oneshot unit after
`hostapd` has put the interface in AP mode. It is not applied by a second
network manager. The address unit removes only that address when it stops.
It does not add a gateway, DNS, or default route.

The installed hostapd file is generated on the Pi from
`scripts/voicestock-network.conf`, mode `600`, and is not committed. PMF
stays explicitly disabled (`ieee80211w=0`). That is a compatibility
workaround for this academic prototype: the working session used it, and
WPA-PSK-SHA256 was part of the failing handshake. Protected Management
Frames are therefore off. An attacker in radio range can forge
deauthentication and disassociation frames. The cell already uses a
passphrase stored in the repository. This is not a production security
boundary. WPA3 and WPA-PSK-SHA256 are not enabled.

The Arch client remains a NetworkManager profile bound with
`connection.interface-name`. It does not store a MAC restriction.

## Alternatives considered

- **Stay on a NetworkManager hotspot.** That path did not complete WPA2
  with the Arch client on this radio. It remains rejected unless a later
  hardware run shows the RSN mismatch is gone.
- **systemd-networkd or dhcpcd for the address.** Either one would be a
  second manager that can also claim Ethernet. The oneshot only runs
  `ip addr replace` on the access-point interface.
- **Leave the address as a manual command.** The experiment needed that
  command because nothing persistent configured the interface. The oneshot
  is that command, ordered after AP mode, including after a restart.
- **Bind the PC profile to the permanent USB MAC.** Unnecessary once the
  interface name is explicit. A transient address must not be written into
  the permanent-MAC property.

## Consequences

- Boot starts `voicestock-hostapd.service` and
  `voicestock-ap-address.service`. The distro `hostapd.service` is disabled
  so two access-point processes do not share the radio.
- NetworkManager learns the exception from
  `/etc/NetworkManager/conf.d/voicestock-unmanaged.conf`.
  `nmcli device set managed no` is only the current boot.
- Ethernet is not modified. Development SSH on `eth0` can remain.
- A fresh hardware run is still required after this change is on the Pi.
  The manual session does not close LocalNetworkInfra-04.
- Rollback is documented in the
  [local network setup](../setup/local-network.md). It stops the
  VoiceStock units and returns the Wi-Fi interface to NetworkManager. It
  does not delete Ethernet profiles.
