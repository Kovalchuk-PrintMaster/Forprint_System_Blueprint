# Modular Topology and Resilience Standards

This standards package defines how ForPrint modules should be structured, connected, protected from cross-module ownership leaks, and prepared for resilient operation.

The goal is to keep ForPrint modular, local-first, debuggable, and service-ready without prematurely turning the project into a heavy microservice platform.

Read in this order:

1. `architecture_topology_policy.md`
2. `data_ownership_and_storage_policy.md`
3. `module_interaction_reliability_policy.md`
4. `gateway_responsibility_policy.md`
5. `module_global_context_policy.md`

These standards are advisory by default and should be applied gradually through Blueprint-approved prompts and module checkpoints.
