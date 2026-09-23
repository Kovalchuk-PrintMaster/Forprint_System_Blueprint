# Session Digest — Telegram data ingest and early 1C integration

This unique sparse source captures an early data-oriented Telegram phase.

## Dialogue ingestion

Owner defines HTML→CSV extraction for customer chats, including client mapping, message pairing, intent/style/sentiment tagging and Supabase import.

The workflow later shifts to a safer compatibility-first rule: use known-good CSV examples that already import successfully, then generate synthetic examples in the same shape.

## Important historical schema drift

This early source allows styles:
formal, casual, friendly, professional, urgent.

Later Telegram history normalizes styles to:
warm, formal, casual, neutral.

Likewise this source uses sentiments beyond positive/neutral/negative, including urgent/curious/confused. Later owner-defined sentiment lookup narrows to positive/neutral/negative.

Therefore early labels are pre-normalization history, not current taxonomy.

## Synthetic metadata caveat

Several fields are filled by convention:
response_time=1.5, feedback=0, fixed confidence values.

These are synthetic annotations, not observed production facts.

## Privacy caveat

The historical import shape contains names, phone numbers and real conversation text. Current privacy/retention/sanitization policy must govern any reuse for model training or fixtures.

## Database normalization question

Owner rejects one enormous sparse table for suppliers/contractors/products/services. Assistant recommends normalized tables connected by IDs.

The general relational principle is useful, but Telegram is not thereby the current owner of those canonical entities.

## Early 1C integration idea

Owner asks whether Telegram should have fresh copies/access to 1C nomenclature, stock, orders, payments and client-related data.

Assistant proposes periodic/event synchronization through:
1C export → JSON/CSV → Python connector → Supabase/API → scheduled/event refresh.

This is discussion-level history only.

Later project architecture is stronger:
- Accounting Registry owns accounting/1C boundary;
- Operational Registry owns operational truth;
- Library owns canonical definitions;
- Gateway owns runtime transport/validation/routing;
- Telegram is an operational interface.

Thus current Telegram should consume approved projections/contracts, not maintain a competing canonical 1C/client/product mirror.

## Chronology

Filename `07.10.26` is impossible relative to the 15.09.2026 export and there is no reliable internal timestamp. Exact date remains unknown.
