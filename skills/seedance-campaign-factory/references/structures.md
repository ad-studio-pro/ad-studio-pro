# Prompt Structures — 4 Templates for 4 Families

Each video format belongs to one of 4 families (see `format-catalog.md`). The
family determines which prompt structure to use. Same product, different
format → different prompt structure.

> ⚠️ ALWAYS use the structure matching the format's family. Don't apply
> Structure A (UGC) to a Hero shot — it produces a soft, weak product hero.
> Don't apply Structure B (Hero) to a Street Interview — it strips out the
> authenticity that makes UGC believable.

| Structure | Family | Style anchor | Cinematic vocab? | Length target |
|---|---|---|---|---|
| **A — 9-Layer UGC** | Family A (Formats 1–12) | `handheld` / `documentary` | ❌ NEVER | 100–260 words |
| **B — Multi-Shot Hero** | Family B (Formats 13–16) | `dramatic` / `premium` / `photorealistic` | ✅ YES | 120–300 words |
| **C — Cinematic TV Spot** | Family C (Formats 17–20) | `cinematic` / `dramatic` | ✅ YES (heavy) | 180–350 words |
| **D — 2-Second Viral Hook** | Family D (Formats 21–23) | varies (photorealistic / cinematic) | ✅ SELECTIVE | 150–280 words |

---

## Universal Rules (apply to ALL structures)

These are non-negotiable across all 23 formats:

1. **Seedance 2.0 reference syntax:** Use `@Image 1`, `@Image 2` … `@Image 9`
   for image refs. Use `@Video 1` for continuation refs (multi-chunk). Use
   `@Audio 1` for music/beat-sync refs.
2. **Consistency anchor:** Every prompt that references a product image MUST
   include: *"The product from @Image 1 must remain visually unchanged
   across all cuts — same label, same color, same orientation."*
3. **Motion specificity:** Every action verb gets a degree adverb (slowly,
   casually, deliberately, gently, briskly, mindfully). "She picks up X" → bad.
   "She slowly picks up X" → good.
4. **No on-screen rendered text:** Negative block always includes "no text
   overlay, no captions, no subtitles, no watermarks, no lower-third, no
   graphic typography, no brand callout banners." Text/captions are added
   in post-production (CapCut, DaVinci) — not rendered by Seedance.
5. **Aspect ratio + duration in prompt:** Mention in the opening line OR
   the footer.
6. **Product-specific negatives:** Pull from the Product Profile (jewelry →
   "no second ring on other hand", beverage → "no competitor bottle", etc.).
7. **Universal negatives:** "no plastic-looking skin, no oily sheen, no
   sweaty face, no acne, no breakouts."

---

# Structure A — 9-Layer UGC (Family A, Formats 1–12)

> Use for authentic, person-led, smartphone-feel content. **NEVER use
> cinematic vocabulary** — it breaks the UGC illusion. The whole point of
> UGC is "a real person filmed this on their phone."

## Forbidden Words (Structure A only)

Never include these in Structure A prompts — they degrade UGC authenticity:
`cinematic`, `professional`, `stunning`, `8k`, `studio`, `perfect`, `ARRI`,
`ALEXA`, `35mm`, `film grain` (as a stand-alone modifier), `polished`.

If you need a substitute:
- "cinematic" → leave out, or use `handheld feel`
- "professional" → `clean`, `intentional`
- "studio lighting" → `natural window light`, `overhead warm light`
- "perfect" → `clean`, `precise`

## Template

