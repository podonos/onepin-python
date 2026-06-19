# Security Policy

## Supported versions

`onepin` follows semantic versioning. Security patches are applied to the latest
published minor release on PyPI. Older minor lines do not receive backports.

| Version | Supported          |
| ------- | ------------------ |
| latest minor (`0.x`) | :white_check_mark: |
| older   | :x:                |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report privately via GitHub's [security advisory form](https://github.com/podonos/onepin-python/security/advisories/new).
We aim to acknowledge new reports within 2 business days.

If GitHub advisories are unavailable to you, email `security@onepin.ai`
with the details and we will follow up directly.

## Scope

In scope:

- The published `onepin` Python package on PyPI
- The hand-rolled CLI under `src/onepin/_cli/`
- Authentication and credential-storage paths (`~/.onepin/credentials`)
- Build, release, and supply-chain configuration in this repository

Out of scope:

- The upstream OpenAPI spec and Fern generator configuration (reported separately)
- Issues that require an already-compromised local environment (e.g., an attacker
  with shell access to the user's machine)
- Denial-of-service against the Onepin API itself (report to the API team directly)

## Disclosure

We coordinate disclosure with reporters. By default, we publish an advisory
within 90 days of the initial report, or sooner once a fix is released.
