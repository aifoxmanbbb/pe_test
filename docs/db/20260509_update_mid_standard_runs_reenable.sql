-- 2026-05-09 初中标准恢复 1000米/800米：
-- 目标标准：
--   - 国家学生体质健康测试（初中）
--   - 学生体质健康达标比赛评分标准（初中）
-- 说明：系统按 vadmin_pef_standard_item.is_delete=0 读取启用项目。
--       本脚本可重复执行：优先恢复已被逻辑删除的项目；若项目缺失，则从库内已有初中跑步规则复制。

SET NAMES utf8mb4;

DROP TEMPORARY TABLE IF EXISTS tmp_mid_standard_target;
CREATE TEMPORARY TABLE tmp_mid_standard_target AS
SELECT
  id,
  biz_type,
  name
FROM vadmin_pef_standard
WHERE is_delete = 0
  AND stage_type = 'mid'
  AND name IN (
    '国家学生体质健康测试（初中）',
    '学生体质健康达标比赛评分标准（初中）'
  );

-- 1) 恢复目标标准中已经存在但被逻辑删除的 1000米/800米项目。
UPDATE vadmin_pef_standard_item si
JOIN tmp_mid_standard_target ts ON ts.id = si.standard_id
SET
  si.is_delete = 0,
  si.is_required = 1,
  si.is_gate_item = CASE
    WHEN si.calc_mode = 'threshold'
      OR si.item_code IN ('run_gate', '1000m_gate', '800m_gate')
      OR si.item_name LIKE '%门槛%'
      THEN 1
    ELSE si.is_gate_item
  END,
  si.update_datetime = NOW()
WHERE si.is_delete = 1
  AND (
    si.item_code IN ('run_1000', 'run_800', 'run_gate', '1000m', '800m', '1000m_gate', '800m_gate')
    OR si.item_name IN ('1000米', '1000米跑', '男生1000米', '男生1000米(门槛)', '800米', '800米跑', '女生800米', '女生800米(门槛)')
    OR si.item_name LIKE '%1000米%'
    OR si.item_name LIKE '%800米%'
  );

-- 2) 若目标标准完全缺少对应项目，则从现有初中标准中复制规则。
DROP TEMPORARY TABLE IF EXISTS tmp_mid_run_expected;
CREATE TEMPORARY TABLE tmp_mid_run_expected AS
SELECT 'run_1000' AS item_code, '1000米跑' AS item_name, 'male' AS gender, 50 AS sort
UNION ALL
SELECT 'run_800' AS item_code, '800米跑' AS item_name, 'female' AS gender, 51 AS sort;

DROP TEMPORARY TABLE IF EXISTS tmp_mid_run_source_candidate;
CREATE TEMPORARY TABLE tmp_mid_run_source_candidate AS
SELECT
  si.id AS source_item_id,
  CASE
    WHEN si.item_code IN ('run_1000', '1000m', '1000m_gate')
      OR si.item_name LIKE '%1000米%'
      THEN 'run_1000'
    ELSE 'run_800'
  END AS item_code,
  CASE
    WHEN si.item_code IN ('run_1000', '1000m', '1000m_gate')
      OR si.item_name LIKE '%1000米%'
      THEN 'male'
    ELSE 'female'
  END AS target_gender,
  CASE
    WHEN target_src.id IS NOT NULL
      AND si.item_code IN ('run_1000', 'run_800')
      AND si.calc_mode = 'segment'
      THEN 130
    WHEN s.stage_type = 'mid'
      AND s.biz_type = 'fitness'
      AND s.name = '国家学生体质健康测试（初中）'
      AND si.item_code IN ('run_1000', 'run_800')
      THEN 120
    WHEN s.stage_type = 'mid'
      AND si.item_code IN ('run_1000', 'run_800')
      AND si.calc_mode = 'segment'
      THEN 110
    WHEN s.stage_type = 'mid' AND si.calc_mode = 'segment' THEN 100
    WHEN target_src.id IS NOT NULL THEN 90
    WHEN s.stage_type = 'mid' THEN 70
    ELSE 50
  END
  + CASE
      WHEN si.gender = 'male' AND (
        si.item_code IN ('run_1000', '1000m', '1000m_gate')
        OR si.item_name LIKE '%1000米%'
      ) THEN 5
      WHEN si.gender = 'female' AND (
        si.item_code IN ('run_800', '800m', '800m_gate')
        OR si.item_name LIKE '%800米%'
      ) THEN 5
      ELSE 0
    END AS source_priority