```
[LAYER 1 — FORMAT HEADER]
{N} seconds {style_anchor} {format-specific shot vocab},
filmed on smartphone, {lighting cue}, {camera angle/distance}.

→ style_anchor: `handheld` (default) or `documentary`.

[LAYER 2 — PERSON]
A {age} {gender} of {heritage} heritage,
{hair description},
wearing {outfit description},
{pick 2–3 skin reality cues from bank below}.

→ Skin reality cue bank: natural skin with visible texture · visible pores
  across nose and cheeks · slight unevenness in skin tone · minor undereye
  shadows · a hint of shine on forehead from natural oils · slight pinkness
  on cheeks and nose · a few expression lines when smiling · light freckles.
→ NEVER use: acne, pimples, breakouts, blemishes, rosacea.

[LAYER 3 — SETTING]
In {specific space} — {detail 1}, {detail 2}, {detail 3},
{atmosphere word} and real.

→ 3 specific lived-in objects (books on shelf, coffee mug, folded towel).

[LAYER 4 — PRODUCT INTRO]
{Pronoun} {action verb with adverb} the @Image 1
({explicit product description from image}) {how/where}.
The product from @Image 1 must remain visually unchanged across all cuts
— same label, same color, same orientation.

[LAYER 5 — SCRIPT BEATS]
{3–4 jump cuts with timestamps}:
[00:00] {Opening beat — hook moment, adverbs on every action}
[00:0X] {Beat 2}
[00:0X] {Beat 3}
[00:0X] {Closing beat — brand mention if applicable, in final beat only}

→ Dialogue word-count to duration: 1–8 words → 4–5s · 9–15 → 6–8s ·
  16–25 → 9–12s · 26–35 → 13–15s. Include at least one silent action beat.
→ Dialogue style: casual filler words (okay so, literally, like). Ends
  mid-thought or with a laugh — NOT polished sign-offs.
→ Brand mention only in closing beat; if 2+ syllable name, add: "she
  pronounces both syllables clearly with a small pause between them."

[LAYER 6 — TONE DIRECTION]
Throughout the video, the tone is {emotion 1}, {emotion 2}, {emotion 3} —
{behavior description}. {Explicit pacing cue}.

→ Pacing cue is MANDATORY. Pick one: "pauses between thoughts as if
  collecting the next word" / "leaves a beat of silence after each
  sentence" / "speaks at a relaxed, unhurried pace — no rushing" / "takes
  natural breaths between sentences."

[LAYER 7 — EDIT STYLE]
Each jump cut is {angle/distance variation}, {handheld feel / locked-off}.

[LAYER 8 — TECHNICAL FLAWS]
The lighting is {light type} — {one light flaw}.
The image is slightly imperfect — {pick 2–3 camera flaws}.
The sound is {audio source} — {audio details}.

→ Camera flaws bank: natural phone quality, not color graded · slight motion
  blur on fast movements · soft focus, nothing is tack sharp · visible grain
  in darker areas · auto white balance shift between cuts · natural lens
  vignetting on edges.
→ Audio source: direct from phone mic (room ambience, no music) / front
  camera mic (slightly tinny, room echo) / car interior acoustics (muffled).

[LAYER 9 — VIBE STATEMENT]
The overall feel is {adjective 1}, {adjective 2}, {adjective 3} —
{relatable metaphor in one sentence}.

[NEGATIVE]
no text overlay, no captions, no subtitles, no on-screen text, no watermarks,
no lower-third, no graphic typography, no brand callout banners,
{product-specific negatives from Product Profile},
no plastic-looking skin, no oily sheen, no sweaty face, no acne, no breakouts,
no excessive freckles, no makeup-blotches across face.
```

## Example (Format 3 — Product Review, for a silicone ring)

```
10 seconds handheld honest review handheld talking head, filmed on smartphone,
soft window daylight, casual handheld selfie angle.

A 28-year-old woman of Mexican-American heritage, dark wavy hair pulled into
a loose bun, wearing a faded olive t-shirt, natural skin with visible texture,
slight pinkness on cheeks and nose, minor undereye shadows.

In her bedroom — a stack of books on the nightstand, a small potted succulent
on the windowsill, a folded throw blanket on the bed, cozy and real.

She casually holds up the @Image 1 (matte dark-grey silicone ring) to the
camera, turning it slowly so the brand impression catches the light. The ring
from @Image 1 must remain visually unchanged across all cuts — same dark-grey
color, same matte finish, same finger placement.

[00:00] She looks at the camera with a small smile, holding up her LEFT hand
deliberately to show the ring on her ring finger: "Okay so I've been wearing
this for like a week now."

[00:03] Quick jump cut, slightly closer — she taps the ring gently with her
right index finger, eyebrows raised slightly. "It's literally so comfortable
I forgot I had it on."

[00:06] Jump cut to medium close — she's slowly stretching her fingers,
looking at the ring on her LEFT hand. Right hand bare.

[00:09] Final shot — back to wide selfie angle, she smiles softly: "Thunder
Fit — she pronounces both syllables clearly with a small pause between them.
Worth it."

Throughout the video, the tone is honest, considered, decisive — she leaves
a beat of silence after each sentence before continuing. Each jump cut is
slightly closer or at a different angle, as if she filmed multiple takes and
edited the best bits. Handheld feel throughout.

The lighting is soft natural daylight — slightly uneven across her face.
The image is slightly imperfect — natural phone quality, not color graded,
soft focus on the edges, auto white balance shift between cuts. The sound is
direct from the phone mic — room tone with subtle outdoor traffic in the
background.

The overall feel is honest, lived-in, real — a friend telling you about
something she genuinely likes.

Negative: no text overlay, no captions, no subtitles, no on-screen text, no
watermarks, no lower-third, no graphic typography, no brand callout banners,
no second ring, no wedding band, no metal band on other finger, no diamond
ring elsewhere, no ring on right hand, no plastic-looking skin, no oily
sheen, no sweaty face, no acne, no breakouts, no excessive freckles.
```

