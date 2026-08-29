# Integration Gateway — evening delta

Purpose: prevent uncontrolled or ambiguous module-to-module communication.

Gateway knows:
- allowed caller/callee relationships;
- operations;
- required/optional fields;
- data types;
- versions;
- allowed defaults;
- deprecated/forbidden values;
- structured error codes.

Rule:
No semantic guessing between business modules where a formal contract exists.

Live scenarios:
- deprecated `Taxi-388` is rejected before Logistics receives it;
- receiver expects 6 fields but sender repeatedly sends 5: explicit default may pass with drift finding, otherwise fail closed;
- repeated fallback creates an aggregated contract-drift finding.

Gateway diagnoses and explains; it should not arbitrarily rewrite another module's code.

Legacy 1C mapping remains outside Gateway's core role.
