/*
  体考/体测系统初始化脚本（V7 - 学校模块增强版）
  生成日期：2026-04-06
  说明：
  1) 引入 vadmin_pef_school 学校管理表。
  2) 完善“体育基础档案”菜单层级：学校 -> 年级 -> 班级 -> 学生。
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =========================================================
-- 1. 基础信息管理表
-- =========================================================

CREATE TABLE IF NOT EXISTS `vadmin_pef_school` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `school_name` varchar(120) NOT NULL UNIQUE COMMENT '学校名称',
  `school_code` varchar(50) COMMENT '代码',
  `region` varchar(100) COMMENT '地区',
  `stage_types` varchar(64) DEFAULT 'mid,high' COMMENT '学段集合：primary,mid,high,university',
  `sort` int NOT NULL DEFAULT 0,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_delete` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考体测-学校';

CREATE TABLE IF NOT EXISTS `vadmin_pef_grade` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `grade_name` varchar(50) NOT NULL UNIQUE,
  `grade_code` varchar(50),
  `sort` int NOT NULL DEFAULT 0,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `remark` varchar(255),
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_delete` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考体测-年级';

CREATE TABLE IF NOT EXISTS `vadmin_pef_class` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `grade_id` int NOT NULL,
  `class_name` varchar(50) NOT NULL,
  `class_code` varchar(50) UNIQUE,
  `coach_user_id` int,
  `sort` int NOT NULL DEFAULT 0,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_delete` tinyint(1) NOT NULL DEFAULT 0,
  CONSTRAINT `fk_pef_class_grade` FOREIGN KEY (`grade_id`) REFERENCES `vadmin_pef_grade` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考体测-班级';

CREATE TABLE IF NOT EXISTS `vadmin_pef_student` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `student_no` varchar(50) NOT NULL UNIQUE,
  `name` varchar(50) NOT NULL,
  `gender` varchar(8) NOT NULL,
  `birthday` date DEFAULT NULL,
  `grade_id` int NOT NULL,
  `class_id` int NOT NULL,
  `user_id` int,
  `phone` varchar(20),
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `remark` varchar(255),
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_delete` tinyint(1) NOT NULL DEFAULT 0,
  CONSTRAINT `fk_pef_student_grade` FOREIGN KEY (`grade_id`) REFERENCES `vadmin_pef_grade` (`id`),
  CONSTRAINT `fk_pef_student_class` FOREIGN KEY (`class_id`) REFERENCES `vadmin_pef_class` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考体测-学生花名册';

-- =========================================================
-- 2. 业务管理表 (标准/批次/成绩 - 保持不变)
-- =========================================================

CREATE TABLE IF NOT EXISTS `vadmin_pef_standard` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `biz_type` varchar(16) NOT NULL,
  `name` varchar(120) NOT NULL,
  `region` varchar(64) NOT NULL,
  `year` int NOT NULL,
  `stage_type` varchar(16) NOT NULL,
  `version` varchar(32) NOT NULL,
  `status` varchar(16) NOT NULL DEFAULT 'draft',
  `source_type` varchar(16) DEFAULT 'manual',
  `conflict_policy` varchar(32) DEFAULT 'lower_priority',
  `remark` varchar(255),
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_delete` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考/体测标准主表';

CREATE TABLE IF NOT EXISTS `vadmin_pef_standard_item` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `standard_id` int NOT NULL,
  `item_code` varchar(64) NOT NULL,
  `item_name` varchar(64) NOT NULL,
  `gender` varchar(8) NOT NULL DEFAULT 'all',
  `calc_mode` varchar(16) NOT NULL DEFAULT 'segment',
  `pass_threshold` decimal(10,3),
  `excellent_threshold` decimal(10,3),
  `full_threshold` decimal(10,3),
  `segment_json` json,
  `is_required` tinyint(1) NOT NULL DEFAULT 1,
  `is_gate_item` tinyint(1) NOT NULL DEFAULT 0,
  `max_score` decimal(10,3) DEFAULT 0.000,
  `sort` int NOT NULL DEFAULT 0,
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_delete` tinyint(1) NOT NULL DEFAULT 0,
  CONSTRAINT `fk_pef_standard_item_standard` FOREIGN KEY (`standard_id`) REFERENCES `vadmin_pef_standard` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考/体测标准项目明细';

CREATE TABLE IF NOT EXISTS `vadmin_pef_batch` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `biz_type` varchar(16) NOT NULL,
  `batch_name` varchar(120) NOT NULL,
  `standard_id` int NOT NULL,
  `school_name` varchar(120) NOT NULL,
  `grade_name` varchar(64) NOT NULL,
  `class_name` varchar(64) NOT NULL,
  `stage_type` varchar(16),
  `start_date` date,
  `end_date` date,
  `status` varchar(16) NOT NULL DEFAULT 'draft',
  `remark` varchar(255),
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_delete` tinyint(1) NOT NULL DEFAULT 0,
  CONSTRAINT `fk_pef_batch_standard` FOREIGN KEY (`standard_id`) REFERENCES `vadmin_pef_standard` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考/体测批次表';

CREATE TABLE IF NOT EXISTS `vadmin_pef_score` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `biz_type` varchar(16) NOT NULL,
  `batch_id` int NOT NULL,
  `student_no` varchar(64) NOT NULL,
  `student_name` varchar(64) NOT NULL,
  `gender` varchar(8) NOT NULL,
  `mobile` varchar(32),
  `school_name` varchar(120) NOT NULL,
  `grade_name` varchar(64) NOT NULL,
  `class_name` varchar(64) NOT NULL,
  `item_code` varchar(64) NOT NULL,
  `item_name` varchar(64) NOT NULL,
  `raw_score` decimal(10,3),
  `score_value` decimal(10,3),
  `is_pass` tinyint(1),
  `is_excellent` tinyint(1),
  `is_full` tinyint(1),
  `teacher_comment` varchar(255),
  `test_date` date,
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_delete` tinyint(1) NOT NULL DEFAULT 0,
  CONSTRAINT `fk_pef_score_batch` FOREIGN KEY (`batch_id`) REFERENCES `vadmin_pef_batch` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考/体测成绩明细表';

-- =========================================================
-- 3. 菜单与权限初始化 (纠正层级与补全学校管理)
-- =========================================================

SET @now = NOW();

-- 清理旧菜单数据
DELETE FROM `vadmin_auth_role_menus` WHERE `menu_id` IN (SELECT id FROM `vadmin_auth_menu` WHERE `perms` LIKE 'pe%' OR `perms` LIKE 'fitness%' OR `perms` LIKE 'sport%');
DELETE FROM `vadmin_auth_menu` WHERE `perms` LIKE 'pe%' OR `perms` LIKE 'fitness%' OR `perms` LIKE 'sport%';

-- 3.1 体考管理 (PE)
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
VALUES ('体考管理', 'ant-design:dashboard-outlined', '/pe/overview', '#', '/pe', 0, 0, 10, '0', NULL, 'pe', 0, 1, 0, 0, 0, 1, @now, @now, 0);
SET @pe_root = LAST_INSERT_ID();

INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
VALUES 
('成绩总览', NULL, NULL, 'views/Vadmin/PE/Overview/Overview', 'overview', 0, 0, 1, '1', @pe_root, 'pe.analysis.overview', 0, 1, 0, 0, 0, 0, @now, @now, 0),
('成绩录入', NULL, NULL, 'views/Vadmin/PE/Entry/Entry', 'entry', 0, 0, 2, '1', @pe_root, 'pe.score.entry', 0, 1, 0, 0, 0, 0, @now, @now, 0);

-- 统计分析目录
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
VALUES ('统计分析', NULL, NULL, '#', 'analysis', 0, 0, 3, '0', @pe_root, 'pe.analysis', 0, 1, 0, 0, 0, 1, @now, @now, 0);
SET @pe_analysis = LAST_INSERT_ID();

INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
VALUES 
('学生阶段对比', NULL, NULL, 'views/Vadmin/PE/Analysis/Student/Student', 'student', 0, 0, 1, '1', @pe_analysis, 'pe.analysis.student', 0, 1, 0, 0, 0, 0, @now, @now, 0),
('班级对比分析', NULL, NULL, 'views/Vadmin/PE/Analysis/Class/Class', 'class', 0, 0, 2, '1', @pe_analysis, 'pe.analysis.class', 0, 1, 0, 0, 0, 0, @now, @now, 0),
('年级对比分析', NULL, NULL, 'views/Vadmin/PE/Analysis/Grade/Grade', 'grade', 0, 0, 3, '1', @pe_analysis, 'pe.analysis.grade', 0, 1, 0, 0, 0, 0, @now, @now, 0),
('报表中心', NULL, NULL, 'views/Vadmin/PE/Report/Report', 'report', 0, 0, 4, '1', @pe_root, 'pe.report', 0, 1, 0, 0, 0, 0, @now, @now, 0),
('评分标准', NULL, NULL, 'views/Vadmin/PE/Standard/Standard', 'standard', 0, 0, 5, '1', @pe_root, 'pe.standard', 0, 1, 0, 0, 0, 0, @now, @now, 0),
('批次管理', NULL, NULL, 'views/Vadmin/PE/Batch/Batch', 'batch', 0, 0, 6, '1', @pe_root, 'pe.batch', 0, 1, 0, 0, 0, 0, @now, @now, 0);

-- 3.2 体测管理 (Fitness)
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
VALUES ('体测管理', 'ant-design:line-chart-outlined', '/fitness/overview', '#', '/fitness', 0, 0, 11, '0', NULL, 'fitness', 0, 1, 0, 0, 0, 1, @now, @now, 0);
SET @fit_root = LAST_INSERT_ID();

INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
VALUES 
('体测总览', NULL, NULL, 'views/Vadmin/Fitness/Overview/Overview', 'overview', 0, 0, 1, '1', @fit_root, 'fitness.analysis.overview', 0, 1, 0, 0, 0, 0, @now, @now, 0),
('体测录入', NULL, NULL, 'views/Vadmin/Fitness/Entry/Entry', 'entry', 0, 0, 2, '1', @fit_root, 'fitness.score.entry', 0, 1, 0, 0, 0, 0, @now, @now, 0);

-- 统计分析目录
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
VALUES ('统计分析', NULL, NULL, '#', 'analysis', 0, 0, 3, '0', @fit_root, 'fitness.analysis', 0, 1, 0, 0, 0, 1, @now, @now, 0);
SET @fit_analysis = LAST_INSERT_ID();

INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
VALUES 
('学生体测分析', NULL, NULL, 'views/Vadmin/Fitness/Analysis/Student/Student', 'student', 0, 0, 1, '1', @fit_analysis, 'fitness.analysis.student', 0, 1, 0, 0, 0, 0, @now, @now, 0),
('班级体测分析', NULL, NULL, 'views/Vadmin/Fitness/Analysis/Class/Class', 'class', 0, 0, 2, '1', @fit_analysis, 'fitness.analysis.class', 0, 1, 0, 0, 0, 0, @now, @now, 0),
('年级体测分析', NULL, NULL, 'views/Vadmin/Fitness/Analysis/Grade/Grade', 'grade', 0, 0, 3, '1', @fit_analysis, 'fitness.analysis.grade', 0, 1, 0, 0, 0, 0, @now, @now, 0),
('体测报表中心', NULL, NULL, 'views/Vadmin/Fitness/Report/Report', 'report', 0, 0, 4, '1', @fit_root, 'fitness.report.export', 0, 1, 0, 0, 0, 0, @now, @now, 0),
('体测标准', NULL, NULL, 'views/Vadmin/Fitness/Standard/Standard', 'standard', 0, 0, 5, '1', @fit_root, 'fitness.standard.list', 0, 1, 0, 0, 0, 0, @now, @now, 0),
('批次管理', NULL, NULL, 'views/Vadmin/Fitness/Batch/Batch', 'batch', 0, 0, 6, '1', @fit_root, 'fitness.batch', 0, 1, 0, 0, 0, 0, @now, @now, 0);

-- 3.3 学生个人中心
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
VALUES ('我的体育', 'ant-design:user-outlined', '/sport/my-scores', '#', '/sport', 0, 0, 12, '0', NULL, 'sport.student', 0, 1, 0, 0, 0, 1, @now, @now, 0);
SET @sport_root = LAST_INSERT_ID();

INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
VALUES ('我的成绩', NULL, NULL, 'views/Vadmin/Sport/Student/MyScores', 'my-scores', 0, 0, 1, '1', @sport_root, 'sport.student.scores', 0, 1, 0, 0, 0, 0, @now, @now, 0);

-- 3.4 体育基础档案 ( PEF Foundation )
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
VALUES ('体育基础档案', 'ant-design:database-outlined', '/sport/foundation/school', '#', '/sport/foundation', 0, 0, 13, '0', NULL, 'sport.foundation', 0, 1, 0, 0, 0, 1, @now, @now, 0);
SET @found_root = LAST_INSERT_ID();

INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
VALUES 
('学校管理', NULL, NULL, 'views/Vadmin/Sport/School/School', 'school', 0, 0, 1, '1', @found_root, 'sport.foundation.school', 0, 1, 0, 0, 0, 0, @now, @now, 0),
('年级管理', NULL, NULL, 'views/Vadmin/Sport/Grade/Grade', 'grade', 0, 0, 2, '1', @found_root, 'sport.foundation.grade', 0, 1, 0, 0, 0, 0, @now, @now, 0),
('班级管理', NULL, NULL, 'views/Vadmin/Sport/Class/Class', 'class', 0, 0, 3, '1', @found_root, 'sport.foundation.class', 0, 1, 0, 0, 0, 0, @now, @now, 0),
('学生管理', NULL, NULL, 'views/Vadmin/Sport/Student/Student', 'student', 0, 0, 4, '1', @found_root, 'sport.foundation.student', 0, 1, 0, 0, 0, 0, @now, @now, 0);

-- 3.5 权限分配
SET @admin_role_id = (SELECT id FROM `vadmin_auth_role` WHERE `role_key` = 'admin' LIMIT 1);
INSERT INTO `vadmin_auth_role_menus` (`role_id`, `menu_id`)
SELECT @admin_role_id, id FROM `vadmin_auth_menu`
WHERE `perms` LIKE 'pe%' OR `perms` LIKE 'fitness%' OR `perms` LIKE 'sport%';

SET FOREIGN_KEY_CHECKS = 1;
