# Make Command Standard

## Status

Target standard

## Purpose

This document defines preferred Makefile command names across ForPrint modules.

The goal is to reduce cognitive load when moving between repositories.

## Core commands

Every active Python-based ForPrint module should eventually support:

```text
make install
make test
make lint
make format
make check
make check-report
make clean
Expected behavior
make install

Install dependencies for the module virtual environment.

make test

Run automated tests.

make lint

Run lint checks.

make format

Run code formatter.

make check

Run lint and tests.

make check-report

Run the module check-report runner and generate machine/human reports.

make clean

Remove local caches and generated temporary files.

Future coordination commands

These are planned target commands:

make blueprint-pull
make coordination-check
make status-report
make blueprint-pull

Pull ForPrint System Blueprint updates.

make coordination-check

Check whether the module has active Blueprint global/module-specific instructions to apply.

make status-report

Update or validate local coordination/status files.

Rule

Module-specific commands are allowed.

But common commands should keep common names and similar behavior.


---
