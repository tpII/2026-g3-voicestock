# VoiceStock Ethernet setup

How to prepare the direct Ethernet link between the Raspberry Pi 3 and the PC,
check that each machine has the right local configuration, and recover from
the usual setup mistakes.

Why this topology was chosen is the
[local network strategy](../research/local-network-strategy.md). This page is
the procedure. It covers the cable, the static addresses, local inspection,
the order to bring the link up, and troubleshooting.

Application traffic is a separate feature, `RaspberryPiPCCommunication`.
Endpoints, payloads, speech-to-text, and language models are not part of this
guide. Once the addresses below are in place, that feature is documented in
the
[Raspberry Pi–PC communication interface](../interfaces/pc-communication.md).
The operator page that the PC browser opens on the Pi is the
[web setup guide](pi-web.md).

The setup scripts check the machine they run on. They do not ping the other
host, and they do not test Internet access. That physical check belongs to
LocalNetworkInfra-04.

## Expected topology

```text
                    Internet
                       |
                     Wi-Fi
                       |
                      PC
                       |
                    Ethernet
                       |
                Raspberry Pi 3
```

| Role | Address |
| --- | --- |
| Network | `192.168.50.0/24` |
| Netmask | `255.255.255.0` |
| Raspberry Pi 3 | `192.168.50.1/24` |
| PC | `192.168.50.2/24` |

The PC uses Wi-Fi for Internet and Ethernet only for VoiceStock. The
Raspberry Pi uses Ethernet for VoiceStock and does not need Internet during
normal operation. The VoiceStock Ethernet interfaces have no gateway and no
DNS server.

```text
                    Internet
                       |
                     Wi-Fi
                       |
                      PC
                 default route
                       |
        +--------------+--------------+
        |                             |
      Wi-Fi                         Ethernet
                                   192.168.50.2/24
                                        |
                                        |
                                  direct cable
                                        |
                                        |
                                   192.168.50.1/24
                                  Raspberry Pi 3
```

On the PC the routes should be:

```text
192.168.50.0/24 -> Ethernet
default route   -> Wi-Fi
```

A normal Ethernet cable is enough. The design does not use a crossover cable.

## Hardware preparation

Minimum for a development session or a demo:

- a Raspberry Pi 3, powered on;
- a PC;
- an Ethernet port on the PC, or a USB Ethernet adapter plugged into the PC;
- a normal Ethernet cable between that port and the Pi;
- the PC's Wi-Fi available when the session needs Internet.

During operation the Ethernet port used for VoiceStock is dedicated to that
direct cable. Do not share it with a dock network, a campus LAN, or a virtual
switch. If the PC has several wired adapters, decide which physical port faces
the Pi before applying an address.

## Raspberry Pi setup

Prerequisites:

- Raspberry Pi OS with NetworkManager;
- `nmcli` and `ip` on the Pi;
- root, because the script writes a system connection profile;
- the VoiceStock repository checked out on the Pi.

From the repository root:

```bash
sudo bash scripts/setup_pi_ethernet.sh
```

The script refuses to run without root. It looks for Ethernet devices and
ignores Wi-Fi:

- no Ethernet device: it stops;
- exactly one: it uses that device;
- more than one: it stops and lists them. Pass the port cabled to the PC:

```bash
sudo bash scripts/setup_pi_ethernet.sh eth0
```

`eth0` is an example. Use the device name from `nmcli device status`. A Wi-Fi
name is rejected. The name may contain only letters, digits, `.`, `_`, and
`-`.

The script creates or updates one NetworkManager profile,
`voicestock-ethernet`:

- type Ethernet, bound to the selected interface;
- IPv4 method `manual`;
- address `192.168.50.1/24`;
- no IPv4 gateway and no IPv4 DNS;
- `ipv4.never-default` enabled, so this profile is not the default route;
- autoconnect enabled, with priority `100`;
- IPv6 disabled on this profile.

Running it again updates that same profile and activates it. It does not
create `voicestock-ethernet-1`. NetworkManager stores the profile, so the
address remains after reboot. The script does not change Wi-Fi profiles.

At the end it prints whether `192.168.50.1/24` is present, whether
`voicestock-ethernet` is active on that interface, and whether the profile
has no gateway, no DNS, and is not the default IPv4 route.

## Windows PC setup

Prerequisites:

- Windows PowerShell 5.1 or newer, running as Administrator;
- `netsh.exe`, which the script uses to store an empty IPv4 DNS list;
- the exact `Name` of the Ethernet adapter cabled to the Pi.

The script does not choose an adapter. List them and copy the `Name` of the
dedicated port:

```powershell
Get-NetAdapter | Select-Object Name, InterfaceDescription, Status, MacAddress
```

Development and demo PCs often also have USB Ethernet, dock, VPN, Hyper-V,
and Docker adapters. Do not pass a Wi-Fi name, a VPN name, or a virtual
adapter. A Wi-Fi adapter is rejected and left unchanged. A wildcard such as
`Ethernet*` is rejected.

