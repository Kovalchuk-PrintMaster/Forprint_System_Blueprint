# Historical Customer Asset Indexing and Retrieval

## Problem

ForPrint already has historical customer files.

They should not be searched live by Telegram Bot.

## Target architecture

```text
Physical archive
    ↓
Prepress / Asset Indexing Worker
    ↓
Machine-readable asset index
    ↓
Fast candidate search
    ↓
Deep comparison of a small candidate set
    ↓
Customer confirmation when ambiguity remains
```

## Indexing worker responsibilities

Potential metadata per asset/document:
- stable asset id;
- customer id;
- order id;
- archive reference/path;
- original filename;
- received/created date;
- file type;
- size;
- page count;
- dimensions;
- color/resolution;
- exact binary hash;
- visual/perceptual fingerprints;
- OCR/text signature;
- semantic descriptors;
- representative page fingerprints;
- revision-family relationship;
- actual production links;
- printed/approved/rejected/superseded status.

## Retrieval layers

### Exact identity
Same physical/binary file.

### Visual similarity
Same or nearly same design after export/compression/minor edits.

### Semantic/order similarity
Same product/order pattern despite different content.

## Multi-page documents

Use progressive enrichment:
1. document-level metadata;
2. representative pages;
3. deeper page-by-page comparison only after candidate narrowing.

## Screenshot scenario

Customer says:
> “I printed this book before”

and sends a screenshot.

Target flow:
1. query only this customer’s index;
2. retrieve likely documents;
3. deep-compare a small candidate set;
4. if two revisions remain very close, present both;
5. customer selects the exact historical version.

The machine’s job is to remove nearly all irrelevant candidates, not invent certainty between two almost-identical legitimate revisions.

## Revision families

Support relationships such as:

```text
BOOK-041
├── R01
├── R02
└── R03
```

Actually produced/approved revisions should generally rank above files that merely appeared in communication.
