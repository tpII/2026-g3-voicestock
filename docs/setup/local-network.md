# VoiceStock local network setup

How to bring up the isolated VoiceStock Wi-Fi cell between the Raspberry Pi 3
and the PC, check the local configuration, and recover from the usual setup
mistakes.

Why this topology was chosen, including the earlier Ethernet plan, is the
[local network strategy](../research/local-network-strategy.md). The decision
record is [ADR-0004](../decisions/0004-use-isolated-raspberry-pi-wifi-access-point.md).
This page is the procedure.

Application traffic is a separate feature, `RaspberryPiPCCommunication`.
Endpoints, payloads, speech-to-text, language models, and the web application
are not part of this guide. Once the addresses below are in place, that
feature is documented in the
[Raspberry Pi–PC communication interface](../interfaces/pc-communication.md).

The setup scripts check the machine they run on. They do not ping the other
host, and they do not test Internet access. That physical check belongs to
LocalNetworkInfra-04 and has not been done.

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
                         AP mode
```

| Role | Value |
| --- | --- |
| SSID | `VoiceStock` |
| Security | WPA2-PSK |
| Band | 2.4 GHz |
| Network | `192.168.50.0/24` |
| Raspberry Pi 3 | `192.168.50.1/24` |
| PC VoiceStock Wi-Fi | `192.168.50.2/24` |

The PC Internet Wi-Fi interface keeps its own DHCP, gateway, DNS, and default
route. The VoiceStock Wi-Fi interface has none of those. The Raspberry Pi is
only the access point. It does not join another Wi-Fi network and it has no
Internet path.

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
            Raspberry Pi 3 access point
```

```text
default route    -> Internet Wi-Fi
192.168.50.0/24  -> VoiceStock Wi-Fi
```

## Fixed settings and the prototype passphrase

SSID, addresses, and the WPA2 passphrase are defined once, in
[`scripts/voicestock-network.conf`](../../scripts/voicestock-network.conf).
Both setup scripts source that file. Do not copy the passphrase into another
script or into this guide.

That passphrase is committed on purpose for the current academic prototype.
It is not a production secret. API keys and other credentials stay out of the
repository. Before any production or final deployment, remove this passphrase
from the repository. This setup does not use environment variables, a vault,
or an interactive password prompt.

## What you need

- Raspberry Pi 3 running Raspberry Pi OS, with NetworkManager (`nmcli`) and
  `iw`.
- A PC running Arch Linux, with NetworkManager (`nmcli`) and two Wi-Fi
  interfaces. One of them must already be the Internet connection. The other
  is dedicated to VoiceStock.
- The VoiceStock repository on both machines, so the scripts can read
  `scripts/voicestock-network.conf`.

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
does not change the domain.

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

The Pi script creates or updates one persistent profile, `voicestock-ap`, on
the Pi's Wi-Fi interface:

- mode access point, 2.4 GHz, SSID `VoiceStock`, WPA2-PSK;
- static address `192.168.50.1/24`;
- no gateway, no DNS, IPv6 disabled, `ipv4.never-default`;
- autoconnect enabled, so the profile survives reboot.

If the Pi has exactly one Wi-Fi interface, the script can select it. If it
has none, or more than one, pass the interface. It never configures Ethernet.

From the repository root:

```bash
sudo bash scripts/setup_pi_access_point.sh
```

Or, when the interface must be named:

```bash
sudo bash scripts/setup_pi_access_point.sh wlan0
```

`wlan0` is an example. Use the Wi-Fi device from `nmcli device status`.

The script refuses to run without root. It checks that the device is Wi-Fi,
that NetworkManager manages it, and that it can report Access Point mode.
Running it again updates `voicestock-ap`. It does not create a second
profile.

Other Wi-Fi profiles on the Pi have autoconnect turned off so the radio does
not join another network after reboot. Those profiles are not deleted. A
manual client connection replaces the access point until `voicestock-ap` is
activated again.

