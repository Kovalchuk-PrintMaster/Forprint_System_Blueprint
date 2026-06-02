# Configuration Policy

## Status

Target standard

## Purpose

This document defines the ForPrint policy for configuration, paths, thresholds and constants.

## Core rule

Avoid hardcoded paths, thresholds, repository locations, timeout values and environment-specific constants in business logic.

Prefer configuration files.

## Preferred config directory

```text
config/

For larger modules, config may be split by domain:

config/
├── app.yaml
├── storage.yaml
├── integrations.yaml
├── coordination.yaml
└── thresholds.yaml
Coordination configuration

Coordination-related settings should be config-driven where practical.

Examples:

Blueprint repository path;
module repository paths;
activity warning thresholds;
activity critical thresholds;
status file paths;
report output paths.
Secrets

Secrets must not be committed to Git.

Do not store in repository config:

tokens;
passwords;
private keys;
real credentials;
production 1C access;
private client data.

Use environment variables or external secret storage.

Thresholds

Timing and priority thresholds should not be hardcoded.

Example future config:

activity_thresholds:
  p0:
    warning_after_days_without_report: 3
    critical_after_days_without_report: 7
  p1:
    warning_after_days_without_report: 7
    critical_after_days_without_report: 14
Path policy

Absolute paths may be used in local developer config when needed, but they should be isolated in config files and not scattered through business logic.


---