---

# Structure B — Multi-Shot Hero (Family B, Formats 13–16)

> Use for kinetic, no-person product hero shots. Based on Higgsfield's
> official Multi-Shot pattern. Full cinematic vocabulary encouraged.

## Allowed Cinematic Vocabulary (Structure B)

These are ENCOURAGED in Structure B (and forbidden in A):
`cinematic lighting`, `35mm film quality`, `professional color grading`,
`film grain`, `depth of field mastery`, `ARRI ALEXA aesthetic`, `dramatic
lighting`, `sharp focus`, `high detail texture`, `premium feel`, `polished`.

Still avoid: `studio` (use `seamless backdrop` instead), `perfect` (use
`clean`, `precise`), `stunning` (use `striking`).

## Template

```
[OPENING LINE — Style descriptors]
{N} seconds {format} aesthetic, photorealistic, 35mm film quality,
professional color grading, sharp focus, high detail texture, film grain,
depth of field mastery, ARRI ALEXA aesthetic, {dramatic / premium / kinetic}
lighting.

[SCENE ESTABLISHMENT]
{Product description from @Image 1 — color, packaging, label details},
on a {backdrop description — seamless, surface, environment},
{ambient / lighting condition}.

The product from @Image 1 must remain visually unchanged across all cuts —
same label, same color, same orientation.

[SHOT-BY-SHOT BREAKDOWN]
Shot 1: {camera framing} as {action with degree adverb}, {camera movement},
{detail / lighting on product}.

Shot 2: {camera framing} as {action with degree adverb}, {camera movement},
{detail / lighting on product}.

Shot 3: {camera framing} as {action with degree adverb}, {camera movement},
{detail / lighting on product}.

[VFX (optional, in brackets)]
[VFX: {specific visual effect — splash droplets, light streaks, smoke
disperse}, rendered photorealistic, no CGI artifacting]

[AUDIO]
{Sound design description — sparse, atmospheric, brand-tone sting / drone /
chime / subtle drum hit / no music}.

[NEGATIVE]
no text overlay, no captions, no subtitles, no on-screen text, no watermarks,
no lower-third, no graphic typography, no brand callout banners,
{product-specific negatives},
no plastic-looking surface, no CGI sheen, no fake reflection.

[FOOTER]
Total: {duration}s / {N} shots / {aspect ratio}
```

## Example (Format 13 — Product Hero / Hyper Motion, for a silicone ring)

```
12 seconds product hero aesthetic, photorealistic, 35mm film quality,
professional color grading, sharp focus, high detail texture, film grain,
depth of field mastery, ARRI ALEXA aesthetic, dramatic side lighting from
upper left.

A matte dark-grey silicone ring from @Image 1, with subtle brand impression
visible on inner band, suspended in mid-air against a deep charcoal seamless
backdrop, dust particles drifting through warm light beams cutting across the
frame.

The product from @Image 1 must remain visually unchanged across all cuts —
same matte dark-grey color, same brand impression position, same band width.

Shot 1: Extreme close-up macro as the ring slowly rotates clockwise on its
own axis, light catching the matte texture in a slow sweep across the surface,
shallow depth of field with bokeh dust in foreground.

Shot 2: Medium wide shot as the ring deliberately drops from the upper frame
in slow motion, falling toward an unseen surface, dust particles disturbed in
its wake, single light beam following its descent.

Shot 3: Tight close-up as the ring lands gently on a polished dark stone
surface, slight bounce, settling into stillness with ripples of dust
expanding outward photorealistically.

Shot 4: Wide hero shot as the ring sits centered on the stone, dramatic side
light catches the matte finish, depth of field collapses to focus exclusively
on the ring, fade to dark.

[VFX: photorealistic dust particles, no CGI artifacting, natural air movement,
real material physics on the silicone bounce]

Audio: deep low atmospheric drone, single soft chime at Shot 3 landing,
ambient air, no music. Final shot fades to silence.

Negative: no text overlay, no captions, no subtitles, no on-screen text, no
watermarks, no lower-third, no graphic typography, no brand callout banners,
no second ring, no wedding band visible, no metal band, no diamond ring,
no plastic-looking surface, no CGI sheen, no fake reflection, no human hands.

Total: 12s / 4 shots / 9:16
```

