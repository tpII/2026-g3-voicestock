# VoiceStock Ethernet setup

How to apply the static Ethernet addresses for the direct link between the
Raspberry Pi 3 and the PC. The topology and the reasons for it are recorded in
the [local network strategy](../research/local-network-strategy.md). This page
only covers configuration.

These scripts check the configuration on the machine where they run. They do
not ping the other host, and they do not check Internet access. That physical
check belongs to LocalNetworkInfra-04.

## Addressing

| Role | Address |
| --- | --- |
| Network | `192.168.50.0/24` |
| Netmask | `255.255.255.0` |
| Raspberry Pi 3 | `192.168.50.1/24` |
| PC | `192.168.50.2/24` |

The PC keeps its default route on Wi-Fi, which remains the Internet path.
The VoiceStock Ethernet interface has no gateway and no DNS server. During
operation that Ethernet port is dedicated to the direct cable between the PC
and the Raspberry Pi.

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

On the PC the intended routes are:

```text
192.168.50.0/24 -> Ethernet
default route   -> Wi-Fi
```

A normal Ethernet cable is enough. The design does not use a crossover cable.

## Prerequisites

Raspberry Pi:

- Raspberry Pi 3 with Raspberry Pi OS.
- NetworkManager, with the `nmcli` command available.
- Root, because the script writes a system connection profile.
- The repository checked out on the Pi.

Windows PC:

- Windows PowerShell 5.1 or newer, running as Administrator.
- The name of the Ethernet adapter that will be cabled to the Pi. The script
  does not choose an adapter.

Neither script installs DHCP, a Wi-Fi access point, `hostapd`, DNS, NAT, or
IP forwarding.

## Raspberry Pi

From the repository:

```bash
sudo bash scripts/setup_pi_ethernet.sh
```

The script looks for the Pi's Ethernet interface. It configures that interface
only. If NetworkManager reports more than one Ethernet interface, name the
VoiceStock one:

```bash
sudo bash scripts/setup_pi_ethernet.sh eth0
```

`eth0` is an example. Use the name NetworkManager shows for the port cabled
to the PC. A Wi-Fi interface name is rejected.

The script creates or updates one NetworkManager profile, `voicestock-ethernet`:

- type Ethernet, bound to the selected interface;
- IPv4 method `manual`;
- address `192.168.50.1/24`;
- no IPv4 gateway and no IPv4 DNS;
- `ipv4.never-default` enabled;
- autoconnect enabled, with priority above the default wired profile;
- IPv6 disabled on this profile.

Running it again updates that same profile and activates it. It does not
create `voicestock-ethernet-1`. NetworkManager stores the profile, so the
address remains after reboot. The script does not change Wi-Fi profiles.

At the end it prints whether the address is present, the profile is active,
and the profile has no gateway, no DNS, and is not the default IPv4 route.

## Windows

List adapters and choose the Ethernet port that will face the Raspberry Pi.
Do this before cabling if several wired adapters are easy to confuse. The
`Name` column is the value the script requires:

```powershell
Get-NetAdapter | Select-Object Name, InterfaceDescription, Status, MacAddress
```

Development and demo PCs often have extra Ethernet, USB, dock, VPN, Hyper-V,
and Docker adapters. Copy the `Name` of the dedicated one. The script refuses
a wildcard and refuses to guess.

In an Administrator PowerShell, from the repository:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_pc_ethernet.ps1 -InterfaceAlias "Ethernet"
```

Replace `Ethernet` with the exact `Name` from `Get-NetAdapter`. A Wi-Fi
adapter is rejected.

On that adapter only, the script:

- disables IPv4 DHCP;
- sets `192.168.50.2/24`;
- removes any IPv4 default route;
- clears IPv4 DNS servers;
- removes other IPv4 addresses so a second run does not accumulate them.

Windows stores this in the persistent adapter configuration, so it remains
after reboot. The script does not add a default route, does not change Wi-Fi,
and does not enable Internet Connection Sharing.

A disabled adapter is left disabled. Enable it, then run the script again.

At the end it prints whether `192.168.50.2/24` is set and whether that adapter
has no default gateway and no DNS server.
