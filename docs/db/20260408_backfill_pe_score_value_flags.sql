/*
  文件: 20260408_backfill_pe_score_value_flags.sql
  目的: 回填 vadmin_pef_score（体考）中的 score_value / is_pass / is_excellent / is_full
  特点:
  1) 不使用 JSON_TABLE，规避 1210 - Incorrect arguments to JSON_TABLE
  2) 先按阈值兜底，再用合法的 segment_json 覆盖 score_value
  3) 仅处理 biz_type='pe' 且 raw_score 非空的数据

  适用: MySQL 8.0+
*/

SET NAMES utf8mb4;
SET @old_sql_safe_updates = @@SQL_SAFE_UPDATES;
SET SQL_SAFE_UPDATES = 0;

START TRANSACTION;

/* -------------------------------------------------------
   Step 1: 阈值兜底计算（状态位 + 分值兜底）
   - 若阈值是“越低越好”（如跑步秒数），依据 pass_threshold > full_threshold 判断
   - segment 项先按阈值给兜底分，后续再用 segment_json 精确覆盖
-------------------------------------------------------- */
UPDATE vadmin_pef_score s
JOIN vadmin_pef_batch b
  ON b.id = s.batch_id
 AND b.is_delete = 0
JOIN vadmin_pef_standard_item si
  ON si.standard_id = b.standard_id
 AND si.item_code = s.item_code
 AND si.is_delete = 0
 AND (si.gender = 'all' OR si.gender = s.gender)
SET
  s.is_pass = CASE
    WHEN s.raw_score IS NULL OR si.pass_threshold IS NULL THEN s.is_pass
    WHEN si.pass_threshold > COALESCE(si.full_threshold, si.pass_threshold) THEN IF(s.raw_score <= si.pass_threshold, 1, 0)
    ELSE IF(s.raw_score >= si.pass_threshold, 1, 0)
  END,
  s.is_excellent = CASE
    WHEN s.raw_score IS NULL OR si.excellent_threshold IS NULL THEN s.is_excellent
    WHEN si.pass_threshold > COALESCE(si.full_threshold, si.pass_threshold) THEN IF(s.raw_score <= si.excellent_threshold, 1, 0)
    ELSE IF(s.raw_score >= si.excellent_threshold, 1, 0)
  END,
  s.is_full = CASE
    WHEN s.raw_score IS NULL OR si.full_threshold IS NULL THEN s.is_full
    WHEN si.pass_threshold > COALESCE(si.full_threshold, si.pass_threshold) THEN IF(s.raw_score <= si.full_threshold, 1, 0)
    ELSE IF(s.raw_score >= si.full_threshold, 1, 0)
  END,
  s.score_value = CASE
    WHEN s.raw_score IS NULL THEN s.score_value
    WHEN si.is_gate_item = 1 THEN 0
    WHEN si.calc_mode = 'threshold' THEN
      CASE
        WHEN si.pass_threshold > COALESCE(si.full_threshold, si.pass_threshold) THEN
          CASE
            WHEN si.full_threshold IS NOT NULL AND s.raw_score <= si.full_threshold THEN COALESCE(si.max_score, 100)
            WHEN si.excellent_threshold IS NOT NULL AND s.raw_score <= si.excellent_threshold THEN ROUND(COALESCE(si.max_score, 100) * 0.85, 3)
            WHEN si.pass_threshold IS NOT NULL AND s.raw_score <= si.pass_threshold THEN ROUND(COALESCE(si.max_score, 100) * 0.60, 3)
            ELSE 0
          END
        ELSE
          CASE
            WHEN si.full_threshold IS NOT NULL AND s.raw_score >= si.full_threshold THEN COALESCE(si.max_score, 100)
            WHEN si.excellent_threshold IS NOT NULL AND s.raw_score >= si.excellent_threshold THEN ROUND(COALESCE(si.max_score, 100) * 0.85, 3)
            WHEN si.pass_threshold IS NOT NULL AND s.raw_score >= si.pass_threshold THEN ROUND(COALESCE(si.max_score, 100) * 0.60, 3)
            ELSE 0
          END
      END
    WHEN si.calc_mode = 'segment' THEN
      CASE
        WHEN si.pass_threshold IS NULL THEN COALESCE(s.score_value, 0)
        WHEN si.pass_threshold > COALESCE(si.full_threshold, si.pass_threshold) THEN
          CASE
            WHEN si.full_threshold IS NOT NULL AND s.raw_score <= si.full_threshold THEN COALESCE(si.max_score, 100)
            WHEN si.excellent_threshold IS NOT NULL AND s.raw_score <= si.excellent_threshold THEN ROUND(COALESCE(si.max_score, 100) * 0.85, 3)
            WHEN s.raw_score <= si.pass_threshold THEN ROUND(COALESCE(si.max_score, 100) * 0.60, 3)
            ELSE 0
          END
        ELSE
          CASE
            WHEN si.full_threshold IS NOT NULL AND s.raw_score >= si.full_threshold THEN COALESCE(si.max_score, 100)
            WHEN si.excellent_threshold IS NOT NULL AND s.raw_score >= si.excellent_threshold THEN ROUND(COALESCE(si.max_score, 100) * 0.85, 3)
            WHEN s.raw_score >= si.pass_threshold THEN ROUND(COALESCE(si.max_score, 100) * 0.60, 3)
            ELSE 0
          END
      END
    ELSE s.score_value
  END