---

# Structure C — Cinematic TV Spot (Family C, Formats 17–20)

> Use for narrative-driven, character-led, story-arc content. Full cinematic
> vocabulary encouraged. Always has a beginning / middle / end. The product
> moment is the climax, not the opening.

## Cinematic Vocabulary (Structure C)

ALL of Structure B's cinematic vocabulary applies, PLUS:
`narrative arc`, `character moment`, `cinematic blocking`, `golden hour`,
`magic hour`, `establishing shot`, `payoff frame`, `intimate moment`.

Still avoid: `studio` (use `controlled environment`), `perfect` (use
`intentional`), `stunning` (use `striking`).

## Template

```
[OPENING LINE — Cinematic aesthetic]
{N} seconds cinematic {format} spot, narrative arc, {tone words},
photorealistic, 35mm film quality, professional color grading, golden hour
lighting / magic hour / {specific lighting}, depth of field mastery,
ARRI ALEXA aesthetic, {handheld feel / locked-off camera}.

[CHARACTER + LOCATION ESTABLISHMENT]
{Character age / gender / heritage / outfit / vibe},
in {specific environment — restaurant / kitchen / outdoor / studio},
{ambient detail}.

[NARRATIVE ARC — 4 beats]
Beat 1 (Setup, 0–{X}s): {establishing moment — character in routine, not
yet aware of product}, {camera direction}, {emotion}.

Beat 2 (Tension, {X}–{Y}s): {something shifts — character notices product,
realizes need, or encounters problem}, {camera direction}, {emotion}.

Beat 3 (Product Moment, {Y}–{Z}s): {character uses product, key benefit
visible, hero shot of product naturally integrated}, {camera direction},
{emotion}. The product from @Image 1 must remain visually unchanged across
all cuts.

Beat 4 (Resolution, {Z}–{N}s): {character in better state, smiling /
satisfied / transformed}, {camera direction}, {emotion}.

[AUDIO]
{Music description — building from sparse to fuller / specific genre /
mood}, {ambient sound}, {optional brief dialogue}.

[NEGATIVE]
no text overlay, no captions, no subtitles, no on-screen text, no watermarks,
no lower-third, no graphic typography, no brand callout banners,
{product-specific negatives},
no plastic-looking skin, no oily sheen, no sweaty face, no acne.

[FOOTER]
Total: {duration}s / {N} beats / {aspect ratio}
```

## Example (Format 17 — TV Spot, for a silicone ring)

