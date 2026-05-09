-- 2026-05-09 Student identity login migration.
-- Goal:
-- 1) student id_card is the unique student identity;
-- 2) student phone is optional, but should stay unique when filled;
-- 3) student_no remains an internal compatibility field for existing score relations.

SET NAMES utf8mb4;

ALTER TABLE vadmin_pef_student
  MODIFY COLUMN phone varchar(20) NULL COMMENT '联系电话';

UPDATE vadmin_pef_student
SET phone = NULL
WHERE phone = '';

-- Preflight duplicate checks before adding unique indexes.
SELECT id_card, COUNT(*) AS duplicate_count
FROM vadmin_pef_student
WHERE id_card IS NOT NULL
GROUP BY id_card
HAVING COUNT(*) > 1;

SELECT phone, COUNT(*) AS duplicate_count
FROM vadmin_pef_student
WHERE phone IS NOT NULL
  AND phone <> ''
GROUP BY phone
HAVING COUNT(*) > 1;

SET @dup_id_card_count := (
  SELECT COUNT(*)
  FROM (
    SELECT id_card
    FROM vadmin_pef_student
    WHERE id_card IS NOT NULL
    GROUP BY id_card
    HAVING COUNT(*) > 1
  ) t
);

SET @dup_phone_count := (
  SELECT COUNT(*)
  FROM (
    SELECT phone
    FROM vadmin_pef_student
    WHERE phone IS NOT NULL
      AND phone <> ''
    GROUP BY phone
    HAVING COUNT(*) > 1
  ) t
);

SET @has_unique_id_card := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'vadmin_pef_student'
    AND INDEX_NAME = 'uk_vadmin_pef_student_id_card'
);

SET @sql := IF(
  @dup_id_card_count = 0 AND @has_unique_id_card = 0,
  'CREATE UNIQUE INDEX uk_vadmin_pef_student_id_card ON vadmin_pef_student(id_card)',
  'SELECT ''skip uk_vadmin_pef_student_id_card: duplicate data exists or index already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @has_unique_phone := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'vadmin_pef_student'
    AND INDEX_NAME = 'uk_vadmin_pef_student_phone'
);

SET @sql := IF(
  @dup_phone_count = 0 AND @has_unique_phone = 0,
  'CREATE UNIQUE INDEX uk_vadmin_pef_student_phone ON vadmin_pef_student(phone)',
  'SELECT ''skip uk_vadmin_pef_student_phone: duplicate data exists or index already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
