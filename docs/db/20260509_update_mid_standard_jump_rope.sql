-- 2026-05-09 初中标准项目调整：
-- 1) 在以下标准中开启/恢复 1000米/800米：
--    - 国家学生体质健康测试（初中）
--    - 学生体质健康达标比赛评分标准（初中）
-- 2) 添加/恢复 立定跳远、1分钟跳绳。
-- 说明：vadmin_pef_standard_item 没有 disabled 字段，系统按 is_delete=0 读取项目，
--       因此“开启”使用恢复逻辑删除；新增项目优先复用库内已有同名项目的评分段。

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

-- 开启/恢复 1000米/800米及其门槛项。
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

-- 如果目标标准里已有被禁用过的跳绳/跳远项目，优先恢复，保留原评分段。
UPDATE vadmin_pef_standard_item si
JOIN tmp_mid_standard_target ts ON ts.id = si.standard_id
SET
  si.is_delete = 0,
  si.item_code = CASE
    WHEN si.item_name LIKE '%跳绳%' OR si.item_code IN ('rope', 'skip_rope', 'jump_rope') THEN 'rope'
    ELSE 'jump'
  END,
  si.item_name = CASE
    WHEN si.item_name LIKE '%跳绳%' OR si.item_code IN ('rope', 'skip_rope', 'jump_rope') THEN '1分钟跳绳'
    ELSE '立定跳远'
  END,
  si.is_required = 1,
  si.is_gate_item = 0,
  si.sort = CASE
    WHEN si.item_name LIKE '%跳绳%' OR si.item_code IN ('rope', 'skip_rope', 'jump_rope') THEN 30
    ELSE 40
  END,
  si.update_datetime = NOW()
WHERE si.is_delete = 1
  AND (
    si.item_code IN ('rope', 'skip_rope', 'jump_rope', 'jump', 'long_jump', 'standing_long_jump')
    OR si.item_name LIKE '%跳绳%'
    OR si.item_name LIKE '%跳远%'
  );

-- 从库内已有启用项目中挑选同名评分规则作为模板。
DROP TEMPORARY TABLE IF EXISTS tmp_mid_item_source_candidate;
CREATE TEMPORARY TABLE tmp_mid_item_source_candidate AS
SELECT
  si.id AS source_item_id,
  s.biz_type AS source_biz_type,
  CASE
    WHEN si.item_name LIKE '%跳绳%' OR si.item_code IN ('rope', 'skip_rope', 'jump_rope') THEN 'rope'
    ELSE 'jump'
  END AS item_key,
  si.gender,
  CASE
    WHEN s.stage_type = 'mid' AND s.biz_type = 'pe' AND s.name LIKE '%五项目%' THEN 100
    WHEN s.stage_type = 'mid' AND s.biz_type = 'pe' THEN 90
    WHEN s.stage_type = 'mid' THEN 80
    WHEN s.biz_type = 'pe' THEN 60
    ELSE 50
  END AS source_priority
FROM vadmin_pef_standard_item si
JOIN vadmin_pef_standard s ON s.id = si.standard_id
WHERE s.is_delete = 0
  AND s.stage_type = 'mid'
  AND si.is_delete = 0
  AND (
    si.item_code IN ('rope', 'skip_rope', 'jump_rope', 'jump', 'long_jump', 'standing_long_jump')
    OR si.item_name LIKE '%跳绳%'
    OR si.item_name LIKE '%跳远%'
  );

DROP TEMPORARY TABLE IF EXISTS tmp_mid_item_source_priority;
CREATE TEMPORARY TABLE tmp_mid_item_source_priority AS
SELECT
  source_biz_type,
  item_key,
  gender,
  MAX(source_priority) AS source_priority
FROM tmp_mid_item_source_candidate
GROUP BY source_biz_type, item_key, gender;

DROP TEMPORARY TABLE IF EXISTS tmp_mid_item_source_ids;
CREATE TEMPORARY TABLE tmp_mid_item_source_ids AS
SELECT
  c.source_biz_type,
  c.item_key,
  c.gender,
  MAX(c.source_item_id) AS source_item_id
FROM tmp_mid_item_source_candidate c
JOIN tmp_mid_item_source_priority p
  ON p.source_biz_type = c.source_biz_type
 AND p.item_key = c.item_key
 AND p.gender = c.gender
 AND p.source_priority = c.source_priority
GROUP BY c.source_biz_type, c.item_key, c.gender;

-- 复制模板规则到目标标准。按 item_name + gender 判重，重复执行不会重复插入。
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
  CASE src_ids.item_key WHEN 'rope' THEN 'rope' ELSE 'jump' END,
  CASE src_ids.item_key WHEN 'rope' THEN '1分钟跳绳' ELSE '立定跳远' END,
  src.gender,
  src.calc_mode,
  src.pass_threshold,
  src.excellent_threshold,
  src.full_threshold,
  src.segment_json,
  1,
  0,
  src.max_score,
  CASE src_ids.item_key
    WHEN 'rope' THEN 30
    ELSE 40 + CASE src.gender WHEN 'female' THEN 1 ELSE 0 END
  END,
  NOW(),
  NOW(),
  0
FROM tmp_mid_standard_target ts
CROSS JOIN tmp_mid_item_source_ids src_ids
JOIN vadmin_pef_standard_item src ON src.id = src_ids.source_item_id
WHERE src_ids.source_biz_type = ts.biz_type
  AND NOT EXISTS (
  SELECT 1
  FROM vadmin_pef_standard_item exists_si
  WHERE exists_si.standard_id = ts.id
    AND exists_si.is_delete = 0
    AND exists_si.item_name = CASE src_ids.item_key WHEN 'rope' THEN '1分钟跳绳' ELSE '立定跳远' END
    AND exists_si.gender = src.gender
);

