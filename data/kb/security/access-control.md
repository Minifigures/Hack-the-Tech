# Access Control

## least-privilege

The principle of least privilege (PoLP) requires that every user, process, or
system component operate using the minimum set of privileges necessary to
perform its function. PoLP limits the blast radius from compromise or human
error and is foundational to a defense-in-depth strategy.

Operationally, PoLP appears as: role-based access control (RBAC) with
narrowly scoped roles, just-in-time elevation for privileged operations,
short-lived credentials for automation, and periodic access reviews.

## separation-of-duties

Separation of Duties (SoD) requires that no single individual can both initiate
and approve a sensitive change. Examples: a developer cannot also deploy to
production, a payment originator cannot also approve the wire, an account
creator cannot also assign privileged roles.

## just-in-time

Just-in-time (JIT) access elevates a user to a privileged role only for the
duration of an approved task. JIT pairs with privileged-access workstations,
break-glass approval flow, and full session recording for audit.
