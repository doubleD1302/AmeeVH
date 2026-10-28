#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verification gate for stella-launcher-auto-update-assurance skill."""

import sys, os, re, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

def check_all():
    print("=== VERIFYING AUTO-UPDATE ASSURANCE INVARIANTS ===")
    errors = []

    # 1. Check VersionCompatibility.java has wildcard support
    vc_file = ROOT / "android/app/src/main/java/com/stellasora/viethoa/localadb/VersionCompatibility.java"
    if not vc_file.is_file():
        errors.append(f"Missing {vc_file}")
    else:
        vc_text = vc_file.read_text(encoding="utf-8")
        if 'candidate.equals("*")' not in vc_text and 'candidate.equals("*")' not in vc_text.replace(" ", ""):
            errors.append("VersionCompatibility.java does not support wildcard '*' matching!")

    # 2. Check PC launcher self_update.py has parent_pid, taskkill and rename logic
    su_file = ROOT / "launcher/core/self_update.py"
    if not su_file.is_file():
        errors.append(f"Missing {su_file}")
    else:
        su_text = su_file.read_text(encoding="utf-8")
        if "parent_pid" not in su_text:
            errors.append("launcher/core/self_update.py missing parent_pid tracking!")
        if "taskkill" not in su_text:
            errors.append("launcher/core/self_update.py missing taskkill parent process handling!")
        if "target.rename" not in su_text:
            errors.append("launcher/core/self_update.py missing target.rename Windows lock bypass!")

    # 3. Check PC launcher config
    cfg_file = ROOT / "launcher/core/config.py"
    if not cfg_file.is_file():
        errors.append(f"Missing {cfg_file}")

    # 4. Check Android build.gradle
    bg_file = ROOT / "android/app/build.gradle"
    if not bg_file.is_file():
        errors.append(f"Missing {bg_file}")
    else:
        bg_text = bg_file.read_text(encoding="utf-8")
        vcode_match = re.search(r"versionCode\s+(\d+)", bg_text)
        if not vcode_match:
            errors.append("Could not extract versionCode from build.gradle")
        else:
            vcode = int(vcode_match.group(1))
            if vcode < 8:
                errors.append(f"versionCode in build.gradle is {vcode}; must be >= 8 for new release!")

    if errors:
        print("\n❌ FAILED INVARIANTS:")
        for err in errors:
            print(" -", err)
        return False
    else:
        print("\n✅ ALL AUTO-UPDATE ASSURANCE INVARIANTS PASSED!")
        return True

if __name__ == "__main__":
    success = check_all()
    sys.exit(0 if success else 1)
