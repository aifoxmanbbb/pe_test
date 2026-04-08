-- 2026-04-08 学校学段字段升级
-- 目标：学校管理支持小学/初中/高中/大学多学段，便于后续按学段筛选

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE `vadmin_pef_school`
  ADD COLUMN `stage_types` varchar(64) DEFAULT 'mid,high' COMMENT '学段集合：primary,mid,high,university' AFTER `region`;

-- 兼容历史数据：将已有学校默认放开为全学段，避免筛选后无数据
UPDATE `vadmin_pef_school`
SET `stage_types` = 'primary,mid,high,university'
WHERE `stage_types` IS NULL OR `stage_types` = '';

SET FOREIGN_KEY_CHECKS = 1;
