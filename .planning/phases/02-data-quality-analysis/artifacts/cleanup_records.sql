-- SliceInsights — Data Cleanup SQL
-- Generated: 2026-03-19 from Phase 2 audit results
-- WARNING: Review each statement before executing. Run in a transaction.

BEGIN;

-- ============================================================
-- 1. Non-Paddle Removal
-- ============================================================
-- AUDIT RESULT: 0 non-paddles detected
-- No cleanup needed — all 86 records are valid paddle items.

-- ============================================================
-- 2. Duplicate Resolution
-- ============================================================
-- AUDIT RESULT: 0 duplicate groups detected
-- No cleanup needed — all 86 paddles are unique.

-- ============================================================
-- 3. Orphaned Market Offers
-- ============================================================
-- Safety check: deactivate any offers pointing to deleted paddles
UPDATE market_offers
SET is_active = false
WHERE paddle_id NOT IN (SELECT id FROM paddle_master)
  AND is_active = true;

-- ============================================================
-- 4. Specs Confidence Recalculation
-- ============================================================
-- All 86 paddles have specs_confidence = 1.0 (default) but
-- validation_sources = '{}' and 8/9 required fields are NULL.
-- The confidence should be recalculated to 0.0 for accuracy.
--
-- NOTE: Use the Python function calculate_specs_confidence()
-- instead of raw SQL for safety. The following UPDATE is provided
-- for reference but should be validated before execution:
--
-- UPDATE paddle_master
-- SET specs_confidence = 0.0
-- WHERE validation_sources = '{}'
--   AND (core_thickness_mm IS NULL
--        OR face_material IS NULL
--        OR core_material IS NULL
--        OR shape IS NULL
--        OR swing_weight IS NULL
--        OR spin_rpm IS NULL
--        OR power_rating IS NULL
--        OR handle_length IS NULL);

-- ============================================================
-- 5. Low-Price Review (informational)
-- ============================================================
-- 3 paddles flagged as leisure/low-price (< R$ 450):
-- These MAY be legitimate entry-level paddles, not necessarily errors.
--
-- SELECT pm.model_name, b.name as brand, mo.price_brl
-- FROM paddle_master pm
-- JOIN brands b ON pm.brand_id = b.id
-- JOIN market_offers mo ON mo.paddle_id = pm.id AND mo.is_active = true
-- WHERE mo.price_brl < 450
-- ORDER BY mo.price_brl;
--
-- Results:
-- [3Rdshot] Oberon Mini — R$ 109
-- [3Rdshot] Start 16mm — R$ 367
-- [Joola] Agassi Champion SS25 — R$ 449

COMMIT;