```
15 seconds cinematic brand spot, narrative arc, honest, focused, satisfied,
photorealistic, 35mm film quality, professional color grading, golden hour
lighting from a kitchen window, depth of field mastery, ARRI ALEXA aesthetic,
handheld feel with subtle drift.

A 32-year-old man of mixed-Asian-American heritage, athletic build, wearing
a faded blue t-shirt and grey chef's apron, working in a warm restaurant
kitchen during the late afternoon shift, soft golden light filtering through
the side window, faint ambient kitchen activity in the background.

Beat 1 (Setup, 0–4s): Wide handheld shot of the chef deliberately
plating a dish, hands moving with practiced precision, his metal wedding
band catching light briefly — he winces almost imperceptibly. Camera
drifts slowly closer. Tone: focused, slightly strained.

Beat 2 (Tension, 4–7s): Close-up on his hands as he carefully removes
the metal band and sets it deliberately on a clean towel. He looks at it
for a beat, frustrated, then opens a small drawer. Camera holds steady.
Tone: resolved.

Beat 3 (Product Moment, 7–11s): Medium close as he gently slides the matte
dark-grey @Image 1 silicone ring onto his LEFT ring finger, the band fitting
snugly without catching. He flexes his hand, the ring stays put. The product
from @Image 1 must remain visually unchanged across all cuts — same matte
dark-grey color, same brand impression, same band width. Camera follows
his hands with a soft drift. Tone: satisfied, relieved.

Beat 4 (Resolution, 11–15s): Wide handheld as he picks up his knife and
returns to plating, faster now, more confident, the ring no longer in his
awareness. He smiles briefly at his work. Camera pulls back to reveal the
busy kitchen. Tone: confident, in flow.

Audio: sparse warm piano building gently from Beat 1 through Beat 4, ambient
kitchen sounds (soft clinks, distant chatter, faint stovetop hum), no
dialogue, music resolves into warmth at final beat.

Negative: no text overlay, no captions, no subtitles, no on-screen text, no
watermarks, no lower-third, no graphic typography, no brand callout banners,
no metal band on right hand (he already removed it in Beat 2), no second ring
of any kind, no plastic-looking skin, no oily sheen, no sweaty face, no acne.

Total: 15s / 4 beats / 9:16
```

---

# Structure D — 2-Second Viral Hook (Family D, Formats 21–23)

> Use for scroll-stopping, pattern-breaking content. The first 2 seconds
> are the whole video — the rest is just delivering on the hook's promise.

## The 2-Second Framework

```
[0.0–0.3s] ATTENTION GRAB
- Visual shock, sound surprise, or pattern interrupt
- First frame/sound is unmissable
- ONE primary stimulus (not multiple competing elements)

[0.3–0.8s] CURIOSITY BUILD
- Incomplete information revealed
- Question posed (visual or verbal)
- Emotional setup begins
- Expectation established (to be subverted or confirmed)

[0.8–1.5s] MOMENTUM
- Confirm the hook is real (not clickbait)
- Move toward answer or climax
- Sound design reaches crescendo
- Visual energy sustained or increased

[1.5–2.0s] COMMITMENT MOMENT
- Viewer has decided: keep watching or scroll
- Deliver on the hook's promise
- Leave viewer wanting MORE
- Create transition into full video narrative
```

## Template

```
[OPENING — Viral aesthetic]
{N} seconds {viral / pattern-interrupt / impossible / transformation}
short-form video, vertical 9:16 phone framing, optimized for TikTok / Reels /
Shorts, {style anchor — photorealistic / cinematic / hyper-realistic}.

[2-SECOND HOOK BREAKDOWN — explicit timestamps]
[0.0-0.3s] {ATTENTION GRAB — one specific shock element with sound cue}

[0.3-0.8s] {CURIOSITY BUILD — what makes them wait}

[0.8-1.5s] {MOMENTUM — confirm hook, sound crescendo}

[1.5-2.0s] {COMMITMENT MOMENT — payoff visible, commitment locked}

[POST-HOOK CONTINUATION (2s–{N}s)]
{What happens after the hook lands — delivers the promise, sustains energy,
ends on satisfaction or question that demands rewatch.}

[PRODUCT MOMENT]
{Where and how the product from @Image 1 appears — must remain visually
unchanged across all cuts.}

[AUDIO]
{Sound design CRITICAL — describe specific sounds at each hook beat, music
build, optional voiceover. Silence allowed only if followed by impactful
sound.}

[NEGATIVE]
no text overlay, no captions, no subtitles, no on-screen text, no watermarks,
no lower-third, no graphic typography, no brand callout banners,
{product-specific negatives},
{family-A negatives if person visible: no plastic skin, no oily sheen, etc.}

[FOOTER]
Total: {duration}s / {hook type} / 9:16
```

## Example (Format 21 — Visual Shock, for a silicone ring)

