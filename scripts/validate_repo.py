from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
PLUGIN = ROOT / "plugins" / "chen-investment-system"
MANIFEST = PLUGIN / ".codex-plugin" / "plugin.json"
SKILLS = PLUGIN / "skills"


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssertionError(f"invalid JSON: {path}: {exc}") from exc


def validate_marketplace() -> None:
    marketplace = load_json(MARKETPLACE)
    assert marketplace.get("name") == "chen-investment-system"
    entries = marketplace.get("plugins")
    assert isinstance(entries, list) and len(entries) == 1
    entry = entries[0]
    assert entry.get("name") == "chen-investment-system"
    assert entry.get("source") == {
        "source": "local",
        "path": "./plugins/chen-investment-system",
    }
    assert entry.get("policy") == {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }
    assert entry.get("category") == "Productivity"


def validate_manifest() -> None:
    manifest = load_json(MANIFEST)
    assert manifest.get("name") == PLUGIN.name
    assert re.fullmatch(r"\d+\.\d+\.\d+", str(manifest.get("version", "")))
    assert manifest.get("skills") == "./skills/"
    assert manifest.get("license") == "MIT"
    for key in ("description", "author", "interface"):
        assert manifest.get(key), f"manifest missing {key}"


def validate_local_links() -> None:
    markdown_link = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for markdown in ROOT.rglob("*.md"):
        if any(part in {".git", "work", "outputs"} for part in markdown.parts):
            continue
        text = markdown.read_text(encoding="utf-8")
        for target in markdown_link.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            relative = target.split("#", 1)[0]
            resolved = (markdown.parent / relative).resolve()
            assert resolved.exists(), f"broken link in {markdown}: {target}"


def validate_safety() -> None:
    assert not (SKILLS / "buffett").exists(), "Buffett upstream source must not be bundled"
    assert not (SKILLS / "public-equity-investing").exists(), "OpenAI plugin source must not be bundled"

    patterns = [
        re.compile(r"gh[oprsu]_[A-Za-z0-9]{20,}"),
        re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
        re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
        re.compile(r"-----BEGIN (?:RSA|OPENSSH|EC|DSA) PRIVATE KEY-----"),
        re.compile(r"[A-Za-z]:\\(?:Users|codex)\\", re.IGNORECASE),
    ]
    excluded = {Path(__file__).resolve()}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.resolve() in excluded:
            continue
        if any(part in {".git", "work", "outputs", "__pycache__"} for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in patterns:
            assert not pattern.search(text), f"sensitive pattern in {path}: {pattern.pattern}"


def validate_cis() -> None:
    validator = SKILLS / "cis" / "scripts" / "validate_cis.py"
    result = subprocess.run(
        [sys.executable, str(validator)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr.strip() or result.stdout.strip())


def main() -> int:
    validate_marketplace()
    validate_manifest()
    validate_local_links()
    validate_safety()
    validate_cis()
    print("Repository validation passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Repository validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
