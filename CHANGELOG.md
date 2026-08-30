# Changelog

## Unreleased
- Reject input/HTML/JSON path collisions so report generation cannot overwrite the source JSONL or another output.
- Add regression coverage for input/output and output/output collisions.

## 1.0.1
- Treat valid non-object JSONL rows as malformed input instead of crashing later.
- Interpret timezone-less ISO timestamps as UTC for deterministic reports.
- Add regression coverage for both cases.

## 1.0.0
- Initial public OSS release.
