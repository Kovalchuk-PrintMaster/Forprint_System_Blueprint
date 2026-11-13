# Duplicate Check

Decision: **OVERLAPPING CONTINUATION — INDEX NEW DELTA ONLY**

Compared with the already processed `12.09` source:

- Full 14.09 export message blocks: **61**
- Shared message IDs: **18**
- Genuinely new message IDs: **43**
- Messages preserved in 12.09 but absent from this re-export: **5**

This is therefore neither a full duplicate nor a clean independent chat.  
To prevent duplication, the DFTB package indexes **only the 43 new messages**. The 18 shared messages remain represented only by the existing `DFTB-blueprint-2026-09-12` package.
