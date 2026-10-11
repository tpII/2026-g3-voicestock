# ADR-0004: Use an isolated Raspberry Pi Wi-Fi access point

## Status

Accepted

## Context

VoiceStock needs a private IPv4 link between the Raspberry Pi 3 and the PC.
The PC must keep Internet access. The Raspberry Pi must not have Internet
access and must not route for the PC.

The first implemented plan was a direct Ethernet cable. That plan is recorded
in [the local network research](../research/local-network-strategy.md). It was
superseded when the target hardware setup turned out not to provide the wired
Ethernet connection the plan required.

## Decision

The Raspberry Pi 3 operates only as the access point of an isolated Wi-Fi
network named `VoiceStock`.

The PC uses two Wi-Fi interfaces. One stays on the normal Internet network.
The other associates only to `VoiceStock`. Addressing stays static on
`192.168.50.0/24`: the Raspberry Pi is `192.168.50.1/24` and the PC is
`192.168.50.2/24`. The VoiceStock network has no DHCP, DNS, gateway, NAT,
forwarding, or bridge. The PC default route stays on the Internet interface.

Application code continues to use those two addresses. It does not choose the
physical medium.

The evidence, the earlier Ethernet decision, and the rejected alternatives are
kept in the research document. This ADR records the decision that is now in
force.

## Alternatives considered

- **Direct Ethernet:** selected earlier because it separated Internet and
  VoiceStock with one cable. Rejected after the target setup was found to have
  no such cable path.
- **Raspberry Pi as a Wi-Fi client of the upstream network:** rejected because
  the Pi would leave access-point mode and could gain Internet access.
- **One Wi-Fi interface on the PC:** rejected because that interface cannot
  stay on the Internet and on the VoiceStock cell at the same time.
- **DHCP, NAT, forwarding, or a bridge:** rejected because the link is a
  two-host isolated network, not a route to the Internet.

## Consequences

### Positive

- The PC can reach the Raspberry Pi and the Internet at the same time.
- The Raspberry Pi remains an endpoint, not a router.
- The addresses already chosen for VoiceStock stay the same.

### Trade-offs

- The reference PC must have a second Wi-Fi interface, dedicated to
  VoiceStock and passed explicitly to the setup script.
- The prototype WPA2 passphrase is stored in the repository. That is
  acceptable only for this academic prototype.
- The Raspberry Pi still has no Internet path during normal operation.
- Physical validation of the link remains LocalNetworkInfra-04 and is not
  implied by this decision.
