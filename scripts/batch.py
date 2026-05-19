"""
Batch generator — runs all 4 ThunderFit ads in sequence.

Usage:
    python scripts/batch.py
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"

# prompt name (without .md) -> reference image (relative to project root)
PROMPT_TO_IMAGE = {
    "01_chef_male":      "assets/product/ring_male_thunderfit_v1.jpg",
    "02_crossfit_male":  "assets/product/ring_male_thunderfit_v1.jpg",
    "03_nurse_female":   "assets/product/ring_female_thunderfit_v1.jpg",
    "04_mother_female":  "assets/product/ring_female_thunderfit_v1.jpg",
}


def main():
    failures = []
    for prompt_name, image_rel in PROMPT_TO_IMAGE.items():
        prompt_file = PROMPTS_DIR / f"{prompt_name}.md"
        image_path = PROJECT_ROOT / image_rel

        if not prompt_file.exists():
            print(f"[skip] missing prompt: {prompt_file}")
            continue
        if not image_path.exists():
            print(f"[skip] missing image:  {image_path}")
            failures.append(prompt_name)
            continue

        print("\n" + "=" * 60)
        print(f"  {prompt_name}")
        print("=" * 60)

        cmd = [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "generate.py"),
            str(prompt_file),
            "--image", str(image_path),
            "--name", prompt_name,
        ]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"[FAIL] {prompt_name} returned code {result.returncode}")
            failures.append(prompt_name)

    print("\n" + "=" * 60)
    if failures:
        print(f"Batch finished with {len(failures)} failure(s): {failures}")
        sys.exit(1)
    print("Batch finished. All ads generated.")


if __name__ == "__main__":
    main()
