#!/usr/bin/env python3
"""
Verification script for kafka-config skill.
Validates the skill structure and content.
"""

import sys
import os
from pathlib import Path


def verify_skill(skill_dir: Path) -> bool:
    """Verify the kafka-config skill structure."""
    errors = []

    # Check SKILL.md exists
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append("SKILL.md not found")
        return False

    # Read and validate frontmatter
    with open(skill_md, 'r') as f:
        content = f.read()

    if '---' not in content[:50]:
        errors.append("SKILL.md missing YAML frontmatter")

    if 'name: kafka-config' not in content:
        errors.append("SKILL.md missing correct name in frontmatter")

    if 'description:' not in content:
        errors.append("SKILL.md missing description in frontmatter")

    # Check for required asset templates
    assets_dir = skill_dir / "assets"
    required_assets = [
        "topic-template.yaml",
        "kafka-user-template.yaml",
        "consumer-config-template.py",
        "producer-config-template.py",
    ]

    for asset in required_assets:
        asset_path = assets_dir / asset
        if not asset_path.exists():
            errors.append(f"Missing required asset: {asset}")

    # Check for reference documents
    refs_dir = skill_dir / "references"
    required_refs = [
        "performance-matrix.md",
        "security-patterns.md",
    ]

    for ref in required_refs:
        ref_path = refs_dir / ref
        if not ref_path.exists():
            errors.append(f"Missing required reference: {ref}")

    # Check for scripts
    scripts_dir = skill_dir / "scripts"
    if not (scripts_dir / "calculate_performance_params.py").exists():
        errors.append("Missing calculate_performance_params.py script")

    if errors:
        print("✗ kafka-config skill validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False

    print("✓ kafka-config skill is valid")
    return True


if __name__ == "__main__":
    skill_dir = Path(__file__).parent.parent
    success = verify_skill(skill_dir)
    sys.exit(0 if success else 1)
