# Cloud Backup Manager — evening delta

Role:
backup, versioned snapshots, retention and tested restore.

Not responsible for live OS/admin tasks.

When capacity allows, retain multiple generations instead of one overwritten mirror.

Snapshot metadata may include timestamp, checksum, source revision, related Git revision, reason/label and retention class.

Critical protected classes:
- central structured business data;
- customer asset/object storage;
- Library/reference storage where applicable;
- explicitly registered critical directories.

Plan periodic restore verification.

Owner accepts a coarse business upper bound of up to 24 hours of lost data as recoverable; expanded review should propose stronger RPO options.
