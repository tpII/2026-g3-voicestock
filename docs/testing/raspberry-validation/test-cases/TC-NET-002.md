# TC-NET-002 — Bidirectional connectivity and isolation

- Status: DESIGNED
- Executions: none
- Procedure version: 1

## Objective

Show that the PC and the Raspberry Pi answer each other on the VoiceStock
subnet, that those packets use the VoiceStock interfaces, and that the Pi
does not gain an Internet path.

## Test level and type

Level: hardware validation.

Type: functional and measurement.

## Requirements and ClickUp traceability

- ClickUp: [LocalNetworkInfra-04](https://app.clickup.com/t/86e3jutyu).
- Requirement: the checks the setup guide leaves open: each direction, the
  PC keeps Internet on its other interface, the VoiceStock interface is not
  the default route, and the Pi has no Internet access.

## Source modules and documentation

- [Local network setup](../../../setup/local-network.md), section "Before a
  demo" and the unchecked hardware list at the end.
- [TC-NET-001](TC-NET-001.md).

## Preconditions and dependencies

- [TC-NET-001](TC-NET-001.md) passed its local criteria in an execution that
  is still the configuration under test. If profiles were edited later,
  repeat TC-NET-001.
- Do not change addresses or add a gateway in order to make ping succeed.

## Required hardware and software

- The Pi access point and the PC client associated, addresses
  `192.168.50.1` and `192.168.50.2`.
- `ping` from iputils or the Raspberry Pi OS equivalent. The `-W` flag is
  the per-packet timeout in seconds on both iputils and the Pi's ping. If
  the installed ping rejects `-W`, record the implementation (`ping -V`)
  and mark the timed samples **BLOCKED** rather than substituting an
  unstated flag.
- `ip` on both hosts.

## Preparation

On the PC:

```bash
ip route get 192.168.50.1
ip route get 1.1.1.1
```

On the Pi:

```bash
ip route get 192.168.50.2
ip route get 1.1.1.1
```

`1.1.1.1` is a probe address, not a requirement that a particular anycast
node stay reachable forever. The PC probe must succeed before the Pi probe
is interpreted.

## Execution

Warm-up: one echo, discarded.

Measured: ten echoes, one second apart. Do not use flood ping.

From the PC:

```bash
ping -c 1 -W 1 192.168.50.1
ping -c 10 -W 1 -i 1 192.168.50.1
```

From the Pi:

```bash
ping -c 1 -W 1 192.168.50.2
ping -c 10 -W 1 -i 1 192.168.50.2
```

Isolation, after the PC has a successful probe to `1.1.1.1`:

```bash
ping -c 3 -W 1 1.1.1.1
```

Run that on the PC and then on the Pi. Three echoes are enough for a
yes-or-no path check. They are not the RTT sample set.

Confirm again:

```bash
ip -4 route show default
```

on both hosts.

Do not add `-I` unless `ip route get` already shows the correct interface
and a later ping contradicts it. Forcing an interface hides a routing
defect. If `ip route get 192.168.50.1` on the PC does not use the
VoiceStock interface, the case fails before ping.

## Observations and evidence

- The four `ip route get` transcripts.
- Full ping summaries (transmitted, received, loss, and the RTT lines).
- Default route lines.

## Metrics

| Metric | Sample | Limit |
| --- | --- | --- |
| PC to Pi ICMP RTT | 10 measured echoes | Recorded. A latency budget is **TO BE DEFINED**. |
| Pi to PC ICMP RTT | 10 measured echoes | Same. |
| Loss | replies missing from those 10 | Recorded. Zero replies fails connectivity. A non-zero allowance is **TO BE DEFINED**. |
| Internet from the Pi | 3 probes | Must not succeed |
| Internet from the PC | 3 probes | Must succeed, otherwise the Pi result is **BLOCKED** |

Convert ping times to seconds in the raw table. Do not subtract Pi and PC
clocks.

## Acceptance criteria

1. `ip route get` on the PC toward `192.168.50.1` names the VoiceStock
   interface from TC-NET-001. The Pi's route toward `192.168.50.2` names
   the access-point interface.
2. At least one measured echo succeeds in each direction. That is the
   connectivity criterion. The loss count is recorded. A numeric loss
   allowance is **TO BE DEFINED**. The execution must not describe the
   link as reliable, and must not mark a reliability criterion passed,
   while that allowance is still undefined. Zero replies fails
   connectivity.
3. The PC receives at least one reply from `1.1.1.1`, and `ip route get
   1.1.1.1` does not use the VoiceStock interface.
4. The Pi receives no reply from `1.1.1.1`, and it has no default route.
5. Name lookup is not used. A DNS failure is not the isolation result.

## Failure conditions

- No replies from the peer: **FAILED**.
- Pi receives a reply from `1.1.1.1` or gains a default route: **FAILED**.
- PC cannot reach `1.1.1.1` either: isolation is **BLOCKED**.
- Ping binary lacks the flags above: **BLOCKED** for the measurement, and
  the case cannot be **CLOSED_PASSED**.

## Recovery and cleanup

Stop ping. Do not leave a flood running. Do not install a new route to
repair a failure inside this execution.

## Limitations and exclusions

ICMP success does not show that TCP port 8000 is open. That is the HTTP
cases. Reboot is TC-NET-003. Application traffic is out of scope here.
