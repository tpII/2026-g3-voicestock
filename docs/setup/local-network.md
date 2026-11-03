# VoiceStock local network setup

How to bring up the isolated VoiceStock Wi-Fi cell between the Raspberry Pi 3
and the PC, check the local configuration, and recover from a failed install.

Why this topology was chosen is the
[local network strategy](../research/local-network-strategy.md). The topology
decision is [ADR-0010](../decisions/0010-use-isolated-raspberry-pi-wifi-access-point.md).
The access-point process is
[ADR-0012](../decisions/0012-run-the-voicestock-access-point-with-hostapd.md).
This page is the procedure.

Application traffic is a separate feature, `RaspberryPiPCCommunication`.
Endpoints, payloads, speech-to-text, and language models are not part of this
guide. Once the addresses below are in place, that feature is documented in
the
[Raspberry Pi–PC communication interface](../interfaces/pc-communication.md).
The operator page that the PC browser opens on the Pi is the
[web setup guide](pi-web.md).

A development path through Tailscale does not replace this cell, and it does
not close the hardware checks at the end of this page.

The setup scripts check the machine they run on. They do not ping the other
host, and they do not test Internet access. A manual `hostapd` session on
3 November 2026 authenticated a phone and the Arch USB client, and the
operator then confirmed ping after assigning `192.168.50.1/24`. That session
is the configuration this installer reproduces. It is not a closed
LocalNetworkInfra-04 result. The installer itself still needs a hardware run.

## Expected topology

```text
                         Internet
                            |
                      external router
                            |
                       PC Wi-Fi #1
                            |
                           PC
                            |
                       PC Wi-Fi #2
                            |
                     VoiceStock Wi-Fi
                            |
                    Raspberry Pi 3
                      hostapd AP
```

| Role | Value |
| --- | --- |
| SSID | `VoiceStock` |
| Security | WPA2-PSK, CCMP, PMF disabled |
| Band | 2.4 GHz, channel 11 |
| Regulatory domain | `AR` |
| Network | `192.168.50.0/24` |
| Raspberry Pi 3 | `192.168.50.1/24` |
| PC VoiceStock Wi-Fi | `192.168.50.2/24` |

The PC Internet Wi-Fi interface keeps its own DHCP, gateway, DNS, and default
route. The VoiceStock Wi-Fi interface has none of those. The Raspberry Pi is
only the access point. It does not join another Wi-Fi network and it has no
Internet path in the final deployment.

```text
PC
├── Wi-Fi #1
│   └── Internet
│         default route, gateway, DNS
│
└── Wi-Fi #2
    └── 192.168.50.2/24
          |
          | SSID VoiceStock
          |
        192.168.50.1/24
            Raspberry Pi 3 hostapd
```

```text
default route    -> Internet Wi-Fi
192.168.50.0/24  -> VoiceStock Wi-Fi
```

Ethernet on the Pi, when it is connected at `192.168.1.100/24` for
development SSH, is not part of this cell. The access-point script does not
modify or deactivate Ethernet.

## Why hostapd replaced the NetworkManager access point

The first Pi script created a NetworkManager profile named `voicestock-ap`.
On 3 November 2026 that profile did not stay up as a WPA2 access point the
Arch client could join. NetworkManager reported a supplicant timeout. With
PMF turned off, the profile activated, and the 4-way handshake still failed:
message 3/4 advertised a WPA-PSK-SHA256 AKM suite that the beacon did not.
The Broadcom driver or firmware cause of that extra suite was not identified.

A foreground `hostapd` process with WPA2-PSK, CCMP, channel 11, country
`AR`, and PMF disabled (`ieee80211w=0`) reached `AP-ENABLED` and completed
the handshake for both clients. The address was missing until
`ip addr add 192.168.50.1/24 dev wlan0`. This procedure installs that
configuration so it survives reboot. It does not switch to an open network,
WPA3, or WPA-PSK-SHA256.

PMF disabled is a compatibility limit. Management frames are not
integrity-protected, so a station in radio range can forge deauthentication.
The prototype passphrase already lives in the repository. Treat the cell as
an academic link, not a production boundary.

