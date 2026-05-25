# Incident Response Playbook

## ransomware-first-action

When ransomware is suspected on a host, the first response action is to
**isolate** the host from the network in a way that preserves volatile
evidence. Specifically:

- Disable wired NICs and disconnect Wi-Fi.
- Apply VLAN ACL deny rules at the switch or firewall to contain east-west
  spread.
- Do **not** power off the host. Powering off destroys memory artifacts and
  pagefile evidence required for triage and recovery.
- Capture a memory image and the contents of the pagefile.
- Notify the incident commander and start the IR ticket.

Subsequent steps include scoping (identify all encrypted hosts via canary
files and SMB traffic anomalies), preserving backups, engaging legal counsel,
and triggering the breach-notification timer.

## phishing

Phishing response: quarantine the message tenant-wide, pull URL telemetry from
the secure web gateway, force credential rotation for confirmed clickers, and
review session token logs for impossible-travel anomalies.

## insider-misuse

Suspected insider misuse: preserve account artefacts, place a litigation hold,
disable interactive logons via just-in-time admin revocation, and engage HR
and legal before any disciplinary action.
