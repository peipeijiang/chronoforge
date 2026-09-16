# ChronoForge · v3

[中文](README.md) · [Skill instructions](SKILL.md)

Create multi-clip films through three input routes: uploaded video recreation, original product ads from product URLs, and product-constrained adaptation using both inputs.

The shared runtime preserves full evidence, versioned whole-film stories, editorial/provider separation, ordered references, L1 and human lock, serial paid creates with ambiguity-safe recovery, L2 container review, deterministic FFmpeg assembly and L3 final-master review.

## Routes and defaults

- Uploaded/local video: watch full-source evidence, measured timecodes, visual/audio findings and causal story.
- Product URL: product-ugc-pipeline acquisition/cognition, complete per-image vision, claim ledger and an original whole-film story. No watch. Do not modify the external product skill.
- Both: both evidence streams, explicit source-to-product adaptation; product truth determines legitimate structure/functions.
- Unclear input: inspect the page type or ask for the missing input. Competitor/review research is optional and hypotheses are labelled.

Images default to LK888/upDrama tt-image-2.5; tt-image-2 is a scoped known-failure alternative. Independent video scenes use omni_flash-10s; actual continuations use omni_flash-10s-fl with the accepted preceding true last frame and target endpoint. Deliberately shorter jobs may use omni-flash. New v3 jobs do not use LaoZhang images or VEO. Preserve legacy assets.

## Start

Requires Python 3.10+, FFmpeg/ffprobe and the relevant external acquisition skill. Paid runtime uses POSIX locks (macOS/Linux).

```bash
git clone --branch v2 https://github.com/peipeijiang/chronoforge.git
cd chronoforge
python3 scripts/init_run.py /path/source.mp4 --out /path/remake
python3 scripts/init_run.py --product-url 'https://shop.example/product' --duration 30 --out /path/product-run
python3 scripts/init_run.py /path/source.mp4 --product-url 'https://shop.example/product' --duration 30 --out /path/hybrid-run
python3 -m unittest discover -s tests -v
```

The publishing branch remains v2; newly initialized runs use the v3 schema. Existing v2 runs/examples remain compatible. Preserve local changes when updating an installed skill.

Author the entire film first, then compile container requests. Three ad variants are not three sequential chapters. V3 editorial_range records chosen edit timing; source_range only records actual source evidence. Supporting detail/montage shots declare purpose instead of fabricated causality.

Read [route workflows](references/route-workflows.md), [prompt/reference contracts](references/prompt-and-reference-contract.md), [provider runtime](references/provider-runtime.md), [model contracts](references/updrama-contract.md), [QA](references/qa-contract.md) and [delivery](references/delivery-and-canary.md).

All generated imagery is text-free. White text and custom voice/music mixing are local postproduction work followed by a fresh L3 review. Bundled assembly supports generated or silent audio. Tests use synthetic media/mocked services; they do not certify live model availability or generated semantic quality. Never publish private source/account data, credentials or task/result URLs.
