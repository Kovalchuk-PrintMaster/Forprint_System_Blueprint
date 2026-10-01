# First contour — Creator Empirical Learning Foundation

## What we are trying to achieve

The first new GDL contour should not try to automate the whole design laboratory.
It should give us a disciplined way to learn from real work.

Tomorrow a real request may be as small as: **“The customer wants a menu.”**

At that point the useful questions are what information is actually missing, what a normal manager can ask, what the customer can reasonably provide, what may remain open, when there is enough information for a Creator prompt, what prompt structure produces a good result, how many attempts were needed, what the operator thought, what the customer accepted, and what should become reusable knowledge.

## Experimental workflow

A manager should be able to start a fresh AI chat with one product-specific loader/instruction such as `MENU_INTAKE_EXPERIMENT`.

The assistant should:

1. ask the manager to provide everything already known;
2. identify missing information;
3. generate a concise copy-ready customer message with the next questions;
4. accept the customer's reply;
5. explicitly preserve unknowns and permissions;
6. avoid inventing brand/style information not provided by the customer;
7. continue until the minimum information for a Creator prompt is available;
8. build the Creator prompt;
9. preserve the full interaction as an empirical case;
10. later record the Creator result and outcome.

A manager does not need design, programming, prompt-engineering, or GDL architecture knowledge.

## Explicit creative discretion

If a customer has no logo, photos or references and says “I have nothing; do it however you think is best,” this is not merely missing data. It is a meaningful customer authorization and should be recorded as such. The flow should stop forcing aesthetic-choice questions that the customer explicitly delegated.

## Why failures matter

A strong dated-diary internal-block prompt and a poor cover prompt should both be retained. We need to understand why one succeeded and one failed. Failed prompts are evidence, not trash.

## Long-term outcome

We should eventually be able to say, based on real cases, which tasks Creator handles well, which should move to local deterministic tools, which prompt structures shorten revision cycles, and where human confirmation is mandatory.