The script does not enable DHCP, NAT, forwarding, or a bridge, and it does
not install `hostapd` or `dnsmasq`.

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
sudo bash scripts/setup_pc_voicestock_wifi.sh wlan1
```

Replace `wlan1` with the VoiceStock interface. The argument is required. The
script does not choose a device, and it stops if the machine does not show at
least two Wi-Fi interfaces.

It also stops, without writing a profile, when that interface owns the
default route or already has an IPv4 gateway. That is the Internet path.
If `voicestock-client` is already the active profile on the named interface,
the script updates it in place so a later run can clear a gateway it finds
there.

The script creates or updates one persistent profile, `voicestock-client`,
bound to that interface and to its MAC address:

- infrastructure mode, 2.4 GHz, SSID `VoiceStock`, WPA2-PSK;
- static address `192.168.50.2/24`;
- no gateway, no DNS, IPv6 disabled, `ipv4.never-default`;
- autoconnect enabled.

Running it again updates the same profile. Other connection profiles,
including the Internet Wi-Fi profile, are not modified.

## Verification

These commands inspect the local configuration. They do not prove that the
PC and the Raspberry Pi can reach each other. That remains
LocalNetworkInfra-04.

On both machines:

```bash
nmcli device status
nmcli connection show --active
ip -4 addr
ip -4 route
```

Expected shape:

```text
PC Internet Wi-Fi:
    default route -> Internet

PC VoiceStock Wi-Fi:
    192.168.50.2/24
    no gateway
    no DNS

Raspberry Pi:
    AP VoiceStock
    192.168.50.1/24
    no gateway
    no DNS
