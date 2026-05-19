# Format Catalog — 23 Video Formats Across 4 Families

This is the complete catalog of video formats supported by `seedance-campaign-factory`.
Each format belongs to one of 4 families. The family determines which prompt
structure to use (see `references/structures.md`).

The 4 families:

| Family | Structure file | Formats | Energy |
|---|---|---|---|
| **A — UGC Family** | Structure A (9-layer) | 1–12 | Authentic, person-led, smartphone feel |
| **B — Hero/Premium** | Structure B (Multi-Shot) | 13–16 | No-person product hero, kinetic, polished |
| **C — Cinematic** | Structure C (TV Spot) | 17–20 | Narrative-driven, story arc, polished |
| **D — Pattern Interrupt** | Structure D (2-second Hook) | 21–23 | Scroll-stopping, viral, surreal |

---

## Compatibility Matrix — Which formats fit which products

Use this table at Stage 1 (auto-detection) to decide which formats are enabled.
Legend: ✅ = strong fit, ⚠️ = optional / use sparingly, ❌ = skip

| Format | Jewelry | Beverage | Skincare | Apparel | Eyewear | Food | Electronics | Supplements | Home | App/SaaS | Pet | Service |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| 1 UGC Entertainment | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2 Street Interview | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| 3 Product Review | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 4 Unboxing | ⚠️ | ⚠️ | ✅ | ⚠️ | ✅ | ⚠️ | ✅ | ⚠️ | ✅ | ❌ | ⚠️ | ❌ |
| 5 ASMR | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ⚠️ | ⚠️ | ✅ | ❌ | ⚠️ | ❌ |
| 6 Tutorial / How-To | ❌ | ⚠️ | ✅ | ⚠️ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| 7 GRWM | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 8 Day-in-the-Life | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 9 POV First-Person | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | ❌ | ✅ | ✅ | ✅ | ⚠️ |
| 10 Reaction | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| 11 Storytime | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| 12 Virtual Try-On (UGC) | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 13 Product Hero / Hyper Motion | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ⚠️ | ❌ |
| 14 Premium Reveal | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| 15 Product 360 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| 16 Macro Detail | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ⚠️ | ❌ |
| 17 TV Spot (narrative) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 18 Lifestyle Aspiration | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 19 Brand Story | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 20 Pro Virtual Try-On | ⚠️ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 21 Visual Shock / Pattern Interrupt | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| 22 Transformation | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| 23 Wild Card / FOOH | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ⚠️ |

**Auto-rule for the agent:** Mark formats as ✅ → enabled by default · ⚠️ → enabled only if user opts in · ❌ → disabled by default.

**User override:** the user can always promote ⚠️ to ✅ or demote ✅ to ❌ via the AskUserQuestion at Stage 1 confirmation.

---

# Family A — UGC Family (Structure A, 9-layer)

> Use Structure A from `references/structures.md`. All formats here are authentic,
> person-led, smartphone-feel content. Style anchor: `handheld` (default) or
> `documentary`. NEVER use cinematic vocabulary (no "cinematic", "35mm",
> "ARRI ALEXA", "professional color grading"). This breaks the UGC illusion.

## Format 1 — UGC Entertainment

- **Vibe:** challenge / dare / entertainment-first. The product is the punchline, not the subject.
- **Best for:** reach, save-rate, "haha" reaction
- **Style anchor:** handheld
- **Setting cues:** kitchen, living room, street, gym, car, bedroom
- **Persona:** energetic Gen-Z creator (18–25), casual outfit
- **Hook patterns:** "I'll give you $100 if…" · "Will it survive?" · "Caught in 4K" · product-flies-into-frame deadpan reaction · failed dare → recover
- **Audio:** ON, snappy, comedic timing
- **Beat shape:** 3–4 snappy jump cuts with comedic timing
- **Tone words:** playful, mischievous, surprised
- **Concept seeds (vary across the batch):**
  - Blind-try / guess-the-brand challenge
  - "$100 challenge" street dare
  - Will-it-fit / will-it-work absurd test
  - Product flies into frame, deadpan reaction
  - Failed dare → recover → pivot to honest moment
  - Group reaction — line of people trying for first time

## Format 2 — Street Interview

