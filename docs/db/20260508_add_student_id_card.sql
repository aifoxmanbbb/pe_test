-- 2026-05-08 学生档案新增必填字段：身份证号
SET NAMES utf8mb4;

SET @column_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'vadmin_pef_student'
    AND COLUMN_NAME = 'id_card'
);

SET @add_column_sql := IF(
  @column_exists = 0,
  'ALTER TABLE vadmin_pef_student ADD COLUMN id_card VARCHAR(32) NOT NULL DEFAULT '''' COMMENT ''身份证号'' AFTER gender',
  'SELECT ''vadmin_pef_student.id_card already exists'''
);
PREPARE add_column_stmt FROM @add_column_sql;
EXECUTE add_column_stmt;
DEALLOCATE PREPARE add_column_stmt;

SET @index_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'vadmin_pef_student'
    AND INDEX_NAME = 'idx_vadmin_pef_student_id_card'
);

SET @add_index_sql := IF(
  @index_exists = 0,
  'CREATE INDEX idx_vadmin_pef_student_id_card ON vadmin_pef_student(id_card)',
  'SELECT ''idx_vadmin_pef_student_id_card already exists'''
);
PREPARE add_index_stmt FROM @add_index_sql;
EXECUTE add_index_stmt;
DEALLOCATE PREPARE add_index_stmt;
