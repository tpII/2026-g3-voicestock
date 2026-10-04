# Local network strategy

Research record for task **LocalNetworkInfra-01**: evaluate the local network
strategy between the Raspberry Pi 3 and the PC.

**Status:** research closed. The topology and the addressing plan are decided.
Applying those addresses on the devices belongs to the next LocalNetworkInfra
task. This document is not an Architecture Decision Record. It keeps the
evidence of the investigation. A later ADR is not required for this choice
unless a future task changes it.

| Area | Status |
| --- | --- |
| Topology | Decided: direct Ethernet between the PC and the Raspberry Pi 3. Not configured in this task. |
| Addressing | Decided: static `192.168.50.0/24`. Not applied on the devices in this task. |
| Raspberry Pi as Wi-Fi access point | Considered and rejected for VoiceStock's current constraints. |

## Purpose

VoiceStock needs the Raspberry Pi 3 and the PC to reach each other on a
private IPv4 network. This document records which physical network provides
that connectivity, which addresses each host uses, and what "isolated" means
for this feature.

`LocalNetworkInfra` is responsible only for that underlying IP connectivity.
It does not define what the two hosts say to each other once the packets can
flow.

## Context

During normal operation the Raspberry Pi and the PC stay next to each other.
The PC already uses its Wi-Fi interface for Internet access. The Raspberry Pi
does not need Internet access while the system is running.

The Raspberry Pi 3 and a typical PC each have an Ethernet interface that can
be dedicated to VoiceStock. That physical arrangement is the constraint this
decision is built on. The choice is about how two nearby machines are linked,
not about a general-purpose wireless network.

The addressing plan below is the source for the VoiceStock local network.
The procedure that applies it is the
[Ethernet setup guide](../setup/local-network.md). Application features keep
using the network; they do not choose it.

## Evaluation criteria

The alternatives are judged against the current physical setup and against
the October system, not against a general networking design.

1. The Raspberry Pi and the PC can exchange IPv4 traffic with each other.
2. The PC keeps its existing Wi-Fi path to the Internet.
3. The Raspberry Pi does not need Internet access during normal operation.
4. The link does not require an access point, an SSID, WPA, or a Wi-Fi DHCP
   service.
5. Addressing stays simple for two known hosts.
6. The Internet-facing interface on the PC stays separate from the VoiceStock
   interface.
7. The Raspberry Pi is not asked to route, translate, or forward traffic for
   the PC.
8. The result is stable enough to demonstrate and straightforward to diagnose.

No throughput or latency measurement was required. Both a direct cable and a
small Wi-Fi cell can carry the later application messages. The difference is
operational cost on this hardware layout.

## Decision

VoiceStock does **not** use the Raspberry Pi as a Wi-Fi access point.

The selected architecture is a **direct Ethernet point-to-point local
network** between the Raspberry Pi 3 and the PC. Both Ethernet interfaces use
**static IPv4 addresses** on a dedicated private subnet. No DHCP server is
part of the design.

A normal Ethernet cable is sufficient. Modern Ethernet interfaces, including
the Raspberry Pi 3 Ethernet port and typical PC Ethernet ports, negotiate
MDI/MDI-X automatically. A crossover cable is not part of the design.

## Physical topology

The PC has two relevant interfaces:

- Wi-Fi reaches the Internet.
- Ethernet is reserved for the VoiceStock local network.

The Raspberry Pi 3 uses its Ethernet interface for that same local network. It
does not use this link as a path to the Internet.

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

## Addressing

Dedicated private subnet:

| Role | Address |
| --- | --- |
| Network | `192.168.50.0/24` |
| Netmask | `255.255.255.0` |
| Raspberry Pi 3 | `192.168.50.1` |
| PC | `192.168.50.2` |

`192.168.50.0/24` is inside the private `192.168.0.0/16` block. These two host
addresses are fixed for VoiceStock. They are not allocated by DHCP and they
are not reused from the network that provides Internet access to the PC.

The dedicated Ethernet network has:

- no default gateway;
- no DNS server.

Hosts on this link address each other by the fixed IPv4 addresses above. Name
resolution is not a requirement of `LocalNetworkInfra`.

