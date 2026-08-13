# Story compiler reference

## Contents

1. Evidence schema
2. Story truth schema
3. Attraction analysis
4. Prop and state tracing
5. Container design
6. Common failures

## Evidence schema

Represent each observation as:

```json
{
  "start": 0.0,
  "end": 2.4,
  "visible_fact": ["character A cleans", "character B squats in a litter box"],
  "editorial_inference": ["the second action creates the later odor"],
  "unknown": [],
  "audio": {"dialogue": null, "effects": ["cloth wipe"], "music": null},
  "source_frames": ["frame-id"]
}
```

Never put inference in `visible_fact`. An edit can imply a relationship without literally showing it.

## Story truth schema

```json
{
  "hook": {"beat_ids": ["B01"], "mechanism": "incongruity"},
  "characters": [{"id":"A","role":"order","state_track":[]}],
  "beats": [{
    "id":"B01",
    "source_range":[0.0,2.4],
    "cause":null,
    "visible_action":"...",
    "reaction":null,
    "consequence":"B02",
    "payoff":"B09",
    "must_preserve":["..."],
    "may_drift":["background pedestrian count"]
  }],
  "prop_tracks": [{"prop":"mask","states":[]}],
  "fidelity_boundary":"structural and semantic reenactment"
}
```

Permit null only for a true initial condition or terminal beat. Otherwise require causal links.

## Attraction analysis

Classify why the source retains attention. Common mechanisms:

- immediate incongruity or taboo conflict;
- withheld information and later reveal;
- reaction shot that explains an unseen cause;
- reversal, wordplay, or editorial insinuation;
- alternating tension/comedy with satisfying craft or process;
- escalating scale, stakes, or visual novelty;
- relationship conflict and reconciliation;
- sensory payoff: extraction, cutting, pouring, transformation, texture, sound;
- loop closure or callback.

Do not reduce attraction to “cute,” “cinematic,” or “fast-paced.” Point to exact beats and explain the mechanism.

## Prop and state tracing

Trace story-bearing state as a finite sequence:

```text
mask: absent → odor reaction → worn → removed after hygiene restored
waste: caused → contained → carried → disposed
drink: beans → grounds → extraction → milk → garnish → served
```

For each transition record:

- initiating beat;
- visible evidence;
- responsible character;
- location;
- next required appearance;
- forbidden discontinuities.

If a prop appears without its earlier cause, the replica has a continuity error even when the prop looks correct.

## Container design

Each container manifest must include:

```json
{
  "id":"C01",
  "source_range":[0.0,10.0],
  "provider_duration":10.0,
  "retain_duration":10.0,
  "beat_ids":["B01","B02"],
  "completion_deadline":10.0,
  "start_state":{},
  "end_state":{},
  "reference_roles":[],
  "shot_segments":[{"shot_id":"S01","source_range":[0.0,10.0]}]
}
```

Provider boundaries are not necessarily source shot boundaries. Preserve all internal source cuts in the prompt and QA manifest.
When a continuous source shot exceeds the provider limit, divide only its container ownership into contiguous `shot_segments`; do not invent an editorial cut in the immutable shot list.

## Common failures

- Object recognition without function: calling a litter scoop a tray.
- Reaction without cause: a mask appears because a prompt requests one.
- Wrong source attribution: odor becomes machine smoke.
- Surface-action replication: coffee actions survive but the joke disappears.
- Literalizing an implication: editorial wordplay becomes unsafe or false physical continuity.
- Equal-duration bins that split an action or separate its reaction.
- Reference dilution: too many generic images weaken the key causal reference.
- Technical-pass inflation: valid codecs are mistaken for story fidelity.