-- 兜底：如果库内没有可复用模板，也至少补齐项目，避免批次下拉/录入项目缺失。
--       后续可通过标准维护页面补充更精细的 segment_json。
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
  'rope',
  '1分钟跳绳',
  'all',
  'segment',
  110,
  155,
  185,
  JSON_ARRAY(
    JSON_OBJECT('range', '0~109', 'score', 0),
    JSON_OBJECT('range', '110~154', 'score', CASE WHEN ts.biz_type = 'pe' THEN 12 ELSE 60 END),
    JSON_OBJECT('range', '155~184', 'score', CASE WHEN ts.biz_type = 'pe' THEN 16 ELSE 80 END),
    JSON_OBJECT('range', '185~999', 'score', CASE WHEN ts.biz_type = 'pe' THEN 20 ELSE 100 END)
  ),
  1,
  0,
  CASE WHEN ts.biz_type = 'pe' THEN 20 ELSE 100 END,
  30,
  NOW(),
  NOW(),
  0
FROM tmp_mid_standard_target ts
WHERE NOT EXISTS (
  SELECT 1
  FROM vadmin_pef_standard_item si
  WHERE si.standard_id = ts.id
    AND si.is_delete = 0
    AND si.item_name = '1分钟跳绳'
);

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
  'jump',
  '立定跳远',
  gender_src.gender,
  'segment',
  CASE gender_src.gender WHEN 'female' THEN 1.460 ELSE 1.850 END,
  CASE gender_src.gender WHEN 'female' THEN 1.850 ELSE 2.250 END,
  CASE gender_src.gender WHEN 'female' THEN 2.030 ELSE 2.400 END,
  CASE gender_src.gender
    WHEN 'female' THEN JSON_ARRAY(
      JSON_OBJECT('range', '0~1.459', 'score', 0),
      JSON_OBJECT('range', '1.460~1.849', 'score', CASE WHEN ts.biz_type = 'pe' THEN 9 ELSE 60 END),
      JSON_OBJECT('range', '1.850~2.029', 'score', CASE WHEN ts.biz_type = 'pe' THEN 12 ELSE 80 END),
      JSON_OBJECT('range', '2.030~5.000', 'score', CASE WHEN ts.biz_type = 'pe' THEN 15 ELSE 100 END)
    )
    ELSE JSON_ARRAY(
      JSON_OBJECT('range', '0~1.849', 'score', 0),
      JSON_OBJECT('range', '1.850~2.249', 'score', CASE WHEN ts.biz_type = 'pe' THEN 9 ELSE 60 END),
      JSON_OBJECT('range', '2.250~2.399', 'score', CASE WHEN ts.biz_type = 'pe' THEN 12 ELSE 80 END),
      JSON_OBJECT('range', '2.400~5.000', 'score', CASE WHEN ts.biz_type = 'pe' THEN 15 ELSE 100 END)
    )
  END,
  1,
  0,
  CASE WHEN ts.biz_type = 'pe' THEN 15 ELSE 100 END,
  40 + CASE gender_src.gender WHEN 'female' THEN 1 ELSE 0 END,
  NOW(),
  NOW(),
  0
FROM tmp_mid_standard_target ts
CROSS JOIN (
  SELECT 'male' AS gender
  UNION ALL
  SELECT 'female' AS gender
) gender_src
WHERE NOT EXISTS (
  SELECT 1
  FROM vadmin_pef_standard_item si
  WHERE si.standard_id = ts.id
    AND si.is_delete = 0
    AND si.item_name = '立定跳远'
    AND si.gender IN (gender_src.gender, 'all')
);

-- 体测初中标准没有同学段跳绳模板时，不应复用小学“一年级~六年级”的评分段。
-- 这里将缺少“初一”规则的目标跳绳项改为初中兜底评分段，确保初中成绩可计算。
UPDATE vadmin_pef_standard_item si
JOIN tmp_mid_standard_target ts ON ts.id = si.standard_id
SET
  si.pass_threshold = 110,
  si.excellent_threshold = 155,
  si.full_threshold = 185,
  si.segment_json = JSON_ARRAY(
    JSON_OBJECT('range', '0~109', 'score', 0),
    JSON_OBJECT('range', '110~154', 'score', CASE WHEN ts.biz_type = 'pe' THEN 12 ELSE 60 END),
    JSON_OBJECT('range', '155~184', 'score', CASE WHEN ts.biz_type = 'pe' THEN 16 ELSE 80 END),
    JSON_OBJECT('range', '185~999', 'score', CASE WHEN ts.biz_type = 'pe' THEN 20 ELSE 100 END)
  ),
  si.max_score = CASE WHEN ts.biz_type = 'pe' THEN 20 ELSE 100 END,
  si.update_datetime = NOW()
WHERE ts.biz_type = 'fitness'
  AND si.is_delete = 0
  AND si.item_name = '1分钟跳绳'
  AND (
    si.segment_json IS NULL
    OR JSON_SEARCH(si.segment_json, 'one', '初一') IS NULL
  );

-- 校验目标标准当前启用项目。
SELECT
  s.name AS standard_name,
  s.biz_type,
  si.item_code,
  si.item_name,
  si.gender,
  si.max_score,
  si.sort,
  si.is_delete
FROM vadmin_pef_standard s
JOIN vadmin_pef_standard_item si ON si.standard_id = s.id
WHERE s.id IN (SELECT id FROM tmp_mid_standard_target)
  AND si.is_delete = 0
ORDER BY s.name, si.sort, si.id;
