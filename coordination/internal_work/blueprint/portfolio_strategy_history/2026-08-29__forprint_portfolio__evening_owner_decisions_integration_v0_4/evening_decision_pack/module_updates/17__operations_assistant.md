# Operations Assistant — evening delta

Universal employee-facing operational assistant.

Potential quick actions:
- production problem;
- equipment incident;
- troubleshooting;
- work instructions;
- QR/context lookup;
- request spare/service;
- escalate to responsible person.

Equipment incident flow:
employee -> choose equipment -> choose typical fault/code/description -> approved troubleshooting -> part/service request -> responsible-person confirmation -> supplier/payment/logistics workflow -> repair verification -> close incident.

Operations Assistant is the interface, not canonical equipment/reference storage.

Library can hold equipment/part/instruction references.
Operations Control Registry can hold active incident state.
