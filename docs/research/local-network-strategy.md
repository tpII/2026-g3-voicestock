# Local network strategy

Research record for the local network between the Raspberry Pi 3 and the PC.
It keeps the evidence and the evolution of the choice. The decision now in
force is [ADR-0004](../decisions/0004-use-isolated-raspberry-pi-wifi-access-point.md).

The operational procedure is the
[local network setup guide](../setup/local-network.md). Application features
use the resulting addresses. They do not choose the network.

| Area | Status |
| --- | --- |
| Topology | Revised on 2026-10-11: isolated Wi-Fi access point on the Raspberry Pi 3, with two Wi-Fi interfaces on the PC. |
| Addressing | Kept: static `192.168.50.0/24`. Raspberry Pi `192.168.50.1/24`. PC `192.168.50.2/24`. |
| Physical validation | Pending. LocalNetworkInfra-04 has not been run on the project hardware. |

## Purpose

VoiceStock needs the Raspberry Pi 3 and the PC to reach each other on a
private IPv4 network while the PC still reaches the Internet and the
Raspberry Pi does not.

`LocalNetworkInfra` provides that IP connectivity. It does not define what
the two hosts say to each other once the packets can flow. That belongs to
`RaspberryPiPCCommunication`.

## How the decision evolved

The current architecture is a revision. The earlier choice is part of the
record, not a discarded draft that can be ignored.

### 1. A Wi-Fi access point was considered first

The first concrete wireless option was to make the Raspberry Pi advertise a
Wi-Fi cell and have the PC join it. That would have carried VoiceStock
traffic without a cable. It was set aside because, with the assumptions used
at the time, it looked more expensive to operate than a cable.

### 2. Direct Ethernet was selected

On 2026-10-04 the project selected a direct Ethernet link. The machines were
expected to stay next to each other. A normal cable, with automatic
MDI/MDI-X, was enough. The PC's single assumed Wi-Fi interface stayed on the
Internet. The Ethernet interfaces were reserved for VoiceStock.

That choice avoided an SSID, WPA, and any access-point service. Static
addresses were enough for two known hosts. The Raspberry Pi was only an
endpoint: it did not create a wireless cell and it did not route for the PC.
A failure to reach `192.168.50.2` would have been on the cable segment.

The addressing plan fixed then is still the plan:

| Role | Address |
| --- | --- |
| Network | `192.168.50.0/24` |
| Netmask | `255.255.255.0` |
| Raspberry Pi 3 | `192.168.50.1/24` |
| PC | `192.168.50.2/24` |

`192.168.50.0/24` is inside the private `192.168.0.0/16` block. The VoiceStock
network had no gateway, no DNS, no DHCP, no NAT, and no IP forwarding. The PC
default route stayed on Wi-Fi.

### 3. The wired link is not available

The Ethernet decision assumed a dedicated wired path between the PC and the
Raspberry Pi 3. The target hardware setup does not provide that path. Keeping
the Ethernet scripts would document a network the project cannot build.

### 4. The architecture returns to an isolated access point

The Wi-Fi access point is the selected architecture again, with the
constraints that made the earlier rejection incomplete now stated explicitly.
The Raspberry Pi 3 creates the cell and does nothing else with its radio. The
PC does not give up Internet access, because Internet and VoiceStock are no
longer asked to share one Wi-Fi interface.

### 5. The PC uses two Wi-Fi interfaces

One PC Wi-Fi interface remains associated to the normal Internet network and
keeps DHCP, its gateway, its DNS, and the default route. A second Wi-Fi
interface associates only to the VoiceStock cell and uses the static address
`192.168.50.2/24`. There is no route between those networks.

## Decision

The Raspberry Pi 3 is an isolated Wi-Fi access point. The PC has two Wi-Fi
interfaces: one for Internet and one for VoiceStock. Addressing is static.
There is no routing between the Internet network and the VoiceStock network.

The Raspberry Pi does not associate as a Wi-Fi client to any other network.
Its Wi-Fi interface is used only in access-point mode. It has no Internet
access through this feature.

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

