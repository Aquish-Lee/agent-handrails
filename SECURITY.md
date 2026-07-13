# Security Policy

## Supported versions

| Version | Supported |
| --- | --- |
| `v0.1.0-alpha.2` | Yes, after publication |
| `v0.1.0-alpha.1` | No; historical rollback baseline |
| Unreleased `main` | Best effort |

Agent Handrails is alpha software. Support means the maintainers will assess
reports and publish a fix/advisory when warranted; it is not a stability or
response-time guarantee.

## Reporting a vulnerability

Do not open a public Issue for a suspected vulnerability. Use GitHub's private
[Report a vulnerability](https://github.com/Aquish-Lee/agent-handrails/security/advisories/new)
form. Include:

- affected tag/commit and installation mode (Plugin or Raw);
- impact and threat model;
- minimal reproduction or malicious input;
- whether state mutation, path ownership, secret exposure, or claim integrity is involved;
- suggested mitigation, if known.

Maintainers aim to acknowledge a report within 7 days and provide an initial
triage within 14 days. Complex reports may take longer. Please allow a
reasonable remediation window before disclosure.

## Security scope

Security-sensitive surfaces include the bundle installer/uninstaller,
filesystem ownership checks, boundary canonicalization and drift detection,
plugin packaging, generated scripts, and prompt behavior that could cause
unauthorized destructive operations or disclose ignored local content.

General model mistakes, unsupported platforms, and evidence-quality bugs are
normally product defects unless they cross a security boundary; report those
through the Bug form.
