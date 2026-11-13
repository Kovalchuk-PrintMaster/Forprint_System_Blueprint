# External reference basis

These references support the architecture patterns used in this package. They are background evidence, not ForPrint authority.

1. NIST SP 800-218 — Secure Software Development Framework (SSDF)
   https://csrc.nist.gov/pubs/sp/800/218/final

2. Google SRE — Release Engineering
   https://sre.google/sre-book/release-engineering/

3. Google SRE Workbook — Canarying Releases
   https://sre.google/workbook/canarying-releases/

4. AWS — Blue/Green Deployments: Managing Data Synchronization and Schema Changes
   https://docs.aws.amazon.com/whitepapers/latest/blue-green-deployments/best-practices-for-managing-data-synchronization-and-schema-changes.html

5. OWASP GenAI — Excessive Agency
   https://genai.owasp.org/llmrisk/llm062025-excessive-agency/

6. Open Policy Agent documentation
   https://www.openpolicyagent.org/docs
   https://www.openpolicyagent.org/docs/cicd

Interpretation used for ForPrint:
- reproducible/automated build-test-release;
- canary/shadow as mature deployment safety;
- backward-compatible schema evolution;
- least functionality/permissions for production AI tool surfaces;
- policy decision separated from action execution.