In an Administrator PowerShell, from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_pc_ethernet.ps1 -InterfaceAlias "Ethernet"
```

Replace `Ethernet` with the exact `Name` from `Get-NetAdapter`.

On that adapter only, the script:

- disables IPv4 DHCP;
- sets `192.168.50.2/24`;
- removes any IPv4 default route;
- sets a static IPv4 DNS list with no servers;
- removes other IPv4 addresses so a second run does not accumulate them.

Windows stores this in the persistent adapter configuration, so it remains
after reboot. The script does not add a default route, does not change Wi-Fi,
and does not enable Internet Connection Sharing.

A disabled adapter is left disabled. Enable it in Windows, then run the
script again.

At the end it prints whether `192.168.50.2/24` is set and whether that
adapter has no default gateway and no DNS server.

## Local configuration verification

These commands inspect configuration on one machine. They are not the
physical acceptance test. Reachability between the PC and the Pi is
LocalNetworkInfra-04.

### Raspberry Pi

```bash
ip -4 addr
ip -4 route
nmcli connection show --active
```

Expected state:

- the Ethernet interface has `inet 192.168.50.1/24`;
- `ip -4 route` shows `192.168.50.0/24` on that interface;
- `ip -4 route` does not show a `default` route via that interface;
- `nmcli connection show --active` lists `voicestock-ethernet` on that
  interface.

`nmcli -g ipv4.gateway,ipv4.dns connection show voicestock-ethernet` should
print nothing useful for either property (empty, or `--`).

### Windows

Replace `Ethernet` with the alias that was configured.

```powershell
Get-NetIPAddress -AddressFamily IPv4
Get-NetRoute -AddressFamily IPv4
Get-DnsClientServerAddress -AddressFamily IPv4
```

Read those three lists against the dedicated adapter, not against every
adapter on the PC. Narrower checks:

```powershell
Get-NetIPAddress -InterfaceAlias "Ethernet" -AddressFamily IPv4
Get-NetRoute -InterfaceAlias "Ethernet" -AddressFamily IPv4 -DestinationPrefix "0.0.0.0/0"
Get-DnsClientServerAddress -InterfaceAlias "Ethernet" -AddressFamily IPv4
Get-NetRoute -DestinationPrefix "0.0.0.0/0" -AddressFamily IPv4
```

Expected state:

```text
Raspberry Pi Ethernet: 192.168.50.1/24
PC Ethernet:           192.168.50.2/24