## Fixed settings and the prototype passphrase

SSID, addresses, and the WPA2 passphrase are defined once, in
[`scripts/voicestock-network.conf`](../../scripts/voicestock-network.conf).
Both setup scripts source that file. The Pi script writes the passphrase
into `/etc/hostapd/voicestock.conf` with mode `600` and root ownership.
That installed file is not committed. Do not copy the passphrase into
another script, a unit file, a log, or this guide.

That passphrase is committed on purpose for the current academic prototype.
It is not a production secret. API keys and other credentials stay out of
the repository. Before any production or final deployment, remove this
passphrase from the repository.

## What you need

- Raspberry Pi 3 running Raspberry Pi OS, with NetworkManager (`nmcli`),
  `iw`, `systemd`, and the `hostapd` package. NetworkManager keeps Ethernet.
  It must not also run the access point.
- `systemd-networkd` and `dhcpcd` must be inactive. The script stops if
  either is active, because either one can take the same interface.
- A PC running Arch Linux, with NetworkManager (`nmcli`) and two Wi-Fi
  interfaces. One of them must already be the Internet connection. The other
  is dedicated to VoiceStock.
- The VoiceStock repository on both machines, so the scripts can read
  `scripts/voicestock-network.conf`.

Install `hostapd` on the Pi before the access-point script. The script does
not install packages and does not reboot:

```bash
sudo apt-get install hostapd
```

A previous Ethernet profile named `voicestock-ethernet`, if it is still stored
on a machine from the earlier architecture, is not used. Remove it manually
when you no longer need it:

```bash
nmcli connection delete voicestock-ethernet
```

The scripts do not delete it.

## Regulatory domain

The Raspberry Pi Wi-Fi regulatory domain must match the country where the
access point operates. For this project that country is Argentina, `AR`.
The access-point script checks the domain and stops if it is not `AR`. It
does not change the domain. `hostapd` is also configured with
`country_code=AR`.

Check:

```bash
iw reg get
```

The first `country` line must be `AR`. On Raspberry Pi OS, set it and reboot:

```bash
sudo raspi-config nonint do_wifi_country AR
sudo reboot
```

Run `iw reg get` again after reboot. Continue with the access-point script
only when the country is `AR`.

## Raspberry Pi: access point

The Pi script is an installer. Running it again updates the same files and
restarts the same units. It does not create a second service or a second
address.

It selects the Wi-Fi interface (or uses the name you pass), refuses
Ethernet, checks Access Point capability and country `AR`, then:

1. Writes `/etc/hostapd/voicestock.conf` (mode `600`).
2. Writes `/usr/local/lib/voicestock/ap-address.sh`.
3. Writes `/etc/NetworkManager/conf.d/voicestock-unmanaged.conf` so
   NetworkManager ignores that Wi-Fi interface after reboot.
4. Stops the old `voicestock-ap` profile if it exists, and turns off its
   autoconnect. The profile is kept.
5. Turns autoconnect off on other Wi-Fi profiles and deactivates any other
   profile that is up on the access-point interface. Those profiles are kept.
   Ethernet profiles are not modified.
6. Reloads NetworkManager configuration and marks the Wi-Fi interface
   unmanaged for this boot. It does not restart NetworkManager.
7. Installs `voicestock-hostapd.service` and
   `voicestock-ap-address.service`, disables the distro `hostapd.service`
   if that unit exists, and starts the VoiceStock units.
8. Reports success only when `hostapd` is active, the interface is in AP
   mode, `192.168.50.1/24` is present, NetworkManager is not managing the
   interface, and the interface has no default route.

`hostapd` owns association and WPA2. The address unit waits until the
interface is in AP mode, then runs `ip addr replace`. On stop it deletes
only `192.168.50.1/24`. Restarting `hostapd` restarts the address unit.
Neither unit enables DHCP, NAT, forwarding, or a bridge.

From the repository root, after `hostapd` is installed:

```bash
sudo bash scripts/setup_pi_access_point.sh
```

Or, when the interface must be named:

