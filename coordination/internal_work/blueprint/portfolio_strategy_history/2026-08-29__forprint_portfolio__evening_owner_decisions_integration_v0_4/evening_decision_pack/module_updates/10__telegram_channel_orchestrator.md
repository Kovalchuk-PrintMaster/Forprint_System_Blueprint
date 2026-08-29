# Telegram Bot / Channel Orchestrator — evening delta

Channel + conversation orchestrator, not owner of accounting/logistics/business truth.

Scenario classification:
new/existing customer, new/repeat request, pricing, delivery problem, reconciliation question, etc.

Define explicit customer-confirmation rules for paid/manual prepress, automatic file correction, delivery changes and order confirmation.

Every inbound/outbound business message should be persisted in central data.

Large files are routed to managed temporary storage/Prepress rather than processed locally.

Plan Ukrainian, English and Russian via early i18n structure and late translation polishing.

Media context capability:
- stable asset ID;
- exact hash;
- perceptual fingerprint;
- normalized preview;
- optional OCR/local analysis;
- semantic analysis only when needed;
- order/conversation links.

Cheap cascade:
exact hash -> perceptual hash -> preview/OCR -> AI vision only when ambiguous.

AI escalation package should include customer ID, request, relevant dialogue, related orders/assets and the unresolved question.