The VoiceStock cell exists so the PC and the Raspberry Pi can exchange IPv4
packets. It is not an upstream network and it is not a path to the Internet.

## Fixed configuration

| Item | Value |
| --- | --- |
| SSID | `VoiceStock` |
| Security | WPA2-PSK |
| Band | 2.4 GHz |
| Subnet | `192.168.50.0/24` |
| Raspberry Pi | `192.168.50.1/24` |
| PC VoiceStock interface | `192.168.50.2/24` |
| Addressing | Static IPv4 only |
| DHCP, DNS, gateway | None on the VoiceStock network |
| Regulatory domain | Argentina (`AR`) on the Raspberry Pi |

The prototype passphrase lives in one file,
[`scripts/voicestock-network.conf`](../../scripts/voicestock-network.conf).
The setup scripts source that file. It is not copied into other scripts.

Committing that passphrase is intentional for the current academic prototype.
It is not a production secret and it does not change the project rule for API
keys and other credentials. Before any production or final deployment, this
passphrase has to leave the repository. This task does not add environment
variables, a vault, or an interactive prompt.

## Routing and isolation

Each host gets a connected route to `192.168.50.0/24` from its own static
address. That route is not a route via a gateway.

On the PC the two paths stay distinct:

```text
default route    -> Internet Wi-Fi
192.168.50.0/24  -> VoiceStock Wi-Fi
```

The VoiceStock interface has `ipv4.never-default` set, no gateway, and no
DNS. Traffic for the Raspberry Pi uses that interface. Traffic for every
other network, including the Internet, keeps the default route on the
Internet Wi-Fi interface. The setup for VoiceStock does not change that
interface.

On the Raspberry Pi the access-point interface has `192.168.50.1/24`, no
gateway, and no DNS. The Pi can reach the PC at `192.168.50.2`. It is not
given a default route.

Isolation means:

- the PC and the Raspberry Pi can communicate on `192.168.50.0/24`;
- the Raspberry Pi does not connect to the Internet;
- the Raspberry Pi is not a Wi-Fi client;
- the Raspberry Pi does not route, translate, or forward for the PC;
- NAT, IP forwarding, bridging, and Internet Connection Sharing are not part
  of this feature;
- the PC's Internet connection does not depend on the VoiceStock cell, and
  the VoiceStock cell does not depend on the PC having Internet access.

Isolation does not mean the two hosts are forbidden to talk to each other.
Reachability between `192.168.50.1` and `192.168.50.2` is the purpose of the
cell.

## Why this revision

The cable plan could not be built on the target setup. A second Wi-Fi
interface on the PC removes the objection that made the access point a poor
fit: the Internet association and the VoiceStock association are different
radios, so joining `VoiceStock` does not disconnect the PC from the Internet.

The Raspberry Pi 3 radio is used in one role only. It advertises `VoiceStock`
on 2.4 GHz. The Pi 3 does not provide a 5 GHz radio, and the architecture
does not ask it to join another network at the same time.

Static addresses stay simpler than DHCP for two known hosts. NetworkManager
on the Pi and on the reference PC (Arch Linux) can hold a persistent profile
without `hostapd` or `dnsmasq`. Those extra services would have been a DHCP
or access-point stack the design does not need.

The same address pair is kept so `RaspberryPiPCCommunication` does not change
because the medium changed. The application still talks to `192.168.50.2`
and `192.168.50.1`.

## Alternatives rejected for the current setup

### Direct Ethernet

Appropriate when a dedicated cable exists. It does not exist on the target
setup, so it is no longer the architecture. The scripts that configured it
are not part of the active procedure. Git history keeps them.

### Raspberry Pi as a client of the upstream Wi-Fi

The Pi would associate to the same network that provides Internet access, or
to some other infrastructure network. That puts the radio in client mode,
which this feature forbids, and it can give the Pi a gateway. The Pi would
also depend on that upstream network being present. VoiceStock needs the
opposite: a cell that exists only between these two machines.

### One Wi-Fi interface on the PC

A single radio can be associated to the Internet router or to `VoiceStock`,
not to both. Using it for VoiceStock would drop the PC's Internet path. The
reference PC therefore has a dedicated second interface, and the setup script
receives that interface as an explicit argument.