```
8 seconds pattern-interrupt short-form video, vertical 9:16 phone framing,
optimized for TikTok / Reels / Shorts, photorealistic with hyper-realistic
physics.

[0.0-0.3s] ATTENTION GRAB: Extreme close-up macro of a heavy industrial
hammer slowly being raised against a deep black backdrop, dramatic side light
catches the metal head, sound: low ominous drone builds, single high-pitched
metal scrape.

[0.3-0.8s] CURIOSITY BUILD: Camera pulls back slightly to reveal the matte
dark-grey @Image 1 silicone ring sitting alone on a thick steel anvil, the
hammer poised directly above it. Sound: drone intensifies, breath hold.

[0.8-1.5s] MOMENTUM: Hammer accelerates downward in slow motion, motion blur
on the steel head, anvil reflects the descent. Sound: deep impact-anticipation
swell, "WHOOSH" of the swing.

[1.5-2.0s] COMMITMENT MOMENT: Hammer strikes the ring at full force,
shockwave ripples through the air, dust explodes outward — and the ring
springs back into perfect shape, completely undamaged, sitting calmly on the
anvil. Sound: massive metallic CLANG, then immediate silence.

Post-hook continuation (2-8s): Slow-motion pull-back shows the ring still
sitting on the anvil, completely intact, the hammer resting beside it. Camera
slowly orbits around the ring to reveal every angle — no dents, no scratches,
no damage. The matte dark-grey finish catches the light exactly as in @Image 1.
Final beat (6-8s): a single hand picks up the ring deliberately and slides it
onto a LEFT ring finger, flexes once, the ring holds. Cut to black.

The product from @Image 1 must remain visually unchanged across all cuts —
same matte dark-grey color, same brand impression, same band width, same
band orientation. Right hand bare throughout.

Audio: hammer impact at 1.5s is the loudest moment. After the strike, complete
silence for 0.3s, then ambient breath returns. No music until the final 2
seconds — soft confident drone enters as the ring is put on. Cut to black is
silent.

Negative: no text overlay, no captions, no subtitles, no on-screen text, no
watermarks, no lower-third, no graphic typography, no brand callout banners,
no second ring on the hand putting it on, no metal band visible, no wedding
band, no diamond, no damage to the ring at any frame, no CGI sheen on the
ring, no broken hammer, no exaggerated VFX particles.

Total: 8s / pattern-interrupt impact / 9:16
```

---

## Multi-Chunk Handling (all structures)

If a video exceeds 15 seconds (Seedance's hard limit), split into 2 chunks
with linked IDs (e.g. `v007 (1/2)` + `v008 (2/2)`):

- **Chunk A** ends on a complete sentence/action + 1–2s silent visual beat.
  Note in the structure's final beat: "Final 1-2s: silent visual beat —
  {character holds position / camera holds on product / etc.}"
- **Chunk B** opens with 0.5–1s silent visual beat that mirrors Chunk A's
  ending. Add to Chunk B's prompt:
  `"Open on the exact visual state at the last frame of @Video 1 —
  {explicit description} — then continue with: {Chunk B beats}"`.
- Pass Video A in Chunk B's `video_urls` as `@Video 1`.


# Multi-Product / Variant-Set Handling (2+ reference images)

When the user uploads N images that are N variants of the product (e.g. 7 ring
colors) — not just angles of one item — every structure (A/B/C/D) adds this
protocol on top of its template:

1. **Role map.** @Image 1..N — each image is ONE variant. Never merge variants,
   never render a "multi-pack" as a single object, never invent unreferenced colors.
2. **Rotation beats.** Each variant gets its own timestamped beat at a different
   camera angle/distance, naming its exact @Image number.
3. **Anchor repeatedly.** Name each @Image at the moment it appears AND in the
   global consistency line. Seedance needs mid-timeline reminders (official-manual
   pattern: references are anchored multiple times across the timeline).
4. **One at a time.** Only one variant visible at any moment; previous variant fully
   removed off-screen first. Wear/hold location anchored once (LEFT index finger /
   LEFT hand) and never moves.
5. **Global consistency line.** "All product references @Image 1 through @Image N
   must remain visually unchanged across cuts — same colors, materials, shapes as in
   their respective source images."
6. **Time budget.** ~2s hook + ≥2s per variant + ~2s close. 7 variants → 20s+
   (multi-chunk). Too short? Show fewer variants, never rush beats under 2s.
7. **Optional finale.** All variants laid out together, "each matching its own
   source image exactly".
8. **Negatives.** no duplicate products, no merged colors, no variant in two places
   at once, no extra invented variants.

**Reference sheets upgrade.** For maximum consistency, each variant's @Image should
ideally be a 6-panel reference sheet (front / left / right / top / macro / worn)
generated in Seedream 5.0 Lite or Nano Banana from the original photo — one sheet
gives Seedance every angle of that variant.
