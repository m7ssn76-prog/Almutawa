from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BLOCKED_SUFFIXES = {
    ".7z",
    ".aac",
    ".aif",
    ".aiff",
    ".amr",
    ".bak",
    ".caf",
    ".db",
    ".doc",
    ".docx",
    ".flac",
    ".key",
    ".m4a",
    ".m4v",
    ".mov",
    ".mp3",
    ".mp4",
    ".ogg",
    ".opus",
    ".p12",
    ".pdf",
    ".pem",
    ".pfx",
    ".ppt",
    ".pptx",
    ".rar",
    ".sqlite",
    ".sqlite3",
    ".wav",
    ".webm",
    ".wma",
    ".xls",
    ".xlsx",
    ".zip",
}

BLOCKED_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".replit",
    "credentials.json",
    "netlify.toml",
    "render.yaml",
    "render.yml",
    "secrets.json",
    "vercel.json",
}

BLOCKED_FILENAME_PATTERNS = {
    "plaintext key filename": re.compile(
        r"(?i)(?:^|[._-])(?:aes\d*|encryption)?[._-]?key(?:[._-]|$)"
    ),
    "password-bearing filename": re.compile(
        r"(?i)(?:^|[._-])(?:owner[._-]?)?(?:password|passwd|pwd)(?:[._-]|$)"
    ),
    "credential-bearing filename": re.compile(
        r"(?i)(?:^|[._-])(?:credential|secret|access[._-]?token|api[._-]?key)(?:[._-]|$)"
    ),
}

IGNORED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
}

TEXT_SUFFIXES = {
    "",
    ".cfg",
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

CONCRETE_PATTERNS = {
    "private-key header": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    ),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "OpenAI-style secret": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "Slack token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    "Google API key": re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    "Bearer credential": re.compile(
        r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}\b", re.IGNORECASE
    ),
    "JWT-like token": re.compile(
        r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"
    ),
    "company-specific marker": re.compile(r"technipfmc", re.IGNORECASE),
    "company email domain": re.compile(r"@technipfmc\.com", re.IGNORECASE),
    "company internal URL": re.compile(
        r"https?://[^\s]+technipfmc[^\s]*", re.IGNORECASE
    ),
}

ASSIGNMENT_PATTERNS = {
    "credential assignment": re.compile(
        r"(?i)(?:api[_-]?key|client[_-]?secret|password|access[_-]?token|authorization)"
        r"\s*[:=]\s*['\"][^'\"\n]{8,}['\"]"
    ),
}

CODE_OR_CONFIG_SUFFIXES = {
    ".cfg",
    ".ini",
    ".js",
    ".json",
    ".py",
    ".sh",
    ".toml",
    ".yaml",
    ".yml",
}

REQUIRED_PUBLIC_SAFE_MARKERS = {
    Path("README.md"): (
        "PUBLIC-SAFE REPOSITORY MODE",
        "Evidence freshness rule",
    ),
    Path("PUBLICATION_POLICY.md"): (
        "PUBLIC-SAFE REPOSITORY MODE",
        "Evidence and status freshness",
    ),
}

AUDIT_POLICY = Path(".asa/audit-policy.json")
SELF = Path("scripts/repo_policy_check.py")


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        files.append(relative)
    return sorted(files)


def validate_public_safe_governance() -> list[str]:
    violations: list[str] = []

    for relative, markers in REQUIRED_PUBLIC_SAFE_MARKERS.items():
        path = ROOT / relative
        if not path.is_file():
            violations.append(f"missing public-safe governance file: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                violations.append(
                    f"missing public-safe governance marker {marker!r}: {relative}"
                )

    policy_path = ROOT / AUDIT_POLICY
    if not policy_path.is_file():
        violations.append(f"missing audit policy: {AUDIT_POLICY}")
        return violations

    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        violations.append(f"invalid audit policy JSON: {AUDIT_POLICY}: {exc}")
        return violations

    visibility_policy = policy.get("repository_visibility_policy", {})
    if visibility_policy.get("mode") != "public_safe":
        violations.append("audit policy repository visibility mode must be 'public_safe'")

    freshness_rule = policy.get("freshness_rule", {})
    if freshness_rule.get("dated_records") != "historical_snapshot":
        violations.append("dated .asa records must be classified as historical_snapshot")
    if freshness_rule.get("current_state_source") != "live_verification_required":
        violations.append("current state must require live verification")

    if policy.get("classification") != "Internal Test Only":
        violations.append("audit policy classification must remain 'Internal Test Only'")

    return violations


def scan() -> list[str]:
    violations = validate_public_safe_governance()

    for relative in iter_files():
        path = ROOT / relative
        lower_name = path.name.lower()

        if lower_name in BLOCKED_NAMES:
            violations.append(f"blocked filename: {relative}")

        for label, pattern in BLOCKED_FILENAME_PATTERNS.items():
            if pattern.search(lower_name):
                violations.append(f"{label}: {relative}")

        if path.suffix.lower() in BLOCKED_SUFFIXES:
            violations.append(f"blocked file type: {relative}")

        if relative == SELF or path.suffix.lower() not in TEXT_SUFFIXES:
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for label, pattern in CONCRETE_PATTERNS.items():
            if pattern.search(text):
                violations.append(f"{label}: {relative}")

        if path.suffix.lower() in CODE_OR_CONFIG_SUFFIXES:
            for label, pattern in ASSIGNMENT_PATTERNS.items():
                if pattern.search(text):
                    violations.append(f"{label}: {relative}")

    return violations


def main() -> int:
    violations = scan()
    if violations:
        print("Repository policy check failed:")
        for item in violations:
            print(f"- {item}")
        print("Remove the protected material or obtain the required private review.")
        return 1

    print("Repository policy check passed: public-safe governance and configured content controls are satisfied.")
    print("This automated check does not replace human confidentiality review or live GitHub-state verification.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