FROM vadmin_pef_standard_item si
JOIN vadmin_pef_standard s ON s.id = si.standard_id
LEFT JOIN tmp_mid_standard_target target_src ON target_src.id = s.id
WHERE s.is_delete = 0
  AND s.stage_type = 'mid'
  AND si.is_delete = 0
  AND si.item_name NOT LIKE '%/%'
  AND si.item_name NOT LIKE '%／%'
  AND (
    (
      si.gender IN ('male', 'all')
      AND (
        si.item_code IN ('run_1000', 'run_gate', '1000m', '1000m_gate')
        OR si.item_name LIKE '%1000米%'
      )
    )
    OR (
      si.gender IN ('female', 'all')
      AND (
        si.item_code IN ('run_800', 'run_gate', '800m', '800m_gate')
        OR si.item_name LIKE '%800米%'
      )
    )
  );

DROP TEMPORARY TABLE IF EXISTS tmp_mid_run_source_priority;
CREATE TEMPORARY TABLE tmp_mid_run_source_priority AS
SELECT
  item_code,
  target_gender,
  MAX(source_priority) AS source_priority
FROM tmp_mid_run_source_candidate
GROUP BY item_code, target_gender;

DROP TEMPORARY TABLE IF EXISTS tmp_mid_run_source_ids;
CREATE TEMPORARY TABLE tmp_mid_run_source_ids AS
SELECT
  c.item_code,
  c.target_gender,
  MAX(c.source_item_id) AS source_item_id
FROM tmp_mid_run_source_candidate c
JOIN tmp_mid_run_source_priority p
  ON p.item_code = c.item_code
 AND p.target_gender = c.target_gender
 AND p.source_priority = c.source_priority
GROUP BY c.item_code, c.target_gender;

INSERT INTO vadmin_pef_standard_item (
  standard_id,
  item_code,
  item_name,
  gender,
  calc_mode,
  pass_threshold,
  excellent_threshold,
  full_threshold,
  segment_json,
  is_required,
  is_gate_item,
  max_score,
  sort,
  create_datetime,
  update_datetime,
  is_delete
)
SELECT
  ts.id,
  e.item_code,
  e.item_name,
  e.gender,
  src.calc_mode,
  src.pass_threshold,
  src.excellent_threshold,
  src.full_threshold,
  src.segment_json,
  1,
  CASE
    WHEN src.calc_mode = 'threshold'
      OR src.item_code IN ('run_gate', '1000m_gate', '800m_gate')
      OR src.item_name LIKE '%门槛%'
      THEN 1
    ELSE 0
  END,
  src.max_score,
  e.sort,
  NOW(),
  NOW(),
  0
FROM tmp_mid_standard_target ts
CROSS JOIN tmp_mid_run_expected e
JOIN tmp_mid_run_source_ids src_ids
  ON src_ids.item_code = e.item_code
 AND src_ids.target_gender = e.gender
JOIN vadmin_pef_standard_item src ON src.id = src_ids.source_item_id
WHERE NOT EXISTS (
  SELECT 1
  FROM vadmin_pef_standard_item exists_si
  WHERE exists_si.standard_id = ts.id
    AND exists_si.is_delete = 0
    AND (
      (
        e.item_code = 'run_1000'
        AND exists_si.gender IN ('male', 'all')
        AND (
          exists_si.item_code IN ('run_1000', 'run_gate', '1000m', '1000m_gate')
          OR exists_si.item_name LIKE '%1000米%'
        )
      )
      OR (
        e.item_code = 'run_800'
        AND exists_si.gender IN ('female', 'all')
        AND (
          exists_si.item_code IN ('run_800', 'run_gate', '800m', '800m_gate')
          OR exists_si.item_name LIKE '%800米%'
        )
      )
    )
);

-- 校验目标标准当前启用的 1000米/800米项目。
SELECT
  s.name AS standard_name,
  s.biz_type,
  si.item_code,
  si.item_name,
  si.gender,
  si.calc_mode,
  si.is_gate_item,
  si.max_score,
  si.sort,
  si.is_delete
FROM vadmin_pef_standard s
JOIN vadmin_pef_standard_item si ON si.standard_id = s.id
WHERE s.id IN (SELECT id FROM tmp_mid_standard_target)
  AND si.is_delete = 0
  AND (
    si.item_code IN ('run_1000', 'run_800', 'run_gate', '1000m', '800m', '1000m_gate', '800m_gate')
    OR si.item_name LIKE '%1000米%'
    OR si.item_name LIKE '%800米%'
  )
ORDER BY s.name, si.sort, si.id;
