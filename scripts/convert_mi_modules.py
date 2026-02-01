"""
MAPS Module Converter

Converts healthcare-focused MI modules to MAPS-appropriate terminology.
This script documents the terminology mapping and provides helper functions
for manual or automated conversion of module JSON files.

Usage:
    python scripts/convert_mi_modules.py --module module_2.json --output module_2_maps.json

Terminology Mapping:
    patient/client          → customer (Customer-Facing) or colleague (Colleague-Facing)
    doctor/medical          → financial advisor / guidance / support
    treatment               → support / guidance
    smoking cessation       → spending habits / financial goals / performance improvement
    change talk             → goal acknowledgment / commitment language
    sustain talk            → hesitation / concerns
    resistance              → hesitation / pushback
    precontemplation        → not yet ready / not aware
    contemplation           → considering / exploring
    preparation             → planning / ready to start
    action                  → actively working on it
    maintenance             → staying on track
    therapeutic alliance    → professional relationship / working alliance
    session                 → meeting / conversation
    healthcare setting       → financial services / customer support / performance review

Content Classifications:
    - customer_facing: External customers/clients with money/financial issues
    - colleague_facing: Internal colleagues with performance/support issues
    - shared: Neutral content that applies to both contexts
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

# Complete terminology mapping for automated conversion
TERMINOLOGY_MAP = {
    "patient": "customer",
    "client": "customer",
    "doctor": "advisor",
    "medical": "financial",
    "healthcare": "financial services",
    "treatment": "guidance",
    "therapy": "coaching",
    "clinical": "professional",
    "smoking": "spending",
    "health": "financial",
    "therapeutic alliance": "professional relationship",
    "change talk": "goal acknowledgment",
    "sustain talk": "hesitation",
    "resistance": "hesitation",
    "precontemplation": "not yet ready",
}

CONTEXT_MAPS = {
    "customer_facing": {
        "patient": "customer",
        "client": "customer",
        "doctor": "financial advisor",
        "medical": "financial",
        "smoking": "overspending",
        "health": "financial",
    },
    "colleague_facing": {
        "patient": "colleague",
        "client": "team member",
        "doctor": "manager",
        "medical": "performance",
        "smoking": "performance issue",
        "health": "work performance",
    },
}


def convert_module(module: Dict[str, Any], context: str = "customer_facing") -> Dict[str, Any]:
    """Convert a module to MAPS terminology."""
    import copy
    from datetime import datetime

    converted = copy.deepcopy(module)

    # Update code
    if converted.get("code", "").startswith("mi-"):
        converted["code"] = "maps-" + converted["code"][3:]

    # Add content_type
    converted["content_type"] = context

    # Get mapping
    mapping = CONTEXT_MAPS.get(context, TERMINOLOGY_MAP)

    # Simple recursive text replacement
    def replace_text(obj):
        if isinstance(obj, str):
            result = obj
            for old, new in sorted(mapping.items(), key=lambda x: -len(x[0])):
                result = result.replace(old, new)
            return result
        elif isinstance(obj, dict):
            return {k: replace_text(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_text(item) for item in obj]
        return obj

    converted = replace_text(converted)

    # Fix specific fields that need manual adjustment
    if "persona_config" in converted:
        converted["persona_config"]["role"] = mapping.get("patient", "participant")

    if "maps_rubric" in converted:
        for dim in converted["maps_rubric"].get("dimensions", {}).values():
            if dim.get("description") == "Therapeutic Alliance":
                dim["description"] = "Professional Alliance"

    # Update timestamp
    converted["updated_at"] = datetime.now().isoformat() + "Z"

    return converted


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Convert MI modules to MAPS terminology")
    parser.add_argument("--module", "-m", required=True, help="Path to module JSON file")
    parser.add_argument("--output", "-o", help="Output path (default: adds _maps suffix)")
    parser.add_argument("--context", "-c", choices=["customer_facing", "colleague_facing", "shared"],
                        default="customer_facing", help="Content classification")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Show conversion without writing")

    args = parser.parse_args()

    with open(args.module, 'r', encoding='utf-8') as f:
        module = json.load(f)

    converted = convert_module(module, args.context)

    print(f"Original: {module.get('code')} - {module.get('title')[:50]}...")
    print(f"Converted: {converted.get('code')} - {converted.get('title')[:50]}...")
    print(f"Context: {args.context}")

    if not args.dry_run:
        output_path = args.output
        if not output_path:
            input_path = Path(args.module)
            stem = input_path.stem.replace("_maps", "")
            output_path = str(input_path.parent / f"{stem}_maps.json")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(converted, f, indent=2, ensure_ascii=False)
        print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
