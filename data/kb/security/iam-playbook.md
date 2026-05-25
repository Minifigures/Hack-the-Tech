# IAM Playbook

## mfa-recovery

If a user loses their primary MFA factor (for example a lost or stolen phone)
the response is **not** to disable MFA. Disabling MFA, even temporarily, opens
the account to takeover and bypasses the controls auditors rely on.

The supported recovery flow is:

1. Identity-verified self-service recovery using a pre-enrolled secondary
   factor (hardware security key, recovery codes, or a registered backup
   device).
2. If no secondary factor is enrolled, issue a temporary hardware token
   (overnight courier for executives travelling internationally) and use the
   help-desk identity-verification script with secondary verification by a
   trusted manager.
3. For genuine break-glass scenarios, use the documented emergency-access
   workflow, which requires multi-party approval, time-boxed access, and a
   full session recording for post-event review.

After any recovery, audit the account for unfamiliar device enrolments and
session tokens, and re-enrol the user in MFA before re-enabling normal access.

## privileged-access

Privileged accounts (domain admin, root, cloud root) must use phishing-
resistant factors (FIDO2 / WebAuthn), be assigned via just-in-time elevation,
and operate from a privileged access workstation. Standing privileged access
should not exist outside of break-glass identities.
