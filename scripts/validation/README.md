# Validation Scripts

This directory contains structured validation scripts for ForPrint System Blueprint artifacts.

New validators should be grouped here instead of placing every validation script directly under `scripts/`.

Legacy validators may remain in `scripts/` until a dedicated migration checkpoint is approved.

Validation scripts in this directory should be safe, read-only by default, and suitable for use from Makefile targets and Blueprint check reports.
