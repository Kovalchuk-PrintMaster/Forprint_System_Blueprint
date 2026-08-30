# 02. Customer Identity, Manual Intake & Semantic Retrieval v1.0

## 1. CRM Customer Identity Resolution

Primary owner: `forprint_crm`.

Телефон лишається сильним практичним lookup key, але не canonical primary key.

Canonical entities:

### Person
```yaml
person_id: immutable
display_name: ...
phones: []
emails: []
telegram_user_ids: []
telegram_usernames: []
viber_ids: []
aliases: []
```

### Organization
```yaml
organization_id: immutable
canonical_name: ...
edrpou: null
aliases: []
```

### Representation
```yaml
representation_id: immutable
person_id: ...
organization_id: ...
role: ...
valid_from: ...
valid_to: null
status: active|inactive|unverified
source: ...
confidence: ...
```

При переході людини в іншу компанію historical representation не видаляється:
закривається `valid_to`.

Order зберігає snapshot:
```yaml
person_id: ...
organization_id: ...
representation_id: ...
confirmed_at: ...
confirmation_source: ...
```

Пошук за останніми 4 цифрами телефону — candidate lookup, не proof of identity.

Anonymous/one-off order може бути прив'язаний до generic customer context без
створення fake verified person.

При contact через email/Telegram/Viber/office/phone новий channel identity спочатку
проходить candidate matching/clarification, а не автоматично створює duplicate customer.

Telegram once-per-order friendly confirmation:
«Це замовлення оформлюємо на <organization>».
Якщо representative більше не працює там — relationship закривається, new order
context формується заново.

## 2. Calculator Manual / Alternative Intake

Primary owner: `calculator_engine`.

Ручний filename/hot-folder/CSV/operator input — не окремий бізнес-процес.
Це adapter до одного `CanonicalCalculationRequest`.

```text
Calculator UI/API ─┐
Filename/Hotfolder ├─> CanonicalCalculationRequest -> validation/calculation
CSV/Legacy import ─┘
```

Рекомендована послідовність:
1. canonical product/job specification;
2. validation rules;
3. material/waste model;
4. canonical calculation result;
5. manual intake adapter;
6. versioned filename grammar;
7. parser;
8. ambiguity detection;
9. clarification;
10. hot-folder watcher;
11. parity tests.

Parser outcomes:
- VALID
- MISSING_FIELD
- AMBIGUOUS
- INVALID
- NEEDS_CLARIFICATION

Важливі поля не вгадуються мовчки.

Filename contract versioned:
```yaml
contract_id: manual_filename_contract
revision: 1
status: ACTIVE
```

## 3. ForPrint Semantic Retrieval Service — new module candidate

Рекомендований candidate ID:
`forprint_semantic_retrieval_service`

Це cross-cutting retrieval service, а не «vector search» як вузька технологія.

Principle:
**Search finds candidates. Domain owner decides truth.**

Searchable entities:
- products/materials;
- people/organizations;
- orders/jobs;
- documents;
- photos/media;
- incidents;
- production knowledge/history.

Hybrid retrieval:
1. ACL filter;
2. exact IDs;
3. structured filters;
4. lexical/full-text;
5. vector text embeddings;
6. image embeddings;
7. hybrid rank;
8. rerank;
9. confidence;
10. explanation.

Projection:
```yaml
entity_id: ...
entity_type: ...
source_module: ...
source_revision: ...
searchable_text: ...
structured_attributes: {}
embedding_ref: ...
image_embedding_refs: []
visibility_scope: ...
indexed_at: ...
```

Result:
```yaml
status: MATCHES|UNCERTAIN|NO_MATCH|POSSIBLE_NEW_ENTITY
candidates:
  - entity_id: ...
    score: ...
    match_reasons: []
    media_refs: []
```

### Reference scenario A — damaged QR during inventory

Operations Assistant receives:
«біла футболка, короткий рукав, можливо бавовна».

Semantic Retrieval → candidates + photos.

Employee confirms / marks uncertain / escalates / marks possible new entity.

Warehouse changes only after domain confirmation.

### Reference scenario B — fuzzy client search

«Ірина, минулого місяця замовляла флаєри».

Semantic Retrieval returns person/order candidates. CRM remains owner `person_id`.

### Reference scenario C — Telegram photo

Client sends photo + «мені треба така штука».

Telegram → Semantic Retrieval → 3–5 candidate products/technologies → Telegram
clarification → Calculator/order flow.

### Product/reference photos

Product/material card should have media metadata.
If incoming product lacks sufficient reference media, Operations Assistant can
prompt employee to capture:
- front;
- back;
- label;
- packaging;
- distinctive detail.

### Evaluation

Stable test corpus + metrics:
- recall@k;
- precision;
- MRR;
- no-match accuracy;
- false confident match rate.

False confident match is a critical metric.

### ACL

Retrieval must enforce access restrictions before returning results.
Search index cannot become a side-channel around domain permissions.
