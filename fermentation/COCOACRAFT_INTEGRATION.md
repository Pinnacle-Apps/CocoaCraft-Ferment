# CocoaCraft integration contract — draft v0.1

The public fermentation engine is an AGPL-3.0-or-later domain package. CocoaCraft (main application) remains the authoritative identity, organization, lot, production and supplier-quality system. This document is an integration proposal, not a deployed connector.

## Existing CocoaCraft structures verified from `docs/supabase-schema-snapshot.sql`

- `orgs(id)`, `org_members(org_id,user_id,role)` with roles owner/admin/editor/viewer.
- `ingredient_lots(id,org_id,ingredient_id,lot_code,supplier_quality_review_id)`.
- `supplier_lot_reviews(id,org_id,ingredient_lot_id,supplier_id,...)`.
- `production_plans(id,org_id,formulation_id,revision,status)`.
- `production_plan_rows(id,production_plan_id,process_step_name,check_name,target_value,min_value,max_value,unit,record_type,required,is_user_modified,...)`.
- `roast_profiles(id,org_id,status,...)`. Existing roast workflow should remain unchanged.

The JSON snapshot was empty when fetched: use SQL snapshot as currently available structural evidence and repair snapshot generation separately before rollout.

## Transport and authorization

1. CocoaCraft user authenticates with the same Supabase Auth session used by the main application. Never trust `org_id` supplied by a client without resolving active organization membership on the server.
2. Resolve `source_lot_id` to an ingredient lot (where available); verify the lot belongs to the same organization. Upstream farm batches may precede CocoaCraft inventory intake, so source-lot linking must be optional; persist a producer lot code and origin separately.
3. Validate `profile_id` and `profile_revision` against a released version; snapshot the exact release for each execution.
4. Pass production-plan checks into fermentation as a read-only set of requirements. On reconciliation never overwrite rows where `is_user_modified = true`; retain source IDs and stable deduplication keys.
5. Record manual observations and future sensor readings under the same append-only event model; units and probe locations are explicit. Temperature envelopes are process targets, not food-safety limits.
6. Use paginated event retrieval and server-side timestamps; enforce ingestion idempotency with externally supplied UUIDs.

## Proposed database migration (main CocoaCraft repository only)

Five structures: `fermentation_profiles` (mutable drafts), `fermentation_profile_versions` (immutable approved snapshots), `fermentation_batches`, `fermentation_observations`, `fermentation_events`. Each table carries `org_id`, with org-membership-scoped RLS. Enforce cross-tenant parent linkage through composite foreign keys `(org_id,id)`; never rely solely on application checks.

Approval produces one immutable revision; draft keystrokes do not generate audit records. Once released, create new revisions; never update or delete historical versions or actual events. Separately control service-side ingestion permissions. Do not create direct client write permissions to immutable records until a reviewed append-only policy and server authorization path exist.

Add migrations only under main CocoaCraft's `supabase/migrations/` and let its existing automated migration + schema snapshot pipeline apply them **only after review**. Do not commit a migration to a branch that can deploy automatically until workflow behavior is verified.

## Not yet implemented

- Live OAuth/browser handoff and CocoaCraft navigation
- RLS migration and tables in production
- Bidirectional API persistence and lot synchronization
- Approved profile version lifecycle and permissioned release actions
- Sensor ingestion, calibration, and operator acceptance workflows
