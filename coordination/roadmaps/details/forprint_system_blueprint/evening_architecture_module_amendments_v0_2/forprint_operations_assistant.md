# forprint_operations_assistant — Evening Architecture Amendment v0.2

Status: Planning input; no autonomous repair authority.

## Equipment troubleshooting

Provide `equipment -> exact error code / symptom -> indexed approved documentation -> result`.

Preferred lookup: exact model+code, approved keyword/symptom index, then bounded semantic candidate lookup only within approved documentation.

Return Ukrainian grounded explanation, source/manual provenance, original figures/ordered figure sequence when available, or explicit `NOT_FOUND`.

## Hard boundary

For production equipment the assistant does not invent repairs and does not freely browse the internet for repair instructions.

## Escalation

Normal operator -> production manager. Authorized production manager -> approved service request channel. Speech-to-text drafting may assist the request.

Static images/step galleries first; animation later only if useful.