WHERE s.is_delete = 0
  AND s.biz_type = 'pe'
  AND s.raw_score IS NOT NULL
  AND (
      s.score_value IS NULL
   OR s.is_pass IS NULL
   OR s.is_excellent IS NULL
   OR s.is_full IS NULL
  );

/* -------------------------------------------------------
   Step 2: 对合法 segment_json 做精确覆盖（仅顶层 [{range,score}, ...] 结构）
   - 不合法 JSON / 非数组 / 非该结构将被自动跳过
-------------------------------------------------------- */
DROP TEMPORARY TABLE IF EXISTS tmp_pe_segment_match;
CREATE TEMPORARY TABLE tmp_pe_segment_match (
  score_id BIGINT NOT NULL,
  seg_score DECIMAL(10,3) NOT NULL,
  PRIMARY KEY (score_id)
);

INSERT INTO tmp_pe_segment_match (score_id, seg_score)
WITH RECURSIVE seq AS (
  SELECT 0 AS idx
  UNION ALL
  SELECT idx + 1 FROM seq WHERE idx < 300
),
segment_rows AS (
  SELECT
    s.id AS score_id,
    CAST(JSON_UNQUOTE(JSON_EXTRACT(JSON_EXTRACT(si.segment_json, CONCAT('$[', seq.idx, ']')), '$.score')) AS DECIMAL(10,3)) AS seg_score,
    TRIM(JSON_UNQUOTE(JSON_EXTRACT(JSON_EXTRACT(si.segment_json, CONCAT('$[', seq.idx, ']')), '$.range'))) AS seg_range,
    s.raw_score
  FROM vadmin_pef_score s
  JOIN vadmin_pef_batch b
    ON b.id = s.batch_id
   AND b.is_delete = 0
  JOIN vadmin_pef_standard_item si
    ON si.standard_id = b.standard_id
   AND si.item_code = s.item_code
   AND si.is_delete = 0
   AND (si.gender = 'all' OR si.gender = s.gender)
  JOIN seq
    ON seq.idx < JSON_LENGTH(si.segment_json)
  WHERE s.is_delete = 0
    AND s.biz_type = 'pe'
    AND s.raw_score IS NOT NULL
    AND si.calc_mode = 'segment'
    AND si.segment_json IS NOT NULL
    AND JSON_VALID(si.segment_json)
    AND JSON_TYPE(si.segment_json) = 'ARRAY'
    AND JSON_TYPE(JSON_EXTRACT(si.segment_json, CONCAT('$[', seq.idx, ']'))) = 'OBJECT'
    AND JSON_EXTRACT(JSON_EXTRACT(si.segment_json, CONCAT('$[', seq.idx, ']')), '$.score') IS NOT NULL
    AND JSON_EXTRACT(JSON_EXTRACT(si.segment_json, CONCAT('$[', seq.idx, ']')), '$.range') IS NOT NULL
),
segment_parsed AS (
  SELECT
    score_id,
    seg_score,
    raw_score,
    CAST(TRIM(SUBSTRING_INDEX(seg_range, '~', 1)) AS DECIMAL(10,3)) AS min_v,
    CAST(TRIM(SUBSTRING_INDEX(seg_range, '~', -1)) AS DECIMAL(10,3)) AS max_v
  FROM segment_rows
  WHERE seg_range REGEXP '^-?[0-9]+(\\.[0-9]+)?[[:space:]]*~[[:space:]]*-?[0-9]+(\\.[0-9]+)?$'
),
segment_hit AS (
  SELECT
    score_id,
    MAX(seg_score) AS seg_score
  FROM segment_parsed
  WHERE raw_score >= LEAST(min_v, max_v)
    AND raw_score <= GREATEST(min_v, max_v)
  GROUP BY score_id
)
SELECT score_id, seg_score
FROM segment_hit;

UPDATE vadmin_pef_score s
JOIN tmp_pe_segment_match t
  ON t.score_id = s.id
SET s.score_value = t.seg_score
WHERE s.is_delete = 0
  AND s.biz_type = 'pe';

DROP TEMPORARY TABLE IF EXISTS tmp_pe_segment_match;

COMMIT;

SET SQL_SAFE_UPDATES = @old_sql_safe_updates;

/* 可选校验 */
SELECT
  COUNT(*) AS total_rows,
  SUM(CASE WHEN score_value IS NULL THEN 1 ELSE 0 END) AS null_score_value,
  SUM(CASE WHEN is_pass IS NULL THEN 1 ELSE 0 END) AS null_is_pass,
  SUM(CASE WHEN is_excellent IS NULL THEN 1 ELSE 0 END) AS null_is_excellent,
  SUM(CASE WHEN is_full IS NULL THEN 1 ELSE 0 END) AS null_is_full
FROM vadmin_pef_score
WHERE is_delete = 0
  AND biz_type = 'pe'
  AND raw_score IS NOT NULL;