## Routing

Assigning `192.168.50.1/24` and `192.168.50.2/24` makes `192.168.50.0/24`
directly reachable on each Ethernet interface. That connected route is the
whole VoiceStock route. It is not a route via a gateway.

On the PC the two paths stay distinct:

```text
192.168.50.0/24 -> Ethernet interface
default route   -> Wi-Fi interface
```

The PC Ethernet interface therefore has no gateway of its own. Traffic for
the Raspberry Pi uses Ethernet. Traffic for every other network, including
the Internet, keeps using the default route on Wi-Fi.

On the Raspberry Pi the Ethernet interface has the static address
`192.168.50.1/24` and no default gateway through that interface. The Pi can
reach the PC at `192.168.50.2`. It is not given a route to the Internet by
this feature, and it does not need one during normal operation.

## Isolation

"Isolated local network" means the VoiceStock Ethernet segment is a private
link between these two hosts, separate from the PC's Internet connection.

Concretely:

- the PC and the Raspberry Pi can communicate with each other over Ethernet;
- the Raspberry Pi does not require Internet access;
- the Raspberry Pi must not act as a router for the PC;
- NAT is not part of this feature;
- IP forwarding between the local Ethernet network and the PC's Internet
  connection is not part of this feature;
- Internet connectivity on the PC does not depend on the VoiceStock network,
  and the VoiceStock network does not depend on the PC having Internet access.

Isolation does not mean that the PC and the Raspberry Pi are prevented from
communicating. Reachability between `192.168.50.1` and `192.168.50.2` is the
purpose of the link.

## Rationale

Ethernet was selected instead of a Raspberry Pi Wi-Fi access point for the
following reasons.

The two machines are expected to remain physically close while VoiceStock is
operating, so a short Ethernet cable matches the real layout. The PC's Wi-Fi
interface remains available for Internet access and is not consumed by the
VoiceStock link.

The project then does not have to configure or maintain an access point. There
is no SSID, no WPA configuration, no Wi-Fi DHCP service, no `hostapd`, and no
other Wi-Fi access-point infrastructure.

Static point-to-point addressing is simpler than DHCP when the only hosts are
two known devices with fixed roles. A wired link is also predictable: it does
not depend on radio association, signal quality, or which wireless network the
PC joined.

The architecture separates the Internet-facing interface (PC Wi-Fi) from the
VoiceStock interface (Ethernet on both machines). That split reduces the
networking work assigned to the Raspberry Pi. The Pi is an endpoint on the
local segment, not the device that creates the wireless cell or the device
that routes for the PC. Fewer roles on the Pi make failures easier to locate
during troubleshooting and during a demonstration: if the Pi cannot reach
`192.168.50.2`, the problem is on the Ethernet segment, not in Wi-Fi
association or in the PC's Internet connection.

## Alternatives considered

### Raspberry Pi Wi-Fi access point

An access point on the Raspberry Pi was the other concrete option. The PC
would have associated to a wireless network created by the Pi, and that
wireless cell would have carried VoiceStock traffic.

That approach is a valid way to connect two machines in general. It is a
weaker fit for VoiceStock's current physical and operational constraints:

- it consumes the Raspberry Pi Wi-Fi interface for infrastructure;
- it requires additional access-point configuration;
- simultaneous Internet access on the PC is less straightforward when the PC
  has only one Wi-Fi adapter, because that adapter would be associated to the
  Pi instead of to the upstream network;
- it adds SSID, WPA, and wireless DHCP (or an equivalent static Wi-Fi plan)
  that the project does not need while both devices sit next to each other.

The access point was therefore rejected for this system. It can be
reconsidered only if a later requirement removes the nearby Ethernet layout,
for example if the PC and the Pi must operate without a cable. This research
does not design that variant.

DHCP on the Ethernet segment was not selected either. With exactly two known
hosts, a DHCP service would add a component to install and diagnose without
changing the addresses the applications must use. Static addresses keep the
plan visible and stable.

## Scope

