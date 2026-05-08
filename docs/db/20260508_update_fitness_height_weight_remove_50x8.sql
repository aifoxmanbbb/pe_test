-- 2026-05-08 体测项目调整：新增身高/体重，移除 50米×8往返跑
SET NAMES utf8mb4;

UPDATE vadmin_pef_standard_item si
JOIN vadmin_pef_standard s ON s.id = si.standard_id
SET si.is_delete = 1, si.update_datetime = NOW()
WHERE s.biz_type = 'fitness'
  AND si.is_delete = 0
  AND (
    si.item_code = 'run_50x8'
    OR si.item_name IN ('50米×8往返跑', '50米x8往返跑', '50x8往返跑')
  );

INSERT INTO vadmin_pef_standard_item (
  standard_id, item_code, item_name, gender, calc_mode,
  pass_threshold, excellent_threshold, full_threshold, segment_json,
  is_required, is_gate_item, max_score, sort,
  create_datetime, update_datetime, is_delete
)
SELECT
  s.id, 'height', '身高', 'all', 'record',
  NULL, NULL, NULL, JSON_ARRAY(),
  1, 0, 0, -2,
  NOW(), NOW(), 0
FROM vadmin_pef_standard s
WHERE s.biz_type = 'fitness'
  AND s.is_delete = 0
  AND NOT EXISTS (
    SELECT 1
    FROM vadmin_pef_standard_item si
    WHERE si.standard_id = s.id
      AND si.item_code = 'height'
      AND si.is_delete = 0
  );

INSERT INTO vadmin_pef_standard_item (
  standard_id, item_code, item_name, gender, calc_mode,
  pass_threshold, excellent_threshold, full_threshold, segment_json,
  is_required, is_gate_item, max_score, sort,
  create_datetime, update_datetime, is_delete
)
SELECT
  s.id, 'weight', '体重', 'all', 'record',
  NULL, NULL, NULL, JSON_ARRAY(),
  1, 0, 0, -1,
  NOW(), NOW(), 0
FROM vadmin_pef_standard s
WHERE s.biz_type = 'fitness'
  AND s.is_delete = 0
  AND NOT EXISTS (
    SELECT 1
    FROM vadmin_pef_standard_item si
    WHERE si.standard_id = s.id
      AND si.item_code = 'weight'
      AND si.is_delete = 0
  );
