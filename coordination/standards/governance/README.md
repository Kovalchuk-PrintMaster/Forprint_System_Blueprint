# Standards Governance

This directory contains standards about how ForPrint Blueprint standards are organized, indexed, grouped and maintained.

These documents do not define business module behavior directly.

They define how standards themselves should be structured so the project remains readable, navigable and maintainable as the number of standards grows.

## Module prompt execution and reporting

`module_prompt_execution_and_reporting_protocol.md` defines the global end-to-end workflow for module assistants that receive prompts from Blueprint.

It clarifies that modules may read Blueprint prompts and standards, but must write only inside their own repositories.

Blueprint-side incoming reports, review records and prompt queue acceptance metadata are created only from the Blueprint context.
