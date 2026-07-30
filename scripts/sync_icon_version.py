#!/usr/bin/env python3
"""Stamps manifest.json's icon src URLs with a content-hash query string
whenever icon-192.png/icon-512.png change.

Run automatically by the pre-commit hook (.githooks/pre-commit). Safe to run
manually too -- it's a no-op if the icon files haven't changed.

Android/Chrome's installed-PWA (WebAPK) icon-update check only re-fetches an
icon when its URL in the manifest changes -- it diffs the icons array, not
pixel bytes -- so overwriting icon-192.png/icon-512.png in place would never
be noticed by an existing install, or even by a fresh "Add to Home Screen"
after an Android uninstall (which doesn't clear Chrome's site data for the
origin). Appending a content hash to the src query string gives every icon
change a new URL, which is what actually triggers Chrome to pick it up.
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "manifest.json"


def main():
    manifest_text = MANIFEST_PATH.read_text(encoding="utf-8")

    def replace_icon_src(m):
        rel_path = m.group(1)
        file_path = ROOT / rel_path
        if not file_path.is_file():
            sys.exit(f"manifest.json references missing icon: {rel_path}")
        digest = hashlib.sha256(file_path.read_bytes()).hexdigest()[:8]
        return f'"src": "{rel_path}?v={digest}"'

    new_manifest_text = re.sub(
        r'"src":\s*"(icon-(?:192|512)\.png)(?:\?v=[0-9a-f]+)?"',
        replace_icon_src,
        manifest_text,
    )

    if new_manifest_text == manifest_text:
        print("manifest.json icon URLs already up to date")
        return

    MANIFEST_PATH.write_text(new_manifest_text, encoding="utf-8")
    subprocess.run(["git", "add", str(MANIFEST_PATH)], cwd=ROOT, check=True)
    print("manifest.json icon URLs updated")


if __name__ == "__main__":
    main()
