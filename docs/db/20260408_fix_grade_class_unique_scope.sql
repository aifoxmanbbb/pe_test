/*
  2026-04-08
  修复 年级/班级 唯一约束范围：
  1) 年级名称不再全局唯一，改为同学校内唯一（含软删位）
  2) 班级名称不再误设为全局唯一，改为同学校+同年级内唯一（含软删位）
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

SET @db = DATABASE();

-- 1) vadmin_pef_grade: 删除旧的全局唯一索引（可能名称不同）
SET @idx_to_drop = (
  SELECT index_name
  FROM information_schema.statistics
  WHERE table_schema = @db
    AND table_name = 'vadmin_pef_grade'
    AND non_unique = 0
    AND index_name <> 'PRIMARY'
    AND (
      index_name IN ('uk_pef_grade_name', 'grade_name')
      OR (
        seq_in_index = 1
        AND column_name = 'grade_name'
      )
    )
  LIMIT 1
);
SET @sql = IF(@idx_to_drop IS NULL, 'SELECT 1', CONCAT('ALTER TABLE `vadmin_pef_grade` DROP INDEX `', @idx_to_drop, '`'));
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2) vadmin_pef_grade: 新增同校唯一索引（含软删位）
SET @grade_new_idx_exists = (
  SELECT COUNT(1)
  FROM information_schema.statistics
  WHERE table_schema = @db
    AND table_name = 'vadmin_pef_grade'
    AND index_name = 'uk_pef_grade_school_name'
);
SET @sql = IF(
  @grade_new_idx_exists > 0,
  'SELECT 1',
  'ALTER TABLE `vadmin_pef_grade` ADD UNIQUE INDEX `uk_pef_grade_school_name` (`school_id`, `grade_name`, `is_delete`)'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 3) vadmin_pef_class: 删除可能存在的 class_name 全局唯一索引
SET @cls_idx_to_drop = (
  SELECT index_name
  FROM information_schema.statistics
  WHERE table_schema = @db
    AND table_name = 'vadmin_pef_class'
    AND non_unique = 0
    AND index_name <> 'PRIMARY'
    AND (
      index_name IN ('uk_pef_class_name', 'class_name')
      OR (
        seq_in_index = 1
        AND column_name = 'class_name'
      )
    )
  LIMIT 1
);
SET @sql = IF(@cls_idx_to_drop IS NULL, 'SELECT 1', CONCAT('ALTER TABLE `vadmin_pef_class` DROP INDEX `', @cls_idx_to_drop, '`'));
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 4) vadmin_pef_class: 新增同校同年级唯一索引（含软删位）
SET @class_new_idx_exists = (
  SELECT COUNT(1)
  FROM information_schema.statistics
  WHERE table_schema = @db
    AND table_name = 'vadmin_pef_class'
    AND index_name = 'uk_pef_class_scope_name'
);
SET @sql = IF(
  @class_new_idx_exists > 0,
  'SELECT 1',
  'ALTER TABLE `vadmin_pef_class` ADD UNIQUE INDEX `uk_pef_class_scope_name` (`school_id`, `grade_id`, `class_name`, `is_delete`)'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET FOREIGN_KEY_CHECKS = 1;