```bash
sudo bash scripts/setup_pi_access_point.sh wlan0
```

`wlan0` is an example. Use the Wi-Fi device from `nmcli device status`.

The script refuses to run without root. If the Pi has no Wi-Fi interface,
or more than one, pass the interface. It never configures Ethernet.

## Arch Linux PC: VoiceStock Wi-Fi

Leave the Internet Wi-Fi connected. Identify both interfaces before changing
anything:

```bash
nmcli device status
ip -4 route
```

The Wi-Fi device named on the `default` route is the Internet interface. Do
not pass that device to the VoiceStock script. Pass the other Wi-Fi device.

```bash
sudo bash scripts/setup_pc_voicestock_wifi.sh wlp0s20f0u4
```

Replace `wlp0s20f0u4` with the VoiceStock interface. The argument is
required. The script does not choose a device, and it stops if the machine
does not show at least two Wi-Fi interfaces.

It also stops, without writing a profile, when that interface owns the
default route or already has an IPv4 gateway. That is the Internet path.
If `voicestock-client` is already the active profile on the named interface,
the script updates it in place so a later run can clear a gateway it finds
there.

The script creates or updates one persistent profile, `voicestock-client`,
bound to that interface name:

- infrastructure mode, 2.4 GHz, SSID `VoiceStock`, WPA2-PSK;
- static address `192.168.50.2/24`;
- no gateway, no DNS, IPv6 disabled, `ipv4.never-default`;
- autoconnect enabled;
- `802-11-wireless.mac-address` empty.

The profile is not matched to the address currently in
`/sys/class/net/<interface>/address`. On the project USB adapter that
address was temporary, while NetworkManager compares
`802-11-wireless.mac-address` with the permanent device address. A previous
profile that stored the temporary MAC is cleared on the next run.

State `100 (connected)` is managed. The script rejects only unmanaged state
`10`. It does not use a prefix match that also rejects `100`.

Running it again updates the same profile. Other connection profiles,
including the Internet Wi-Fi profile and Docker bridges, are not modified.

## Verification

These commands inspect the local configuration. They do not prove that the
PC and the Raspberry Pi can reach each other.

On the Raspberry Pi:

```bash
systemctl is-active voicestock-hostapd.service voicestock-ap-address.service
systemctl is-enabled voicestock-hostapd.service
iw dev wlan0 info
ip -4 addr show dev wlan0
ip -4 route
nmcli device status
```

Expected shape:

```text
voicestock-hostapd.service        active
voicestock-ap-address.service     active
wlan0                             type AP
wlan0                             192.168.50.1/24
route                             192.168.50.0/24 dev wlan0
route                             no default via wlan0
nmcli                             wlan0 unmanaged
```

Do not print `/etc/hostapd/voicestock.conf`. It contains the passphrase.
To check the non-secret lines:

```bash
sudo awk -F= '$1 != "wpa_passphrase" { print }' /etc/hostapd/voicestock.conf
```

That output should include `wpa=2`, `wpa_key_mgmt=WPA-PSK`,
`rsn_pairwise=CCMP`, `ieee80211w=0`, `hw_mode=g`, `channel=11`, and
`country_code=AR`.

On the PC:

```bash
nmcli device status
nmcli connection show --active
ip -4 addr
ip -4 route show default
nmcli -g ipv4.gateway,ipv4.dns,ipv4.method,ipv4.never-default,connection.interface-name,802-11-wireless.mac-address connection show voicestock-client
```

`192.168.50.2/24` is on the interface you passed. Gateway, DNS, and
`mac-address` are empty. The method is `manual`, `never-default` is `yes`,
and the interface name is the one you passed. The `default` route still
names the Internet Wi-Fi interface.

## Startup sequence

1. On the Raspberry Pi, confirm `iw reg get` shows country `AR`.
2. Install `hostapd` if `command -v hostapd` fails.
3. On the Pi, from the repository root, run
   `sudo bash scripts/setup_pi_access_point.sh` (add the interface name if
   the script asks for it).
4. Confirm the two VoiceStock units are active and the Pi address is
   `192.168.50.1/24`.
