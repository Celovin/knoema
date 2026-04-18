# Security Policy

## Supported Versions

Knoema Engine is pre-1.0 software. Security fixes are applied to the `main` branch and the latest tagged release line.

| Version | Supported |
| --- | --- |
| `main` | Yes |
| `v0.1.x` | Yes |
| Older snapshots | No |

## Reporting a Vulnerability

Report suspected vulnerabilities privately to `hello@celovin.com`.

Include:

- affected version or commit hash;
- affected file, command, or workflow;
- reproduction steps;
- expected impact;
- whether a credential, private dataset, or user-supplied API key is involved.

Do not open a public issue for exploitable vulnerabilities or leaked credentials.

## Scope

In scope:

- Python package code under `src/knoema`;
- CLI, dashboard, playground, SaaS scaffold, website, and adapters;
- GitHub Actions workflows;
- dependency metadata and release artifacts;
- documentation that could cause unsafe operational use.

Out of scope:

- attacks against third-party LLM providers;
- social engineering;
- denial-of-service load testing against hosted services without prior permission;
- public-safety use with real incidents, real people, or operational law-enforcement data.

## Secrets And API Keys

Knoema examples must not persist user API keys. Playground keys are session inputs only and should never be logged, committed, or stored in exported JSONL files.

The repository ignores `.env`, `.env.*`, private keys, SQLite databases, runtime logs, and private planning files. If a secret is accidentally committed:

1. revoke the credential immediately;
2. rotate it at the provider;
3. remove it from git history with `git filter-repo` or BFG Repo-Cleaner;
4. force-push the cleaned history only after coordination;
5. review provider audit logs for abuse.

## Public-Safety Boundary

All public-safety examples must remain fictional, synthetic, and non-identifying. Knoema is not designed for prediction, suspect scoring, surveillance, or enforcement automation.

## Local Audit Commands

Install the security tool extra:

```bash
pip install -e ".[security]"
```

Run the current Phase 34 checks:

```bash
bandit -r src
pip-audit
safety check
cyclonedx-py environment .venv --pyproject pyproject.toml --mc-type library --of JSON -o docs/security/knoema-sbom.cdx.json
cd website && npm audit
cd ../sdk/typescript && npm audit
```

Current audit report: [Phase 34 Security Audit](security/audit_2026-04-18.md).

## GitHub Security Settings

Dependabot version update configuration is committed at `.github/dependabot.yml`.

Repository-level GitHub security settings were checked on 2026-04-18. `secret_scanning`, `secret_scanning_push_protection`, and `dependabot_security_updates` were disabled at that time. Enabling those settings requires an explicit repository-owner action because it changes external security configuration.
