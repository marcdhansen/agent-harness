import json
from pathlib import Path


def generate_checklist_md():
    checklist_dir = Path(".agent/rules/checklists")
    output_file = Path(".agent/docs/SOP_COMPLIANCE_CHECKLIST.md")

    if not checklist_dir.exists():
        print(f"Error: {checklist_dir} not found")
        return

    md_content = "# 📋 Standard Operating Procedure (SOP) Compliance Checklist (Generated)\n\n"
    md_content += "> **Source of Truth**: The JSON files in `.agent/rules/checklists/` define the authoritative workflow.\n\n"
    md_content += "## ⚡ Phases\n\n"

    phases = [
        "initialization",
        "planning",
        "execution",
        "finalization",
        "retrospective",
        "clean_state",
    ]

    for phase_id in phases:
        json_path = checklist_dir / f"{phase_id}.json"
        if not json_path.exists():
            continue

        with open(json_path) as f:
            data = json.load(f)
            if "phases" in data and data["phases"]:
                phase = data["phases"][0]
                md_content += f"### {phase['name']} — {phase['status']}\n\n"
                if phase.get("description"):
                    md_content += f"{phase['description']}\n\n"

                for check in phase.get("checks", []):
                    md_content += (
                        f"- [ ] **{check['description']}** (Validator: `{check['validator']}`)\n"
                    )
                md_content += "\n"

    # Create directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        f.write(md_content)

    print(f"Successfully generated {output_file}")


if __name__ == "__main__":
    generate_checklist_md()