5. On the PC, with Internet Wi-Fi already connected, run `nmcli device status`
   and `ip -4 route`. Note which Wi-Fi interface owns the default route.
6. Run `sudo bash scripts/setup_pc_voicestock_wifi.sh` with the other Wi-Fi
   interface.
7. Confirm `192.168.50.2/24` is on that interface and the default route is
   still the Internet interface.
8. Leave ping, isolation, and reboot evidence for a new hardware execution.
   Do not record them as done from this procedure alone.

After a later reboot the units are enabled, so `hostapd` and the address
should return without running the script again. That boot behavior is
configured here and is not yet demonstrated on the board.

## Diagnose a failure

```bash
systemctl status voicestock-hostapd.service --no-pager
systemctl status voicestock-ap-address.service --no-pager
journalctl -u voicestock-hostapd.service -b --no-pager
iw dev wlan0 info
ip -4 addr show dev wlan0
nmcli -g GENERAL.STATE device show wlan0
```

`journalctl` must not be pointed at the configuration file. A successful
`hostapd` log includes `AP-ENABLED`. The address unit fails if the
interface never reaches `type AP`, or if a default route appears on it.

`nmcli device status` should show the Wi-Fi interface as unmanaged and the
Ethernet interface still connected. If Ethernet changed, use the local
console. The script's recovery text does not restart NetworkManager.

## Recover the previous Wi-Fi client

Ethernet SSH is the safe path. The script does not reboot the Pi. This
sequence stops only the VoiceStock access point and returns the Wi-Fi
interface to NetworkManager. It does not delete Ethernet profiles, Docker
networks, or unrelated Wi-Fi profiles.

```bash
sudo systemctl disable --now voicestock-hostapd.service voicestock-ap-address.service
sudo ip addr del 192.168.50.1/24 dev wlan0 || true
sudo rm -f /etc/NetworkManager/conf.d/voicestock-unmanaged.conf
sudo nmcli general reload
sudo nmcli device set wlan0 managed yes
```

Replace `wlan0` with the interface the installer used.

`nmcli device set managed no` alone is lost on reboot. The
`voicestock-unmanaged.conf` file is what keeps NetworkManager away after
reboot, so recovery removes that file and reloads NetworkManager.

The old `voicestock-ap` profile, if the earlier installer created it, is
left in place with autoconnect disabled. Do not bring it up if you are
returning to a normal client. To join a previous client network again,
turn autoconnect back on for that one profile and activate it:

```bash
nmcli connection modify netplan-wlan0-WiFi-Arriba connection.autoconnect yes
nmcli connection up netplan-wlan0-WiFi-Arriba
```

Use the profile name that `nmcli connection show` lists. Do not delete
`netplan-eth0` or any other Ethernet profile.

A partial install can leave the units disabled and the interface unmanaged.
The commands above are enough to get NetworkManager back. Then fix the
reported error and run `sudo bash scripts/setup_pi_access_point.sh` again.
Re-running does not add a second address or a second unit.

## Troubleshooting

### The access point is not visible

Confirm both units are active and `iw dev wlan0 info` shows `type AP`.
Confirm `iw reg get` shows `AR`. Re-run
`sudo bash scripts/setup_pi_access_point.sh` from the repository root.
The script does not report success when the units are only installed.

### The PC adapter does not connect

Confirm `hostapd` is active first. Then confirm the PC command named the
dedicated interface, not the Internet one. Re-run the PC script with that
same interface. A failure about the passphrase means
`scripts/voicestock-network.conf` on the PC is not the file the Pi
installed. Do not type a different password into NetworkManager. Update
the single conf file and run both scripts again.

If NetworkManager says the device MAC and the connection MAC do not match,
the profile still has a stale `802-11-wireless.mac-address`. Re-run the
PC script. It clears that property.

### The wrong Wi-Fi interface was selected

On the PC, the script will not start if that interface owns the default
route or has a gateway, unless `voicestock-client` is already the active
profile there. If a previous run used the wrong interface, disconnect that
profile, restore Internet on the correct interface, and run the script
again with the dedicated VoiceStock interface:

