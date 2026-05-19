"""Shared language constraint — Seedance 2.0 only renders English dialogue reliably."""

ENGLISH_DIALOGUE_RULE = """🌍 SEEDANCE 2.0 LANGUAGE CONSTRAINT (NON-NEGOTIABLE):
All spoken dialogue, voiceover, and lip-sync MUST be in ENGLISH. Seedance 2.0 cannot reliably produce Hebrew, Arabic, Russian, Chinese, Spanish, or any other language — the result is garbled phonetics. This applies even when the audience is Israeli, MENA, CIS, etc.

For non-American audiences, simulate cultural identity through:
  - PERSONA: heritage, look, body type, clothing match the audience (e.g. Israeli = Ashkenazi / Mizrahi / Sephardi looks, casual Israeli wardrobe)
  - SETTING: real local environments (e.g. Israeli = Tel Aviv kitchen, Jerusalem coffee shop, Israeli supermarket)
  - ACCENT: written as "Israeli-accented English", "light Spanglish (Latina-American)", "Arabic-accented English (Pan-Arab)", "Slavic-accented English (CIS)", etc. — Seedance handles accent fairly well in English.
  - LIGHT cultural code-switching: 1 word at most (e.g. "yalla" for Israeli/Arab, "che" for Argentinian) — but only if Seedance can pronounce it cleanly. Avoid entire Hebrew/Arabic phrases.

NEVER write:
  - Dialogue in Hebrew letters (אנחנו, שלום, וכו')
  - Dialogue in Cyrillic / Arabic / Chinese / Hebrew text — Seedance will not pronounce it
  - "She says in Hebrew/Arabic/Russian": Seedance ignores the language directive and reads the literal text

ALWAYS write:
  - All dialogue in English text, even when the persona is non-American
  - Accent cue: "she speaks with a light Israeli accent" / "his English carries a Mexican-American lilt"
  - Persona/setting matches audience; speech is English."""
