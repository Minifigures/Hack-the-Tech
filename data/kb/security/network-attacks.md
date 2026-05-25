# Network Attacks

## syn-flood

A SYN flood is a TCP-layer denial-of-service attack in which the attacker
sends many TCP SYN packets without completing the three-way handshake. The
server allocates resources for each half-open connection until the connection
backlog is exhausted, denying service to legitimate clients.

Mitigations:

- **SYN cookies**: encode the connection state into the initial sequence
  number so no server state is allocated until the handshake completes.
- **Backlog tuning**: increase `tcp_max_syn_backlog`, lower `tcp_synack_retries`.
- **Stateful firewall** with SYN-flood protection enabled.
- **Upstream DDoS scrubbing** for volumetric attacks beyond network capacity.

## dns-amplification

DNS amplification abuses open recursive resolvers to amplify spoofed-source
queries into large responses directed at the victim. Mitigation: disable open
recursion, deploy BCP38 ingress filtering, and use response-rate limiting.

## arp-spoofing

ARP spoofing poisons the ARP cache to redirect traffic to an attacker on the
same LAN. Mitigations include dynamic ARP inspection on the switch, DHCP
snooping, and segmenting trust boundaries.