### DHCP, NAT, forwarding, or a bridge

DHCP would add a service in order to hand out two addresses that are already
known. NAT, forwarding, bridging, and Internet Connection Sharing would turn
the VoiceStock cell into a path beyond the two hosts. None of those belong
in this feature. The access point is configured with NetworkManager's manual
IPv4 method, not with the shared method that starts DHCP and masquerading.

## Requirements now in force

- The Raspberry Pi Wi-Fi interface runs only as the `VoiceStock` access
  point, using NetworkManager profile `voicestock-ap`.
- The PC VoiceStock interface is chosen explicitly and is configured only by
  NetworkManager profile `voicestock-client` on Arch Linux.
- Subnet `192.168.50.0/24`, Raspberry Pi `192.168.50.1/24`, PC
  `192.168.50.2/24`.
- WPA2-PSK, 2.4 GHz, IPv4 only, static addresses, autoconnect enabled.
- No gateway, no DNS, and no default route on the VoiceStock network.
- No DHCP, NAT, IP forwarding, bridge, or Internet Connection Sharing.
- The PC Internet interface keeps its own DHCP, gateway, DNS, and default
  route.
- The Raspberry Pi regulatory domain for this deployment is Argentina (`AR`).
  The access-point script checks it and does not change it.

Adapter names, the NetworkManager commands, and the prototype passphrase file
are implementation details of the setup guide. Firewall policy beyond the ban
on NAT and forwarding is outside this research. Ports and URLs belong to
`RaspberryPiPCCommunication`.

## Expected state

```text
PC
├── Wi-Fi #1
│   └── Internet (DHCP, gateway, DNS, default route)
│
└── Wi-Fi #2
    └── 192.168.50.2/24
          |
          | VoiceStock Wi-Fi, SSID VoiceStock
          |
        192.168.50.1/24
            Raspberry Pi 3 access point
```

The Raspberry Pi profile `voicestock-ap` has static IPv4 `192.168.50.1/24`,
no gateway, no DNS, IPv6 disabled, and `ipv4.never-default`. The PC profile
`voicestock-client` has static IPv4 `192.168.50.2/24` on the interface the
operator named, with the same restrictions. Checking that the two addresses
can reach each other, and that the PC still has Internet, is
LocalNetworkInfra-04. This research does not claim that check was done.

## Limitations

- No radio measurement was made. The revision follows from the missing cable
  and from the two-interface PC, not from a bandwidth benchmark.
- LocalNetworkInfra-04 is still open. Association, reboot persistence, and
  real packet delivery are not demonstrated by this document.
- The reference PC operating system is Arch Linux with NetworkManager. Other
  PC operating systems are not the setup this feature implements.
- The Raspberry Pi must already be running Raspberry Pi OS with
  NetworkManager. Installing that image, and any earlier software setup that
  needs Internet, happens before this network exists.
- The prototype passphrase is in the repository on purpose. It must be
  reconsidered before a production or final deployment.
- A wrong regulatory domain can hide the cell or reject the channel. The
  expected domain is `AR`. The setup script reports a mismatch. It does not
  rewrite the system domain by itself.
- The second PC radio has to be identified by the operator. The setup refuses
  to guess, because guessing could select the Internet interface.

## Conclusion

Use the Raspberry Pi 3 as an isolated 2.4 GHz access point for SSID
`VoiceStock`, and use a second Wi-Fi interface on the PC to join that cell.
Keep `192.168.50.1/24` on the Pi and `192.168.50.2/24` on the PC. Leave the
PC default route on the Internet Wi-Fi interface. Do not give the VoiceStock
network a gateway, DNS, DHCP, NAT, forwarding, or a bridge, and do not give
the Raspberry Pi an Internet path.

## References

- [RFC 1918: Address Allocation for Private Internets](https://www.rfc-editor.org/rfc/rfc1918.html).
  `192.168.50.0/24` sits inside the private `192.168.0.0/16` block defined there.
- [ADR-0004](../decisions/0004-use-isolated-raspberry-pi-wifi-access-point.md),
  the decision record for this revision.
