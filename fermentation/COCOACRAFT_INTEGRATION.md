# CocoaCraft Fermentation — supplier-first integration contract (draft v0.2)

**Phase 1 owner and UI:** CocoaCraft Supplier Module / Supplier Portal. Farmers, cooperatives and supplier users define fermentation profiles, log batches and submit evidence. **Do not insert fermentation controls into the maker production-run workflow.** Maker users may access approved supplier history only through authorized supplier-sharing and quality-review flows.

## Existing code verified

- Supplier portal UI: `pages/supplier-portal/index.tsx`.
- Authenticated portal context: `lib/supplier-quality/portal.ts` and `pages/api/supplier-portal/context.ts`.
- Supplier lot endpoints: `pages/api/supplier-portal/lots/index.ts` and `[id].ts`.
- `getSupplierPortalContext` verifies an **ACTIVE** `supplier_portal_memberships` record and resolves **both** `orgId` and `supplierId`. `supplierCanContribute` permits `ADMIN` and `CONTRIBUTOR` rather than viewers.
- Existing schema snapshot SQL: `orgs`, `org_members`, `supplier_portal_memberships`, `suppliers`, `supplier_lot_reviews`, `supplier_quality_plans`, `supplier_lot_check_results`, `ingredient_lots`. `ingredient_lots` represents maker-side received inventory and is **not** required to begin supplier-side fermentation.

## Phase 1 ownership and lot lifecycle

1. Supplier portal membership determines authorization, not a client-provided `org_id` or `supplier_id`.
2. Every fermentation profile, version, batch, observation and event must have an enforced owner pair `(org_id, supplier_id)`. Resolve supplier membership against BOTH keys; enforce composite foreign keys through child records.
3. Farm/cooperative producer lot code is recorded at batch creation. A supplier may have several fermentations within a later aggregated shipment lot. Preserve source-to-output lot associations rather than overwriting IDs.
4. Link optional `supplier_lot_review_id` when the lot submission is created. Cross-check both supplier and organization on any attachment.
5. `ingredient_lot_id` is **optional and downstream only**. Makers can see authorized, finalized history as supporting evidence within supplier quality or lot traceability, never unrestricted supplier work-in-progress.
6. No automatic cross-organization visibility. Supplier sharing requires a separately reviewed, explicit access path: existing supplier portal membership does not itself grant any buyer unrestricted fermentation access.

## Process data

- Approved profiles are immutable version snapshots; drafts are editable without recording every draft edit.
- Batch observations and events are append-only operational history, including recording time, elapsed time, measurement source, probe position, units, operator, and correction/supersession linkage when needed.
- Targets are process-specific temperature envelopes, not universal food-safety thresholds. pH can distinguish pulp and bean; events include turns, sampling, inspections, and deviations.
- No direct sensor/cloud credentials in this public repository. CocoaCraft identity is validated server-side using its existing session handling.

## Database work to prepare in main CocoaCraft only

Five proposed structures: `fermentation_profiles`, `fermentation_profile_versions`, `fermentation_batches`, `fermentation_observations`, `fermentation_events`.

- Include `org_id` and `supplier_id` in every table, plus scoped, immutable foreign keys to the owning entity where appropriate.
- Validate ownership using `supplier_portal_memberships` with `status = 'ACTIVE'` for contributor writes, and read access according to the actual existing supplier portal roles and approved sharing policy.
- Do **not** reuse maker production-plan rows as Phase 1 process requirements. Supplier-side process inspections belong to approved fermentation profile versions, with optional later alignment to `supplier_quality_plan_rows`/supplier lot checks.
- Link supplier lot records by `(org_id, supplier_id, supplier_lot_review_id)` only when verified against schema keys and constraints. Do not force maker inventory linkage.
- Migrations belong under main CocoaCraft `supabase/migrations/` following examination of `docs/supabase-schema-snapshot.json` and `.sql`. **Do not commit a migration triggering automatic production application before validation.**
- Preserve full released-profile revision and actual batch history, without draft keystroke history.

## Current limitations

This document is the integration contract only. The Ferment package contains transport models and temperature-envelope assessment, **not** a live supplier API, UI, schema migration, verified end-to-end access, or deployment. The main repository's JSON snapshot returned empty on the last inspection; SQL snapshot was reviewed.