```

On the Raspberry Pi, `192.168.50.1/24` is on the access-point interface,
`voicestock-ap` is the active profile on that interface, and `ip -4 route`
has `192.168.50.0/24` on that interface and no `default` route via it.

```bash
nmcli -g ipv4.gateway,ipv4.dns,ipv4.method,802-11-wireless.mode connection show voicestock-ap
```

That should report an empty gateway, an empty DNS list, `manual`, and `ap`.

On the PC, `192.168.50.2/24` is on the interface you passed, `voicestock-client`
is active on that interface, and the `default` route still names the Internet
Wi-Fi interface.

```bash
nmcli -g ipv4.gateway,ipv4.dns,ipv4.method,ipv4.never-default,connection.interface-name connection show voicestock-client
```

Gateway and DNS are empty, the method is `manual`, `never-default` is `yes`,
and the interface name is the one you passed.

## Startup sequence

1. On the Raspberry Pi, confirm `iw reg get` shows country `AR`.
2. On the Pi, from the repository root, run
   `sudo bash scripts/setup_pi_access_point.sh` (add the interface name if
   the script asks for it).
3. Confirm `voicestock-ap` is active and the Pi address is `192.168.50.1/24`.
4. On the PC, with Internet Wi-Fi already connected, run `nmcli device status`
   and `ip -4 route`. Note which Wi-Fi interface owns the default route.
5. Run `sudo bash scripts/setup_pc_voicestock_wifi.sh` with the other Wi-Fi
   interface.
6. Confirm `192.168.50.2/24` is on that interface and the default route is
   still the Internet interface.
7. Leave the ping, reboot, and application checks for LocalNetworkInfra-04.
   Do not record them as done from this procedure alone.

## Troubleshooting

### The Raspberry Pi access point is not visible

Confirm the script finished without a `FAILED` line and that
`nmcli connection show --active` lists `voicestock-ap`. Confirm
`iw reg get` shows `AR`. A wrong country can keep the cell from starting or
can reject the channel NetworkManager picked. The script does not set a
fixed channel; it only forces the 2.4 GHz band.

Re-run `sudo bash scripts/setup_pi_access_point.sh` from the repository
root. Re-running updates `voicestock-ap`.

### The PC VoiceStock adapter does not connect

Confirm the Pi access point is active first. Then confirm the PC command
named the dedicated interface, not the Internet one. Re-run the PC script
with that same interface. A `FAILED` line about the passphrase means
`scripts/voicestock-network.conf` on the PC is not the same file the Pi
used. Do not type a different password into NetworkManager. Update the
single conf file and run both scripts again.

### The wrong Wi-Fi interface was selected

On the PC, the script will not start if that interface owns the default
route or has a gateway, unless `voicestock-client` is already the active
profile there. If a previous run used the wrong interface and
`voicestock-client` is active on it, do not leave it there. Disconnect that
profile, restore the Internet connection on the correct interface, and run
the script again with the dedicated VoiceStock interface:

```bash
nmcli connection down voicestock-client
sudo bash scripts/setup_pc_voicestock_wifi.sh <voice-stock-interface>
```

The profile is bound to the interface name and to that interface's MAC, so
it does not move onto the Internet adapter by itself.

### `voicestock-ap` is inactive after reboot

On the Pi:

```bash
nmcli connection show voicestock-ap
nmcli device status
```

The profile should name the Wi-Fi device, with autoconnect enabled. Another
Wi-Fi profile with autoconnect still enabled can take the radio. The setup
script turns autoconnect off on those other Wi-Fi profiles. Run
`sudo bash scripts/setup_pi_access_point.sh` again. That updates
`voicestock-ap` and activates it. It does not add another profile.

If NetworkManager reports more than one profile named `voicestock-ap`,
delete the extras until one remains, then run the script again.

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

### The default route moves to the VoiceStock interface

`ip -4 route` must not show `default` via the VoiceStock device on the PC or
via the access-point device on the Pi. Re-run the setup script on that
machine. Both profiles set `ipv4.never-default` and clear a gateway. Neither
script adds a default route.

### The passphrase does not match

Both machines must source the same `scripts/voicestock-network.conf`. The
scripts store that value in the NetworkManager profile and, when they can
read it back, they fail if the stored value differs. They do not print the
passphrase. Copy the repository file again and re-run the script. Do not
create a second VoiceStock profile by hand.

### NetworkManager reports an unmanaged interface

The script stops before it writes the profile. `nmcli device status` shows
the device as unmanaged. Mark that device managed, then run the script
again. On the Pi:

```bash
sudo nmcli device set wlan0 managed yes
sudo bash scripts/setup_pi_access_point.sh wlan0
```

On the PC, use the VoiceStock interface name, not the Internet interface:

```bash
sudo nmcli device set wlan1 managed yes
sudo bash scripts/setup_pc_voicestock_wifi.sh wlan1
```

Replace the example names with the unmanaged VoiceStock device.

### The adapter does not support the expected mode

On the Pi, the script stops when the interface does not report Access Point
mode. Pass the built-in Wi-Fi device, not an Ethernet device. If
`WIFI-PROPERTIES.AP` is empty, the script also checks `iw phy`. A `no` from
either check is final for that device.

On the PC, the script only accepts a Wi-Fi device and asks NetworkManager
for 2.4 GHz infrastructure mode. If activation fails, that adapter may not
support 2.4 GHz client mode. Choose the other spare Wi-Fi interface. Do not
point the script at the Internet interface to work around it.

### Regulatory domain or channel problems

If the cell does not appear, or NetworkManager reports that the access point
could not select a channel, check `iw reg get` on the Pi. The country must
be `AR` before `setup_pi_access_point.sh` will continue. Set it with the
`raspi-config` command in [Regulatory domain](#regulatory-domain) and reboot.
Do not edit unrelated NetworkManager or kernel files by hand for this step.
The script will not change the domain for you.

## Do not

- Do not enable NAT or masquerading.
- Do not enable DHCP on the VoiceStock network, and do not set the Pi
  profile IPv4 method to `shared`.
- Do not enable IP forwarding.
- Do not bridge the VoiceStock interface to any other interface.
- Do not connect the Raspberry Pi to the Internet, and do not make it a
  Wi-Fi client of another network.
- Do not put a gateway, a DNS server, or a default route on the VoiceStock
  Wi-Fi interface.
- Do not pass the PC's Internet Wi-Fi interface to
  `setup_pc_voicestock_wifi.sh`.
- Do not change `192.168.50.1` or `192.168.50.2` without changing
  [`scripts/voicestock-network.conf`](../../scripts/voicestock-network.conf)
  and the [local network strategy](../research/local-network-strategy.md).

## Before a demo

- [ ] Raspberry Pi regulatory domain is `AR`
- [ ] `voicestock-ap` is active and the Pi address is `192.168.50.1/24`
- [ ] The Pi has no gateway and no DNS on that profile
- [ ] The PC VoiceStock interface was passed explicitly
- [ ] `voicestock-client` is active and that interface is `192.168.50.2/24`
- [ ] The PC default route is still the Internet Wi-Fi interface
- [ ] The VoiceStock interface has no gateway and no DNS

LocalNetworkInfra-04 is still open. The items below are not demonstrated by
running the setup scripts:

- the PC can reach the Raspberry Pi;
- the Raspberry Pi can reach the PC;
- the PC still has Internet through its Internet Wi-Fi adapter after the
  VoiceStock link is up;
- the VoiceStock Wi-Fi does not become the PC default route on the real
  hardware;
- the Raspberry Pi has no Internet access;
- the configuration survives reboot;
- the access point comes back after reboot;
- application communication works over the real link.
