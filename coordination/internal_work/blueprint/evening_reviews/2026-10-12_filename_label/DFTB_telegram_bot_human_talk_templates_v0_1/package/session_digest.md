# Session Digest — Telegram human-talk template dataset

## Duplicate result

Unique source. No source-hash, message-ID or exact substantive-text duplicate was found against clean master v2.9.

## Chronology warning

The filename says `12.10.26`, but the MHTML was saved on **15.09.2026**.

Therefore `12.10.26` is only a filename label. The exact historical project date is unknown.

## Historical purpose

The owner wants a Telegram response layer that produces short, warm/human responses from classification dimensions:

- intent;
- style;
- sentiment.

The same synthetic data was intended for:
- `forprint_human_talk_templates`;
- possible Mistral-7B-Instruct fine-tuning.

Current model choice is not inferred.

## Schema evolution inside the source

Turn 1 has an early table shape with:
- `intent_id`;
- textual `style`;
- textual `sentiment`;
- `template_text`;
- `priority`;
- `language`.

Turn 3 explicitly normalizes the model to:
- `intent_id`;
- `style_id`;
- `sentiment_id`;
- `template_text`;
- `priority`;
- `language`;

with foreign keys to:
- `forprint_intents`;
- `forprint_styles`;
- `forprint_sentiments`.

The normalized form is the later historical requirement.

## Owner-supplied taxonomies

### Intents
Ten IDs:
greeting, thanks, payment, delivery, support, information, return, complaint, product query, closing.

### Styles
Exactly four:
- warm;
- formal;
- casual;
- neutral.

### Sentiments
Exactly three:
- positive;
- neutral;
- negative.

### Languages
- uk;
- ru;
- en.

### Priority
0–10.

## Template quality rules

Owner requires:
- 1–2 sentences;
- natural/human phrasing;
- style/sentiment consistency;
- emoji only where suitable;
- no verbatim repetition;
- ready for Telegram use.

## Initial dataset claim

Assistant claims:
10 intents × 4 styles × 3 sentiments = 120 rows per language.

Across 3 languages:
**360 rows**.

Referenced files include taxonomy CSVs, template CSV and distribution summary.

The actual CSV bodies are not preserved in MHTML, so these claims are historical reports, not verified dataset evidence.

## Additional 500-row claim exposes contract drift

Assistant later claims another 500 unique rows.

But its own description mentions:
- styles `friendly`, `playful`;
- states/sentiments `aggressive`, `urgent`.

Those values do **not** exist in the owner-supplied lookup tables.

This is a significant historical data-contract defect candidate.

It must not be interpreted as an authorized taxonomy expansion.

## Additional 1000-row claim

Owner asks for 1000 more rows.

Assistant claims:
- 1000 unique rows;
- uk=334;
- ru=333;
- en=333.

Again the CSV body is unavailable.

## Count inconsistency

Assistant later offers to merge everything into a master of **1800 records**.

But its preceding claims are:

360 + 500 + 1000 = **1860**.

This inconsistency is preserved explicitly.

## Historical CSV import failure

Owner reports that one generated file cannot be imported:

the import UI says columns such as:
`intent_id`, `style_id`, `sentiment_id`, `template_text`, `priority`
are not present in the selected table.

Owner also reports that an earlier:
`forprint_human_talk_templates (1).csv`
imported successfully.

The failing CSV and selected target table are not embedded.

Therefore the exact root cause is unresolved.

Assistant suggests possible causes:
- wrong target table;
- stale/different schema;
- exact-header/BOM problems;
- extra columns;
- malformed CSV rows.

These remain hypotheses, not proven diagnosis.

## Clean-file workaround

Assistant references:
`forprint_human_talk_templates_CLEAN.csv`

with only:
- intent_id;
- style_id;
- sentiment_id;
- template_text;
- priority;
- language.

`created_at` and `updated_at` are omitted so database defaults can populate them.

This is a reasonable historical import strategy, but the file itself is unavailable.

## Safer import pattern

Historical recommendations worth preserving:

1. resolve the exact current table/schema;
2. export/compare a known-good header;
3. validate CSV encoding/delimiter/header/quotes;
4. test ~10 rows first;
5. only then bulk-import;
6. reject taxonomy IDs/labels outside the canonical lookup tables.

## Architecture boundary

This source is about **conversation/presentation data**.

It does not make Telegram the canonical owner of:
- clients;
- orders;
- payments;
- logistics;
- calculation truth.

Later Blueprint explicitly treats Telegram as an operational interface, not canonical truth authority.

## Current audit needed

The main current questions are:
- what is the live Telegram schema?
- who owns intent/style/sentiment/template taxonomies?
- are current datasets valid and deduplicated?
- what AI/model/template-selection runtime is active?
- does current routing respect Gateway/CRM/Blueprint boundaries?
