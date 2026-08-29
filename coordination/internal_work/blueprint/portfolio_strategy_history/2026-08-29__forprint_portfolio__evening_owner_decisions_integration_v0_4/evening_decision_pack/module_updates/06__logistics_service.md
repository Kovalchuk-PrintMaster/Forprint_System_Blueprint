# Logistics Service — evening delta

Own physical shipment/delivery state and delivery execution/tracking.

Urgent taxi scenario:
normal notification -> warning -> critical Telegram/action-required message -> automated voice call -> defined failure policy.

Voice capability:
- phase 1: urgent automated voice notification;
- phase 2: bounded interactive AI call for simple reliable questions, with complex cases returned to text.

Packaging/weight:
- Library: canonical product dimensions/weight and packaging profiles;
- Operations Control Registry: order contents/context;
- Logistics: choose delivery mode, estimate shipment profile, store actual measured shipment facts.
