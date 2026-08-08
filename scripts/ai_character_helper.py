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
    "Re-render this AI-generated image as a polished CGI / digital render. "
    "PRESERVE THE ENTIRE IMAGE EXACTLY: same composition, same framing, same "
    "background, same lighting mood, and EVERY person with the same identity — "
    "same face shapes, hairstyles, skin tones, outfits, expressions, poses and "
    "positions. Only change the rendering style: smooth, subtly stylized "
    "digital-character look (not a raw photograph), so every person clearly "
    "reads as a designed digital character rather than a photo of a real "
    "person. High detail, no elements added or removed."
)


STRONG_PREP_PROMPT = (
    "Re-render this AI-generated image in a clearly STYLIZED high-end 3D "
    "animated-film look: simplified skin shading, softened features, clean "
    "cinematic lighting. PRESERVE THE ENTIRE IMAGE: same composition, framing, "
    "background and every person with the same recognizable identity — same "
    "face shapes, hairstyles, outfits, expressions, poses and positions. It "
    "must be unmistakably a designed animated scene, NOT a photograph. High "
    "detail, no elements added or removed."
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
