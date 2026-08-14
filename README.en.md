<div align="center">

[简体中文](README.md) · **English**

# ChronoForge

**A causality-first agent skill for recreating videos longer than a generation model's clip limit.**

[![Validate](https://img.shields.io/github/actions/workflow/status/peipeijiang/chronoforge/validate.yml?branch=main&style=for-the-badge&label=Validate)](https://github.com/peipeijiang/chronoforge/actions/workflows/validate.yml)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-ChronoForge-6D5AE6?style=for-the-badge)](SKILL.md)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![Languages](https://img.shields.io/badge/Docs-中文%20%7C%20English-1F6FEB?style=for-the-badge)](README.md)

</div>

Short-video models generate clips; stories run longer. ChronoForge turns a source video into evidence, immutable story truth, locked references, fixed-duration generation containers, deterministic assembly, and layered QA. Its central rule is simple: **story truth is immutable; provider clips are packaging**.

ChronoForge targets reference-locked structural and semantic reenactment. It does not promise pixel-perfect cloning, motion identity, or exact likeness, and it requires appropriate rights to the source and reference material.

## Core capabilities

ChronoForge turns long-video recreation into four verifiable data layers: source evidence, editorial truth, provider execution requests, and rendered-media acceptance records. It analyzes the complete source first, then compiles shot boundaries, action order, character states, prop changes, and audio intent into an editorial timeline that is independent of any model's clip limit. Reference images and fixed-duration video jobs are generated only after that truth is frozen.

- **Complete source evidence:** records media metadata, timestamps, visual observations, transcripts, audio cues, and unresolved uncertainty instead of prompting from a few isolated frames.
- **Story and continuity contracts:** stores each shot's cause, action, reaction, result, character state, prop state, and explicit must-preserve/may-drift fields.
- **Editorial shots separated from provider jobs:** original shot boundaries stay authoritative; containers only package adjacent shots into durations accepted by the provider.
- **Compiled and human-locked references:** assigns characters, locations, props, and key states to ordered reference roles; paid video generation waits for L1 QA and human approval.
- **Safe paid execution:** refreshes the provider contract before each batch, writes intent before POST, serializes creates, and prevents blind retries after ambiguous submissions.
- **Layered QA and deterministic assembly:** validates references at L1, raw containers at L2, and the final master at L3; only accepted slices reach deterministic FFmpeg trim, normalization, and concatenation.

## How it works

```mermaid
flowchart TD
  subgraph A["A · Source evidence"]
    SRC["① Source video<br/>local file · rights confirmation"]
    INIT["② ChronoForge / init_run.py<br/>ffprobe · hash · delivery contract"]
    WATCH["③ $watch / claude-video Skill<br/>full pass · dense windows · transcript"]
    EVID["Evidence bundle<br/>source-evidence.json<br/>visible fact · editorial inference · unknown"]
    SRC --> INIT --> WATCH --> EVID
  end

  subgraph B["B · Creative truth and references"]
    STORY["④ ChronoForge story compiler<br/>hook · cause→action→reaction→payoff<br/>character states · prop lifecycles"]
    SHOTS["⑤ Editorial shot truth<br/>exact bounds · action order · audio intent"]
    TOPO["⑥ Semantic container topology<br/>shots stay immutable · 10s jobs are packaging"]
    REFS["⑦ Reference plan<br/>characters · location · props · causal states"]
    PREFLIGHT["⑧ UpDrama runtime preflight<br/>absorbs SKILL (1).md<br/>guide · model detail · request schema"]
    IMG2["⑨ Paid model: gpt-image-2<br/>generate/clean reference assets"]
    L1{"⑩ L1 reference QA<br/>identity · state · contamination · anatomy"}
    LOCK{"One routine human gate<br/>lock reference pack and hashes"}

    EVID --> STORY
    STORY --> SHOTS --> TOPO
    STORY --> REFS --> PREFLIGHT --> IMG2 --> L1
    L1 -->|fail: rebuild only the bad asset| REFS
    L1 -->|pass| LOCK
  end

  subgraph C["C · Multi-container video generation"]
    VPROMPT["⑪ ChronoForge video prompt compiler<br/>reference roles · timed actions · hard cuts<br/>trim deadline · audio · exclusions"]
    OMNI["⑫ Paid model: omni_flash-10s × N<br/>fixed 10s jobs · up to 7 references"]
    LEDGER["Append-only paid-job ledger<br/>submit intent · task ID · result hash<br/>never blind-retry an unknown submission"]
    L2{"⑬ L2 container QA<br/>ffprobe/FFmpeg + Watch<br/>optional vision-tools"}

    TOPO --> VPROMPT
    LOCK --> VPROMPT
    PREFLIGHT --> VPROMPT
    VPROMPT --> LEDGER --> OMNI --> L2
    L2 -->|reference failure| REFS
    L2 -->|motion/cut failure<br/>change one variable| VPROMPT
  end

  subgraph D["D · Deterministic assembly and delivery"]
    ASSEMBLE["⑭ FFmpeg / assemble.py<br/>normalize · trim/atrim · PTS reset · concat"]
    L3{"⑮ L3 master QA<br/>full decode · exact duration · seven edits<br/>A/V seams at 10/17/27s · story payoff"}
    MASTER["Final master<br/>video + prompts + reference manifest<br/>job ledger + L1/L2/L3 QA"]

    L2 -->|pass| ASSEMBLE --> L3
    L3 -->|assembly-only failure: no paid retake| ASSEMBLE
    L3 -->|pass| MASTER
  end

  CREATIVE["Design references (not runtime dependencies)<br/>drama-skills: short-drama-assets / image-prompts<br/>storyboard / video-prompts / review<br/>LuxReal: conditional action and reaction craft"]
  DONORS["Narrow code donors (never invoked unchanged)<br/>product-ugc-pipeline · viral-storyboard-omni<br/>viral-replica-pipeline · Agent Company"]
  CREATIVE -.-> STORY
  CREATIVE -.-> REFS
  CREATIVE -.-> VPROMPT
  DONORS -.-> PREFLIGHT
  DONORS -.-> LEDGER
  DONORS -.-> ASSEMBLE

  classDef evidence fill:#E8F1FF,stroke:#2F6FEB,color:#102A56;
  classDef truth fill:#FFF4CC,stroke:#B58105,color:#513B00;
  classDef model fill:#FFE5E5,stroke:#C93C3C,color:#5C1616;
  classDef gate fill:#F3E8FF,stroke:#7C3AED,color:#3B1764;
  classDef tool fill:#E6F6EA,stroke:#27864A,color:#123F24;
  classDef output fill:#DFF7F4,stroke:#0F766E,color:#134E4A;
  classDef reference fill:#F5F5F5,stroke:#737373,color:#333,stroke-dasharray:5 5;
  class SRC,INIT,WATCH,EVID evidence;
  class STORY,SHOTS,TOPO,REFS,VPROMPT truth;
  class IMG2,OMNI model;
  class L1,LOCK,L2,L3 gate;
  class PREFLIGHT,LEDGER,ASSEMBLE tool;
  class MASTER output;
  class CREATIVE,DONORS reference;
```

Solid colored nodes belong to the ChronoForge runtime. Gray dashed nodes show design or code provenance only; they never become a second orchestrator. Red nodes incur model charges, and purple diamonds are acceptance and retry gates.

The editorial timeline remains the source of truth even when a provider only outputs fixed 10-second clips. A 33.1-second source may become four 10-second jobs, retain `10 + 7 + 10 + 6.1` seconds, and then be assembled back to the editorial duration.

## Quick start

### 1. Install the skill

Requirements: a `SKILL.md`-compatible agent host such as Codex, Python 3.10+, `ffmpeg`, and `ffprobe`.

```bash
git clone https://github.com/peipeijiang/chronoforge.git \
  ~/.agents/skills/chronoforge
```

Start from your agent with a source video:

```text
$chronoforge analyze and recreate /path/to/source.mp4 using 10-second provider clips
```

### 2. Initialize a non-paid run

From the skill directory:

```bash
python3 scripts/init_run.py /path/to/source.mp4 \
  --out /path/to/run \
  --provider-clip-seconds 10 \
  --aspect-ratio 9:16
```

This probes and hashes the source, creates the run structure, and initializes the append-only ledger. It does not call a provider.

### 3. Compile and validate story truth

Use [`assets/story-truth.example.json`](assets/story-truth.example.json) and [`assets/timeline.example.json`](assets/timeline.example.json) as schema examples, then validate your populated manifests:

```bash
python3 scripts/validate_story.py /path/to/run/analysis/story-truth.json
python3 scripts/validate_timeline.py /path/to/run/manifests/timeline.json
```

Stop for human approval after reference assets pass L1 QA. Paid video submission must not begin before that reference pack is locked.

### 4. Validate and submit provider jobs

The bundled adapter currently allow-lists UpDrama `gpt-image-2` and `omni_flash-10s`. Export the key only in your shell—never place it in a request or manifest.

```bash
export UPDRAMA_API_KEY="<your-key>"

python3 scripts/updrama_runtime.py preflight
python3 scripts/updrama_runtime.py validate assets/omni-request.example.json
```

Submitting is paid and requires an explicit confirmation phrase:

```bash
python3 scripts/updrama_runtime.py submit /path/to/run/requests/video/C01.json \
  --run-dir /path/to/run \
  --job-id C01-v1 \
  --confirm-paid I_UNDERSTAND_THIS_IS_PAID

python3 scripts/updrama_runtime.py status <task-id> \
  --run-dir /path/to/run
```

The adapter writes a submit intent before the POST, serializes creates on Unix-like systems, and records ambiguous submissions without retrying them in the same invocation. It is not a provider-level idempotency guarantee: resolve any `unknown_submission` before manually submitting again.

### 5. Assemble the accepted containers

Place the assembly manifest at the run root if it uses paths such as `media/containers/...`, because paths resolve relative to the manifest.

```bash
cp assets/assembly.example.json /path/to/run/assembly.json
# Adapt the container list and retained durations first.
python3 scripts/assemble.py /path/to/run/assembly.json
```

The assembler normalizes geometry, frame rate, pixel format, and audio before trimming and concatenation. It prints the encoded probe data so the final duration and streams can be checked.

## The fidelity contract

| Layer | Accepts | Rejects or retakes |
|---|---|---|
| L1 · References | identity, environment, prop state, role isolation | wrong state, reference contamination, missing story-bearing object |
| L2 · Raw containers | required beats in order, action completion before trim, continuity | technically valid clip with reversed or missing causality |
| L3 · Master | exact editorial order, seams, A/V continuity, setup/payoff | assembly defects; these never trigger a paid generation retake |

Retake the earliest responsible layer and change one variable per controlled retry. A technical pass is not a story pass.

## Long-video topology with a fixed-duration model

Assume a 33.111723-second source has eight continuous editorial shots while the video model always returns 10 seconds. ChronoForge keeps the eight original shot ranges unchanged and compiles semantically adjacent shots into four execution containers:

| Container | Editorial shots | Source range | Generated | Retained | Extra tail |
|---|---|---:|---:|---:|---|
| C01 | S01–S02 | 0–10 s | 10 s | 10 s | None |
| C02 | S03–S04 | 10–17 s | 10 s | 7 s | Stable hold from 7–10 s, then trimmed |
| C03 | S05–S06 | 17–27 s | 10 s | 10 s | None |
| C04 | S07–S08 | 27–33.111723 s | 10 s | 6.111723 s | Stable hold from 6.111723–10 s, then trimmed |

The final duration is `10 + 7 + 10 + 6.111723 = 33.111723` seconds. Containers change execution topology, never editorial truth. A failed container retakes only that job; a trim or concatenation defect returns only to FFmpeg and never triggers paid regeneration.

## Included tools

| Script | Purpose | Paid |
|---|---|---:|
| `init_run.py` | probe/hash the source and initialize a run | No |
| `validate_story.py` | reject missing causal and payoff links | No |
| `validate_timeline.py` | verify editorial and container coverage | No |
| `updrama_runtime.py` | preflight, validate, submit, and inspect jobs | Submit only |
| `assemble.py` | normalize, trim, concatenate, and probe the master | No |

The deeper contracts live in [`references/story-compiler.md`](references/story-compiler.md), [`references/provider-runtime.md`](references/provider-runtime.md), and [`references/qa-contract.md`](references/qa-contract.md).

## Known limits

- ChronoForge is an agent-guided production protocol, not a one-command automatic video cloner.
- Source-video semantic analysis is routed to an installed analysis skill such as `watch`; it is not bundled here.
- The current provider adapter is UpDrama-specific and its runtime contract can drift. Always run `preflight` before paid work.
- `status` records result URLs but does not download or hash media automatically.
- The assembler expects video and audio in every input, uses centered scale-and-crop, and outputs H.264/AAC.
- Paid-create file locking uses `fcntl`, so the current adapter targets macOS and Linux.
- Initialization currently supports `9:16` and `16:9`.

## License

No license has been selected yet. The source is publicly viewable, but reuse requires the owner's permission until a license is added.