`LocalNetworkInfra` provides IP connectivity between the Raspberry Pi 3 and
the PC. After the next configuration task, each host can send IPv4 packets to
the other host's fixed address on `192.168.50.0/24`.

This feature does **not** define:

- the application protocol between the Raspberry Pi and the PC;
- HTTP endpoints;
- request or response payloads;
- speech-to-text communication;
- LLM communication;
- pending-operation synchronization;
- web application behaviour.

Those responsibilities belong to their own VoiceStock features. The protocol
between the two machines belongs to `RaspberryPiPCCommunication`, which
consumes this network and does not configure it.

## Architectural requirements and implementation boundary

The following points are architectural requirements. They are in force for
later LocalNetworkInfra work and for any feature that assumes this network
exists.

- Topology: one Ethernet cable between the PC and the Raspberry Pi 3. The
  cable is a normal straight-through cable. Auto MDI/MDI-X is assumed.
  Crossover cabling is out of scope.
- The Raspberry Pi is not a Wi-Fi access point for VoiceStock.
- Subnet `192.168.50.0/24`, Raspberry Pi `192.168.50.1`, PC `192.168.50.2`,
  netmask `255.255.255.0`.
- Static configuration on both Ethernet interfaces.
- No default gateway and no DNS server on the VoiceStock Ethernet network.
- The PC default route stays on Wi-Fi.
- No NAT and no IP forwarding between that Ethernet network and the PC's
  Internet connection.
- The Raspberry Pi does not route on behalf of the PC.

The following points are implementation details. This research does not decide
them.

- Which operating-system tool writes the static address on each device.
- The kernel or adapter name of either Ethernet interface.
- Firewall rules, except the architectural ban on NAT and on forwarding onto
  this feature.
- Any port, URL, timeout, or message format used after the packets can flow.

## Expected implementation

The next LocalNetworkInfra task configures static Ethernet addressing on both
devices. This research does not perform that configuration.

Expected final state:

```text
PC
├── Wi-Fi
│   └── Internet
│
└── Ethernet
    └── 192.168.50.2/24
          |
          | dedicated VoiceStock network
          |
        192.168.50.1/24
            Raspberry Pi 3
```

The Raspberry Pi Ethernet interface must have:

- static IP `192.168.50.1/24`;
- no default gateway through this interface;
- no DNS requirement through this interface.

The PC Ethernet interface must have:

- static IP `192.168.50.2/24`;
- no gateway on this interface;
- no DNS server associated with the VoiceStock network.

When that configuration is in place, each host has a connected route to
`192.168.50.0/24` through its Ethernet interface, and the PC still uses Wi-Fi
for its default route. Checking that those two addresses answer each other is
a connectivity check for that later task. It does not require Internet access
on the Raspberry Pi.

## Limitations of this research

- No cable, switch, or radio measurement was made. The decision follows from
  the physical layout and from the cost of running an access point, not from
  a bandwidth benchmark.
- Automatic MDI/MDI-X is a property of the Ethernet interfaces in this design.
  This task did not read the link status of the project boards.
- Operating-system names for the Ethernet adapters, and the commands that set
  a static address, are deliberately left to the next task.
- This document does not assign an application port or a base URL. Those
  belong to `RaspberryPiPCCommunication`.
- Software installation on the Raspberry Pi may still happen before this
  network exists. That provisioning path is outside `LocalNetworkInfra`.
  Normal operation of the system does not require the Pi to reach the
  Internet.

## Conclusion

Use a dedicated Ethernet link between the PC and the Raspberry Pi 3, with
static addresses `192.168.50.2/24` on the PC and `192.168.50.1/24` on the Pi.
Leave the PC's default route on Wi-Fi. Do not put a gateway or a DNS server
on the VoiceStock segment, and do not turn the Raspberry Pi into an access
point, a router, or a NAT device.

That gives `RaspberryPiPCCommunication` and the other application features a
stable pair of addresses, without mixing their protocols into the network
design.

## References

- [RFC 1918: Address Allocation for Private Internets](https://www.rfc-editor.org/rfc/rfc1918.html).
  `192.168.50.0/24` sits inside the private `192.168.0.0/16` block defined there.
