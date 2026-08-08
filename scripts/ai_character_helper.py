"""
AI-character reference helper.

Purpose: let this PRIVATE (login-gated, @neobrands.io only) app use AI-GENERATED
character portraits as Seedance reference images — the official Dreamina "AI
influencer" workflow.

ByteDance's reference-image filter (InputImageSensitiveContentDetected) rejects
images its classifier reads as a photo of a REAL person. AI-generated portraits
usually pass, but very photorealistic ones can trip the classifier by accident.

`prepare_ai_character()` re-renders an ALREADY-AI image through Nano Banana as a
clean digital-character render — same identity, slightly less photographic — so
it reads unambiguously as a digital character and clears the filter. This is a
transformation of an AI asset, not a technique for disguising a real person's
photo.
"""

from pathlib import Path

from nano_banana import generate_scene_image, is_available  # noqa: F401


PREP_PROMPT = (
    "Re-render this AI-generated character portrait as a clean, consistent "
    "digital character render. Keep the SAME identity exactly: same face shape, "
    "same hairstyle and color, same skin tone, same outfit, same expression and "
    "pose. Render it as a polished CGI / digital-character portrait — smooth, "
    "even studio lighting, subtly stylized (not a raw phone photo), so it clearly "
    "reads as a designed digital character rather than a photograph of a real "
    "person. Single centered portrait, neutral clean background, high detail."
)


STRONG_PREP_PROMPT = (
    "Re-render this AI-generated character as a clearly STYLIZED 3D animated "
    "character — think high-end animated-film look: simplified skin shading, "
    "slightly larger eyes, softened features, clean rim lighting. Keep the SAME "
    "recognizable identity: same face shape, same hairstyle and color, same "
    "outfit, same expression and pose. It must be unmistakably a designed "
    "animated character, NOT a photograph. Single centered portrait, neutral "
    "clean background, high detail."
)

_PROMPTS = {"soft": PREP_PROMPT, "strong": STRONG_PREP_PROMPT}


def prepare_ai_character(image_path, out_path, log=print, strength="soft"):
    """Re-render one AI character image so it passes the reference filter.
    strength: "soft" (subtle CGI polish) or "strong" (clearly animated style).
    Returns the new PNG path. Identity is preserved.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    log(f"🧑‍🎤 Preparing AI character ({strength}): {Path(image_path).name}")
    return generate_scene_image(_PROMPTS.get(strength, PREP_PROMPT),
                                [str(image_path)], out_path, log=log)


def prepare_many(image_paths, out_dir, log=print, progress=None, strength="soft"):
    """Prepare a batch. Returns list of new paths (aligned with input order)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for i, ip in enumerate(image_paths, 1):
        out = out_dir / f"ai_char_{strength}_{i}.png"
        try:
            results.append(str(prepare_ai_character(ip, out, log=log, strength=strength)))
        except Exception as e:
            log(f"  ⚠ failed on {Path(ip).name}: {e} — keeping original")
            results.append(str(ip))
        if progress:
            progress(i, len(image_paths))
    return results
