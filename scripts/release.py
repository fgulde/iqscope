"""Create the next release tag (vMAJOR.MINOR.PATCH) on the current commit.

Usage: python scripts/release.py {patch|minor} [message]

The package version is derived from the git tag (hatch-vcs), so tagging is releasing.
The tag stays local; push it with `git push origin master <tag>`.
"""

import re
import subprocess
import sys

TAG_PATTERN = re.compile(r"v(\d+)\.(\d+)\.(\d+)")


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def next_tag(latest: str, part: str) -> str:
    match = TAG_PATTERN.fullmatch(latest)
    if match is None:
        sys.exit(f"latest tag {latest!r} is not of the form vX.Y.Z")
    major, minor, patch = (int(group) for group in match.groups())
    if part == "minor":
        return f"v{major}.{minor + 1}.0"
    return f"v{major}.{minor}.{patch + 1}"


def main(argv: list[str]) -> None:
    if not argv or argv[0] not in ("patch", "minor") or len(argv) > 2:
        sys.exit(__doc__)
    part = argv[0]
    message = argv[1].strip() if len(argv) > 1 else ""

    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch != "master":
        sys.exit(f"refusing to tag on branch {branch!r} (expected master)")
    if git("status", "--porcelain"):
        sys.exit("working tree is not clean: commit your changes before tagging")
    already_tagged = [
        tag for tag in git("tag", "--points-at", "HEAD").splitlines() if TAG_PATTERN.fullmatch(tag)
    ]
    if already_tagged:
        sys.exit(f"HEAD is already tagged {already_tagged[0]}")

    latest = git("describe", "--tags", "--abbrev=0", "--match", "v[0-9]*")
    tag = next_tag(latest, part)
    git("tag", "-a", tag, "-m", message or tag)
    print(f"{latest} -> {tag} (local only)")
    print(f"push with: git push origin master {tag}")


if __name__ == "__main__":
    main(sys.argv[1:])
