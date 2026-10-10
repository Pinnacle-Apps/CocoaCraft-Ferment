# CocoaCraft Ferment — initial process model

This new, standalone cocoa fermentation domain package lives alongside the retained Artisan/CocoaCraft-Roast sources. It is **not** a deployed fermentation service and does not modify production CocoaCraft or Supabase.

## Implemented

- Versioned profile and batch transport models, scoped by CocoaCraft organization IDs.
- Multi-day target temperature operating envelopes (not a single ideal curve).
- Manual, sensor and imported observation provenance; optional pulp/bean pH.
- Turning, inspection, sample and deviation event schema.
- Interpolated target-vs-actual temperature assessments, with explicit `unassessed` status when no envelope exists.
- Input validation and unit tests.

Run from the repository root with the existing headless service dependencies installed:

```sh
python -m unittest discover -s fermentation/tests -v
```

## Deliberate limitations

No API exposure, OAuth endpoints, database writes, or hardware automation are included yet. Records remain caller-owned; do not treat client-supplied org IDs as authorization. Before exposing API routes, reuse the Roast service's server-validated CocoaCraft identity and resolve organization membership server-side. Preserve immutable released profile revisions and an append-only operational record in database migrations, after comparing the main CocoaCraft repository's current Supabase structure snapshots.

The threshold checks are informational process monitoring only, **not** validated food-safety limits or automatic bean acceptance decisions. Targets must be defined and validated by the relevant operator.

## License and attribution

The repository retains the upstream Artisan copyright notices and AGPL-3.0 terms. Newly added fermentation source files identify their license. See the repository root `LICENSE`.