```bash
nmcli connection down voicestock-client
sudo bash scripts/setup_pc_voicestock_wifi.sh <voice-stock-interface>
```

The profile is bound to the interface name you pass. It does not follow a
randomized MAC onto another adapter.

### The cell is gone after reboot

On the Pi:

```bash
systemctl is-enabled voicestock-hostapd.service voicestock-ap-address.service
systemctl status voicestock-hostapd.service --no-pager
nmcli -g GENERAL.STATE device show wlan0
```

Both units should be enabled. `wlan0` should be unmanaged. Another Wi-Fi
profile with autoconnect still enabled can take the radio if NetworkManager
manages it again. The setup script turns autoconnect off on those Wi-Fi
profiles. Run the Pi script again. That restarts the same units.

### The PC loses Internet

Internet stays on the Wi-Fi interface that is not passed to the script. List
the default route:

```bash
ip -4 route show default
```

That line must name the Internet interface. If it names the VoiceStock
interface, `voicestock-client` is wrong: `ipv4.never-default` should be
`yes` and the profile should have no gateway. Run the PC script again for
the VoiceStock interface and check the route again. If the Internet
interface itself is disconnected, reconnect it with NetworkManager. The
VoiceStock script does not join or repair that network.

### NetworkManager reports an unmanaged Wi-Fi interface on the PC

The PC script stops before it writes the profile. Mark that device managed,
then run the script again. Use the VoiceStock interface, not the Internet
interface:

```bash
sudo nmcli device set wlp0s20f0u4 managed yes
sudo bash scripts/setup_pc_voicestock_wifi.sh wlp0s20f0u4
```

On the Pi, unmanaged is the required state while `hostapd` is the access
point. Do not mark the Pi Wi-Fi interface managed unless you are following
[Recover the previous Wi-Fi client](#recover-the-previous-wi-fi-client).

## Do not

- Do not enable NAT or masquerading.
- Do not enable DHCP on the VoiceStock network.
- Do not enable IP forwarding for this cell.
- Do not bridge the VoiceStock interface to any other interface.
- Do not connect the Raspberry Pi to the Internet through VoiceStock, and
  do not make the VoiceStock radio a Wi-Fi client of another network while
  the access point is the deployed configuration.
- Do not put a gateway, a DNS server, or a default route on the VoiceStock
  Wi-Fi interface.
- Do not pass the PC's Internet Wi-Fi interface to
  `setup_pc_voicestock_wifi.sh`.
- Do not restart NetworkManager or reboot the Pi as part of the installer.
- Do not disable NetworkManager globally.
- Do not change `192.168.50.1` or `192.168.50.2` without changing
  [`scripts/voicestock-network.conf`](../../scripts/voicestock-network.conf)
  and the [local network strategy](../research/local-network-strategy.md).
- Do not print or commit `/etc/hostapd/voicestock.conf`.

## Before a demo

- [ ] Raspberry Pi regulatory domain is `AR`
- [ ] `voicestock-hostapd.service` is active and enabled
- [ ] The Pi Wi-Fi interface is in AP mode at `192.168.50.1/24`
- [ ] That interface has no gateway, no DNS, and no default route
- [ ] NetworkManager is not managing that interface
- [ ] Ethernet, if used for SSH, was left connected
- [ ] The PC VoiceStock interface was passed explicitly
- [ ] `voicestock-client` is active and that interface is `192.168.50.2/24`
- [ ] The client profile has an empty MAC restriction
- [ ] The PC default route is still the Internet Wi-Fi interface
- [ ] The VoiceStock interface has no gateway and no DNS

LocalNetworkInfra-04 is still open. The items below are not demonstrated by
the installer or by the 3 November manual session's lack of a measured ping
log:

- the PC can reach the Raspberry Pi, with a recorded sample;
- the Raspberry Pi can reach the PC, with a recorded sample;
- the PC still has Internet through its Internet Wi-Fi adapter after the
  VoiceStock link is up;
- the Raspberry Pi has no Internet access when Ethernet is disconnected;
- the configuration survives reboot on the project board.
