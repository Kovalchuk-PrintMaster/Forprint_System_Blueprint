# Live owner scenarios that must survive into roadmaps

## LS-01 — Count large paper stacks by height
For thousands of sheets, an employee may measure stack height instead of counting every sheet.

## LS-02 — Equipment failure affects pricing/load
If a machine fails and capacity drops, an authorized admin may temporarily change Calculator coefficients to reduce demand for the affected product class.

## LS-03 — Material shortage before promised deadline
Detect true available-to-promise shortage, find supplier, obtain invoice/payment, track urgent inbound delivery and reassess customer promise.

## LS-04 — Taxi is waiting, customer does not respond
Escalate normal message -> warning -> critical Telegram alert -> direct voice call.

## LS-05 — Same filename, different image
Two files named `image1.png` may be unrelated. Use internal asset identity and content fingerprints.

## LS-06 — Same visual asset, different file encoding
PNG/JPEG/PDF derivatives may represent the same artwork. Detect relationship without declaring physical files identical.

## LS-07 — "Print the same as last year"
Use customer/date/order/asset context, show likely preview and ask for confirmation.

## LS-08 — Prepress automatic correction
Analyze file, explain problems, offer safe fixes, show preview, require confirmation before proceeding.

## LS-09 — 1C cannot represent all ForPrint data
Keep complete internal truth, adapt the subset 1C accepts and expose transformed/omitted data.

## LS-10 — Deprecated taxi provider
Gateway blocks unsupported provider with a structured error and points to current contract/capability info.

## LS-11 — Six fields expected, five repeatedly sent
Explicit allowed default may pass with drift finding; otherwise fail closed.

## LS-12 — Oversized client file
Accept into managed temporary storage if policy allows, warn about TTL, route to Prepress, create compact production-ready derivative, expire oversized source by policy.