- **Vibe:** sidewalk stranger interviews (Erewhon-style). High-trust, "real people" feel.
- **Best for:** social proof, trust-building, demo in-the-wild
- **Style anchor:** handheld, documentary
- **Setting cues:** outdoor street, park, coffee-shop sidewalk, market, mall, transit hub
- **Persona:** interviewer (off-camera or partial) + stranger reaction. ROTATE stranger demographics aggressively within the batch.
- **Hook patterns:** "What's your favorite [category] right now?" · "Rate this 1–10" · "Trade me your [item] for this"
- **Audio:** ON (ambient street, footsteps, distant traffic)
- **Beat shape:** Interview Q → reaction → closer (3 beats)
- **Tone words:** curious, candid, real
- **Concept seeds:**
  - "What's your favorite [category]?" → reveal
  - "Rate it 1–10" with first-try reaction
  - "Sing for it" — sing a jingle / hum a tune
  - "Trade me your [coffee/snack] for this"
  - Two strangers, blind opinion → reveal the brand
  - "Guess the price" with shocked reaction

## Format 3 — Product Review

- **Vibe:** honest talking-head. Product in hand, ingredients read aloud, side-by-sides, "I tried this for 7 days".
- **Best for:** conversion, trust, considered purchases
- **Style anchor:** handheld
- **Setting cues:** bedroom, bathroom (skincare/grooming), kitchen (food/bev), desk (electronics), couch (apparel)
- **Persona:** authentic mid-20s–30s reviewer matching the product's demographic
- **Hook patterns:** "two-ingredient test" · "I tried this for X days" · "side-by-side with my old favorite" · "honest review" pivot
- **Audio:** ON
- **Beat shape:** hook → demo → verdict (3 beats)
- **Tone words:** honest, considered, decisive
- **Concept seeds:**
  - Read-the-label test — raise eyebrow, try, react
  - "Cold side of the fridge" / "always reach for X" ranking
  - Side-by-side with a competitor (don't name the competitor — show the difference)
  - Diary review — multiple empties on counter, "I tried this for 7 days"
  - Mirror review (Bathroom setting) for skincare/grooming
  - Final ranking — all variants lined up, ranked on camera

## Format 4 — Unboxing

- **Vibe:** premium reveal energy. Hands, packaging, the moment of discovery.
- **Best for:** brand premium-feel, save-driver, "ooh" reaction
- **Style anchor:** handheld (close to locked-off)
- **Setting cues:** clean tabletop, marble counter, soft daylight, neutral background
- **Persona:** hands-only or lifestyle creator (face optional). For high-end products, prefer face-shown.
- **Hook patterns:** slow ribbon-pull, paper-rustle close-up, tag-tug reveal
- **Audio:** ON — often ASMR-leaning (paper, ribbon, tape)
- **Beat shape:** reveal sequence (3–4 beats, slow → fast → slow)
- **Tone words:** anticipatory, premium, satisfied
- **Concept seeds:**
  - Trio / variants reveal nestled in pastel paper
  - Single-product solo drop with slow ribbon-pull
  - Subscription / gift-box drop with handwritten note
  - Hangtag macro series — close-up on tags
  - Crate / wooden-straw "picked today" reveal
  - First-touch energy — sealed → opened in 5 seconds

## Format 5 — ASMR

- **Vibe:** sound-led close-ups. No talking. Audible product handling.
- **Best for:** scroll-stopping, save rate, dwell-time
- **Style anchor:** photorealistic (not cinematic, just precise close-up)
- **Setting cues:** intimate low-noise — kitchen, bathroom, bedroom. NEVER Street / Car / Gym.
- **Persona:** hands-only preferred. If face shown, soft / intimate angle.
- **Hook patterns:** macro cap-unscrew · condensation slide · spoon-clink · bottle-on-marble tap
- **Audio:** ON (THIS IS THE WHOLE POINT — no music, no talking, pure product sound)
- **Beat shape:** 3–4 macro sound moments, no dialogue
- **Tone words:** hushed, intimate, satisfying
- **Concept seeds:**
  - Macro cap / lid / pump-press + pour into a vessel
  - Condensation-bead slide on chilled product, then open
  - Material-on-surface sound (bottle on marble, box on wood, fabric on counter)
  - Ribbon-pull / paper-rustle (crossover with Unboxing)
  - Spoon / ice / metal-on-glass clink
  - Two products clinking gently with no soundtrack

## Format 6 — Tutorial / How-To

- **Vibe:** "Let me show you how to use this." Step-by-step demonstration with voiceover or on-screen tip beats.
- **Best for:** complex products, builds trust through expertise
- **Style anchor:** handheld, documentary
- **Setting cues:** kitchen (recipe), bathroom (skincare routine), desk (tech setup), studio (apparel styling)
- **Persona:** confident demonstrator, mid-20s–30s, expert tone but friendly
- **Hook patterns:** "Here's how to…" · "Step 1:" · "The trick most people miss" · "If you only do one thing…"
- **Audio:** ON, clear voiceover, ambient
- **Beat shape:** intro → step 1 → step 2 → result (4 beats, faster pacing)
- **Tone words:** confident, clear, helpful
- **Concept seeds:**
  - 60-second recipe / routine
  - "3 ways to use this product"
  - "The one mistake everyone makes"
  - Before / during / after of one technique
  - Side-by-side: wrong way vs. right way
  - Speed-run: from sealed product to fully used in 30 seconds

## Format 7 — GRWM (Get Ready With Me)

- **Vibe:** routine while sharing — getting ready, drinking coffee, telling a story. Product is integrated into the routine.
- **Best for:** lifestyle brands, beauty, accessories, female-skewed audience
- **Style anchor:** handheld
- **Setting cues:** bathroom mirror (most common), bedroom, vanity table
- **Persona:** woman 20s–35s, natural look, mid-routine
- **Hook patterns:** "GRWM for a [event]" · "GRWM and I'll tell you about…" · talking + applying
- **Audio:** ON, conversational voiceover
- **Beat shape:** routine flow (4–5 mini-beats integrated)
- **Tone words:** intimate, conversational, multitasking
- **Concept seeds:**
  - GRWM for a date — product as the finishing touch
  - GRWM for work — product fits into morning routine
  - GRWM and I'll tell you a story about how I found this brand
  - GRWM with three product variants — different look each
  - Sunday self-care GRWM
  - Pre-event GRWM with the product as confidence boost

## Format 8 — Day-in-the-Life

- **Vibe:** following the routine from morning → midday → evening, with product appearing in moments throughout.
- **Best for:** showing product in authentic context, multi-touchpoint
- **Style anchor:** handheld, documentary
- **Setting cues:** home → outside → home (full arc)
- **Persona:** real-feeling protagonist, matches product's audience
- **Hook patterns:** "POV: a day with [product]" · "My morning with [product]" · timestamp captions
- **Audio:** ON, ambient + optional voiceover
- **Beat shape:** morning → mid → afternoon → evening (4 timestamps)
- **Tone words:** unhurried, real, lived-in
- **Concept seeds:**
  - Morning to night with [product]
  - "How I survive [activity] thanks to [product]"
  - Pre-shift nurse / chef / athlete with product
  - Travel day — product in airport, hotel, dinner
  - Weekend routine with product as anchor
  - "What I bring to [activity]" — product in pack reveal

## Format 9 — POV First-Person

- **Vibe:** the viewer IS the user. Camera = their eyes. Hands reach out and use the product.
- **Best for:** wearables, apparel, accessories — anything you hold/wear
- **Style anchor:** handheld
- **Setting cues:** depends on product use case
- **Persona:** none visible (or just hands/limbs from below)
- **Hook patterns:** "POV: you just got [product]" · "POV: it's [event]"
- **Audio:** ON, environmental + breath
- **Beat shape:** 3–4 first-person moments, locked perspective
- **Tone words:** immersive, immediate, personal
- **Concept seeds:**
  - POV: putting on the ring/watch/necklace
  - POV: using the product for the first time
  - POV: working out / cooking / typing with the product
  - POV: the moment your friend notices the product
  - POV: comparing two products in your hands
  - POV: unboxing from the customer's hands

## Format 10 — Reaction

- **Vibe:** genuine first-look reaction to the product. Eyes widen, mouth drops, smile spreads.
- **Best for:** new launches, surprise drops, viral content
- **Style anchor:** handheld
- **Setting cues:** close-up of face (medium-close), home / office / public
- **Persona:** authentic reactor matching audience
- **Hook patterns:** seeing product for first time, opening package, trying for first time
- **Audio:** ON, organic reaction sounds (gasp, laugh, "oh my god")
- **Beat shape:** setup → reaction → confirmation (3 beats)
- **Tone words:** surprised, delighted, contagious
- **Concept seeds:**
  - "First time trying [product]" — pure reaction
  - Friend's reaction to your gift
  - Stranger's reaction in a blind test
  - Influencer's reaction to surprise package
  - Side-by-side: bad product vs. your product (reactions)
  - Reaction to brand price (delighted shock at how affordable)

## Format 11 — Storytime

- **Vibe:** narrative testimonial. "Here's a story about how this product changed my…" Builds emotional investment.
- **Best for:** building brand loyalty, conversion through narrative
- **Style anchor:** handheld
- **Setting cues:** intimate setting — couch, car, walking outside (anywhere casual)
- **Persona:** authentic storyteller, mid-20s+, talking to camera
- **Hook patterns:** "Storytime…" · "So this happened…" · "Let me tell you about the time…"
- **Audio:** ON, full voiceover, optional soft music underneath
- **Beat shape:** setup → conflict → resolution + product moment (3–4 beats)
- **Tone words:** confiding, narrative, sincere
- **Concept seeds:**
  - "How [product] saved me from [problem]"
  - "The first time I used [product] I thought…"
  - "I almost didn't buy this and then…"
  - "My boyfriend / mom / friend recommended this and…"
  - "Three weeks in and here's what changed"
  - "I was skeptical until [event]"

## Format 12 — Virtual Try-On (UGC)

- **Vibe:** casual try-on with reaction. Eyewear / apparel / accessories on a real person in their space.
- **Best for:** apparel, eyewear, accessories — anything you wear
- **Style anchor:** handheld
- **Setting cues:** bedroom mirror, dressing room, home with full-length mirror
- **Persona:** matches the brand's customer demographic
- **Hook patterns:** "I'm trying this for the first time" · "Does this look weird?" · mirror selfie reveal
- **Audio:** ON, conversational
- **Beat shape:** put on → check in mirror → final pose (3 beats)
- **Tone words:** curious, vulnerable, satisfied
- **Concept seeds:**
  - Trying 3 sizes/colors of the same product
  - "First time wearing [product]" — full reaction
  - Side-by-side: your old vs. new pair
  - Friend reaction to you wearing it
  - Mirror selfie series at different angles
  - "Will it match my outfit?" multi-outfit try-on

---

# Family B — Hero/Premium (Structure B, Multi-Shot)

> Use Structure B from `references/structures.md`. No person, kinetic product
> hero, polished. Style anchor: `dramatic`, `premium`, `photorealistic`.
> Cinematic vocabulary is OK here ("35mm film grain", "ARRI ALEXA aesthetic",
> "professional color grading") — these formats benefit from it.

## Format 13 — Product Hero / Hyper Motion

- **Vibe:** kinetic product shots — splash, pour, spin, drop. No person. Pure product energy.
- **Best for:** brand hero campaigns, premium-feel video
- **Style anchor:** dramatic, photorealistic
- **Setting cues:** seamless backdrop, neutral surface, dramatic lighting from side
- **Hook patterns:** the pour, droplet impact, cap-pop reveal, levitation
- **Audio:** ON (subtle sound design, no dialogue)
- **Multi-shot count:** 3–4 shots in 15s
- **Concept seeds:**
  - Splash hero — product hits liquid surface
  - Spin reveal — product rotates as label catches light
  - Drop impact — product lands on surface with dust burst
  - Pour pour — liquid pouring from product into glass
  - Cap-pop reveal — slow opening with light streaming through
  - Levitation hero — product hovers with shadow play

## Format 14 — Premium Reveal

- **Vibe:** dark background, dramatic side lighting, product emerges from shadow. Luxury feel.
- **Best for:** luxury launches, premium positioning
- **Style anchor:** dramatic, photorealistic
- **Setting cues:** void stage (black velvet), single-light dramatic setup
- **Hook patterns:** light catches the product first, fabric pulls back, smoke clears
- **Audio:** ON (atmospheric, sparse — chime / hum / soft swell)
- **Multi-shot count:** 3 shots in 12–15s
- **Concept seeds:**
  - Fabric pull-back reveal — silk slides off product
  - Light-from-shadow — product slowly illuminated
  - Smoke clear — mist disperses to reveal product
  - Rotating spotlight — beam circles the product
  - Macro-to-wide — close detail expands to full hero
  - Multiple-variant reveal — products line up in sequence

## Format 15 — Product 360

- **Vibe:** full rotation showing every angle. Clean, polished, e-commerce-ready.
- **Best for:** showcasing design, variants, hero feature
- **Style anchor:** photorealistic, premium
- **Setting cues:** seamless backdrop (white, gradient, or branded color)
- **Hook patterns:** start front-facing, smooth rotation
- **Audio:** ON (subtle drone / brand sting)
- **Multi-shot count:** 1 continuous shot OR 4 angles (front / side / back / top)
- **Concept seeds:**
  - Full 360 rotation on seamless white
  - 4-angle cut sequence (front / 45° / side / back)
  - Macro-to-wide rotation — start tight, pull back during spin
  - Branded-color backdrop rotation
  - Multiple variants rotating in sequence
  - Hand rotates product (only hand visible)

## Format 16 — Macro Detail

- **Vibe:** extreme close-up showing texture, material, craftsmanship. The product as art object.
- **Best for:** premium products with tactile quality
- **Style anchor:** photorealistic, premium
- **Setting cues:** macro lens close-up, soft directional light, shallow depth of field
- **Hook patterns:** rack focus from texture to label, light slide across surface
- **Audio:** ON (subtle texture sounds — fabric rustle, metal hum)
- **Multi-shot count:** 3–4 macro shots in 12s
- **Concept seeds:**
  - Light slides across material texture
  - Rack focus from foreground detail to label
  - Water bead slides off surface
  - Stitching macro on apparel
  - Engraving / etching macro reveal
  - Multi-angle macro tour (4 details in 12s)

---

# Family C — Cinematic (Structure C, TV Spot)

> Use Structure C from `references/structures.md`. Narrative arc, person + story,
> polished commercial feel. Style anchor: `cinematic`, `dramatic`. Full
> cinematic vocabulary encouraged.

## Format 17 — TV Spot (narrative)

- **Vibe:** broadcast-style commercial. Story arc with character, conflict, product moment, resolution. 15-second version of a 60-second TV ad.
- **Best for:** brand campaigns, premium launches, prestige moments
- **Style anchor:** cinematic
- **Setting cues:** real-world locations — kitchen, restaurant, outdoor, gym, office
- **Persona:** authentic character (varies), product user, expressive
- **Hook patterns:** "First-summer-day", "the moment you realize", "before / after life"
- **Audio:** ON (music + ambient + light dialogue, polished)
- **Narrative arc:** setup → tension → product moment → resolution (4 beats)
- **Concept seeds:**
  - Brunch scene — friends + product moment
  - First-summer-day — first sip / first wear / first use
  - Morning ritual — character's day made better
  - "Then this happened" — narrative twist with product as solution
  - Farm-to-table / source-to-product origin story
  - Crowd reaction — character uses product in social scene

## Format 18 — Lifestyle Aspiration

- **Vibe:** beautiful, aspirational moment with product integrated. Less story, more vibe. Pinterest-worthy.
- **Best for:** brand-building, premium positioning, aesthetic-driven brands
- **Style anchor:** cinematic, photorealistic
- **Setting cues:** golden hour, beautiful interior, scenic outdoor
- **Persona:** present but secondary to the aesthetic
- **Hook patterns:** aesthetic moment with product reveal
- **Audio:** ON (atmospheric music, ambient sound)
- **Narrative arc:** atmosphere → product moment → aspiration (3 beats)
- **Concept seeds:**
  - Coffee + product on a sunlit windowsill
  - Beach golden hour — product fits the moment
  - Cozy reading nook — product as accent
  - City balcony at sunset — product in lifestyle
  - Hands at piano / typewriter / desk with product nearby
  - Morning light — slow ritual with product

## Format 19 — Brand Story

- **Vibe:** founder / mission / origin moment. Authentic, emotional, mission-driven.
- **Best for:** building loyalty, telling the "why", one-off campaign anchor
- **Style anchor:** cinematic, documentary
- **Setting cues:** workshop, kitchen, studio, hometown — where it started
- **Persona:** founder or surrogate, speaking sincerely
- **Hook patterns:** "We started this because…" · "12 years ago…" · "The first time…"
- **Audio:** ON (intimate voiceover, soft music)
- **Narrative arc:** origin → mission → product moment (3 beats)
- **Concept seeds:**
  - Founder in workshop telling origin story
  - "Why we make this" — mission moment
  - Heritage / craft story — 3 generations of know-how
  - The team behind the product
  - Source ingredient / material reveal
  - Customer moment — letter / testimonial dramatized

## Format 20 — Pro Virtual Try-On

- **Vibe:** studio-quality try-on. Polished, lit, fashion-editorial. Like a magazine shoot.
- **Best for:** apparel, eyewear, accessories — premium positioning
- **Style anchor:** cinematic, premium
- **Setting cues:** studio with controlled light, polished seamless backdrop, or styled set
- **Persona:** model-quality presenter, styled, posed
- **Hook patterns:** styled walk, mirror reveal, multi-outfit cycle
- **Audio:** ON (atmospheric music, no dialogue)
- **Narrative arc:** entrance → showcase → pose (3 beats)
- **Concept seeds:**
  - Styled walk in studio
  - Multi-look cycle — 3 outfits in 15s
  - Mirror reveal — model approaches mirror, turns to camera
  - Posed shoot — magazine-cover quality
  - Color variant cycle on same model
  - Detail-to-full sequence — macro of fabric → full look

---

# Family D — Pattern Interrupt / Viral (Structure D, 2-Second Hook)

> Use Structure D from `references/structures.md`. Scroll-stopping, surreal,
> pattern-breaking. The first 2 seconds carry the whole video. Style anchor
> varies — can be photorealistic, cinematic, or stylized.

## Format 21 — Visual Shock / Pattern Interrupt

- **Vibe:** something impossible or unexpected in the first frame. Brain says "wait, what?"
- **Best for:** scroll-stopping, viral reach, awareness
- **Style anchor:** photorealistic (impossible thing rendered realistically) OR cinematic
- **Setting cues:** wherever the impossibility lands
- **Hook patterns:** impossible scale, impossible physics, color explosion, glitch effect, freeze-and-snap
- **Audio:** ON (sound design CRITICAL — drop, whoosh, glitch, sting)
- **2-second hook breakdown:** [0.0-0.3s] grab → [0.3-0.8s] build → [0.8-1.5s] momentum → [1.5-2.0s] commit
- **Concept seeds:**
  - Impossible scale — product 50x normal size
  - Reverse motion — product un-spilling itself
  - Color explosion — gray world floods with brand color
  - Glitch reveal — reality "buffers" then product appears
  - Freeze-and-snap — frozen moment then explosion into speed
  - Misdirection — setup expects A, delivers B

## Format 22 — Transformation (Before/After)

- **Vibe:** dramatic change visible in real time. The product causes the transformation.
- **Best for:** results-driven products (skincare, cleaning, fitness, beauty)
- **Style anchor:** photorealistic or cinematic
- **Setting cues:** the space being transformed
- **Hook patterns:** before state → product application → after reveal
- **Audio:** ON (build → satisfying click → release)
- **Narrative arc:** before (0-3s) → product (3-9s) → after (9-15s)
- **Concept seeds:**
  - Skin transformation — Day 1 vs Day 30
  - Space transformation — messy → organized
  - Body transformation — pre / post fitness
  - Product use transformation — broken → fixed / dirty → clean
  - Style transformation — outfit before / outfit after
  - Mood transformation — tired character → energized

## Format 23 — Wild Card / FOOH

- **Vibe:** surreal, impossible-scale, dreamlike. Often Fake-Out-Of-Home (FOOH) — giant product in real city.
- **Best for:** viral moments, brand awareness, attention bombs
- **Style anchor:** cinematic, hyper-realistic
- **Setting cues:** real-world public space (street, square, ocean, sky)
- **Hook patterns:** impossible scale in real environment, surreal physics
- **Audio:** ON (cinematic sound design)
- **Multi-shot count:** 2–3 shots in 15s
- **Concept seeds:**
  - Giant product in Times Square (FOOH classic)
  - Product floats over ocean / city
  - Building-sized product reveal
  - Product transforms landscape
  - Surreal product use (someone drinks from a building-sized bottle)
  - Dreamlike composition — product in impossible space
