#!/usr/bin/env python3
"""
Verification script for helm-chart-generator skill.
Validates the skill structure and required components.
"""

import sys
from pathlib import Path

def verify_skill(skill_path: Path) -> tuple[bool, list[str]]:
    """
    Verify the helm-chart-generator skill structure.

    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = []

    # Check SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        errors.append("SKILL.md not found")
        return False, errors

    # Read SKILL.md content
    content = skill_md.read_text()

    # Check frontmatter
    if not content.startswith("---"):
        errors.append("SKILL.md missing YAML frontmatter")

    # Check required fields in frontmatter
    if "name: helm-chart-generator" not in content:
        errors.append("Missing or incorrect 'name' in frontmatter")

    if "description:" not in content:
        errors.append("Missing 'description' in frontmatter")

    # Check trigger phrases in description
    if "create Helm chart" not in content or "Kubernetes" not in content:
        errors.append("Description missing key trigger phrases")

    # Check for "NOT for" exclusions
    if "NOT for:" not in content:
        errors.append("Description should include 'NOT for:' exclusions")

    # Check script exists
    script_path = skill_path / "scripts" / "generate_helm_chart.py"
    if not script_path.exists():
        errors.append("scripts/generate_helm_chart.py not found")
    else:
        # Verify script is executable
        script_content = script_path.read_text()
        if "def generate_helm_chart" not in script_content:
            errors.append("generate_helm_chart.py missing main function")

        if "if __name__ == \"__main__\":" not in script_content:
            errors.append("generate_helm_chart.py not executable as script")

    # Check references directory
    references_path = skill_path / "references"
    if references_path.exists():
        best_practices = references_path / "helm-best-practices.md"
        if not best_practices.exists():
            errors.append("references/helm-best-practices.md not found")

    # Check body content sections
    required_sections = [
        "## When to Use",
        "## Quick Start",
        "## Generated Structure",
        "## Common Workflows"
    ]

    for section in required_sections:
        if section not in content:
            errors.append(f"Missing required section: {section}")

    # Check for code examples
    if "```bash" not in content:
        errors.append("Missing bash code examples")

    if "```yaml" not in content:
        errors.append("Missing YAML code examples")

    return len(errors) == 0, errors

def main():
    if len(sys.argv) > 1:
        skill_path = Path(sys.argv[1])
    else:
        skill_path = Path(__file__).parent.parent

    print(f"Verifying skill at: {skill_path}")

    is_valid, errors = verify_skill(skill_path)

    if is_valid:
        print("✓ helm-chart-generator valid")
        sys.exit(0)
    else:
        print("✗ Validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