PC default route: Wi-Fi
VoiceStock Ethernet default route: none
VoiceStock Ethernet DNS: none
```

On the PC that means prefix length `24` for `192.168.50.2`, no
`0.0.0.0/0` route on the VoiceStock alias, an empty IPv4 DNS server list on
that alias, and the `0.0.0.0/0` route on the Wi-Fi adapter when Internet is
required.

## Startup procedure

Use this order for a normal session or a demonstration:

1. Power on the Raspberry Pi and wait until it has booted.
2. Start the PC.
3. Connect the Ethernet cable between the Pi and the dedicated PC port.
4. If the session needs Internet, confirm the PC is joined to Wi-Fi.
5. On the Pi, apply or verify `voicestock-ethernet` with
   `sudo bash scripts/setup_pi_ethernet.sh`.
6. On the PC, apply or verify the dedicated adapter with
   `setup_pc_ethernet.ps1 -InterfaceAlias` set to that port's exact name.
7. Continue with the VoiceStock application. The network guide stops here.

Steps 5 and 6 are safe to repeat. Each script updates the same configuration
instead of adding a second address or a second profile.

## Troubleshooting

### The Raspberry Pi does not have 192.168.50.1

Run `ip -4 addr` and `nmcli connection show voicestock-ethernet`. Then run
`sudo bash scripts/setup_pi_ethernet.sh` again from the repository root.

If the script reports that `nmcli` or `ip` is missing, NetworkManager is not
available and this procedure cannot configure the link. If it reports that no
Ethernet interface exists, the Pi does not see a wired device. If it reports
that the profile is not active, or the address check fails, leave the cable
seated and run the script again. Do not assign a second address by hand.

### The PC does not have 192.168.50.2

Check the alias you intend to use:

```powershell
Get-NetIPAddress -InterfaceAlias "Ethernet" -AddressFamily IPv4
```

Run `setup_pc_ethernet.ps1` again as Administrator with that exact
`-InterfaceAlias`. The script removes other IPv4 addresses on that adapter
and sets `192.168.50.2/24`. If the adapter is disabled, enable it in Windows
first. The script will not enable it.

### The Windows script rejects the selected interface

The value must be the `Name` column from `Get-NetAdapter`, character for
character. The script does not guess and does not accept `*`, `?`, `[`, or
`]`.

- Unknown name: the error lists the adapters that exist. Copy one `Name`.
- Disabled adapter: enable it, then run the script again. Nothing else was
  changed.
- Not running as Administrator: open PowerShell as Administrator. The script
  stops before it edits any adapter.

### A Wi-Fi adapter was selected by mistake

The script stops when the alias is a Wi-Fi adapter and does not change it.
Run it again with the Ethernet `Name` from `Get-NetAdapter`. Confirm Wi-Fi
separately with `Get-NetAdapter` and with the `0.0.0.0/0` route. Do not use
the VoiceStock script to repair Wi-Fi.

### The Raspberry Pi reports more than one Ethernet interface

The script prints the device names and stops, so it cannot configure the
wrong port. Identify the port cabled to the PC with `nmcli device status`,
then pass that name:

```bash
sudo bash scripts/setup_pi_ethernet.sh end0
```

Use the printed name, not this example. The script still configures only that
device.

### The Ethernet interface is unmanaged by NetworkManager

The script stops with "not managed by NetworkManager" and does not write the
profile. `nmcli device status` shows the device as unmanaged. This procedure
does not switch the Pi to another network backend. Mark that device managed,
then run the script again:

```bash
sudo nmcli device set eth0 managed yes
sudo bash scripts/setup_pi_ethernet.sh eth0
```

Replace `eth0` with the unmanaged Ethernet device. Do not run this against a
Wi-Fi device.

### An unexpected Ethernet default route exists

On the Pi, `ip -4 route` must not show `default` via the VoiceStock Ethernet
device. On the PC, this must print nothing:

```powershell
Get-NetRoute -InterfaceAlias "Ethernet" -AddressFamily IPv4 -DestinationPrefix "0.0.0.0/0"
```

Re-run the setup script for that machine. The Pi profile sets
`ipv4.never-default` and clears a gateway on `voicestock-ethernet`. The
Windows script removes `0.0.0.0/0` on the selected adapter only. Do not add a
gateway so the Pi can reach the Internet.

### The PC loses Internet after the Ethernet configuration

Internet stays on Wi-Fi. List default routes:

```powershell
Get-NetRoute -DestinationPrefix "0.0.0.0/0" -AddressFamily IPv4
```

The `0.0.0.0/0` entry should name the Wi-Fi adapter. If it names the
VoiceStock Ethernet adapter, run `setup_pc_ethernet.ps1` again for that
alias so the script removes that route. If Wi-Fi itself is disconnected,
reconnect it in Windows. The script does not join or repair Wi-Fi.

### The Ethernet link does not come up

Confirm the Pi is powered, the cable is seated at both ends, and the PC
adapter you configured is the port that has the cable. `Get-NetAdapter` shows
`Up` when the link has carrier, `Disconnected` when it does not, and
`Disabled` when the adapter is turned off. On the Pi, `nmcli device status`
shows the Ethernet device.

`Disconnected` with no carrier is a cable or port problem. The saved address
can already be correct. Seeing both addresses is still not a test that one
host can reach the other. That check is LocalNetworkInfra-04.

### `voicestock-ethernet` is not active after reboot

On the Pi:

```bash
nmcli connection show --active
nmcli connection show voicestock-ethernet
```

The profile should be bound to the Ethernet device, with autoconnect enabled.
Its autoconnect priority is `100`, so it is preferred over the default wired
profile. Run `sudo bash scripts/setup_pi_ethernet.sh` again. That updates
`voicestock-ethernet` and activates it. It does not add another profile.

If NetworkManager reports more than one profile with that exact name, the
script stops. Delete the extra profiles with `nmcli connection delete`,
keeping a single `voicestock-ethernet`, then run the script again.

## Do not

- Do not configure a gateway on the VoiceStock Ethernet interface.
- Do not configure DNS servers on that interface.
- Do not enable Internet Connection Sharing.
- Do not enable NAT.
- Do not enable IP forwarding between Ethernet and Wi-Fi.
- Do not use DHCP for this link.
- Do not turn the Raspberry Pi into a Wi-Fi access point.
- Do not change `192.168.50.1` or `192.168.50.2` without changing the
  architecture recorded in the
  [local network strategy](../research/local-network-strategy.md).
- Do not pass a Wi-Fi, VPN, or virtual adapter as `-InterfaceAlias`.

## Demo checklist

Before a university demo or a test session:

- [ ] Raspberry Pi booted
- [ ] Ethernet cable connected to the dedicated PC port
- [ ] Raspberry Pi Ethernet is `192.168.50.1/24`
- [ ] PC Ethernet is `192.168.50.2/24`
- [ ] PC Wi-Fi is connected when the session needs Internet
- [ ] The VoiceStock Ethernet interfaces have no default gateway
- [ ] The VoiceStock Ethernet interfaces have no DNS servers
- [ ] `voicestock-ethernet` is the active profile on the Pi
- [ ] The same addresses are still present after a reboot
