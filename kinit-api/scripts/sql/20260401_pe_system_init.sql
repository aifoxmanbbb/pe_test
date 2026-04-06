/*
  体考/体测系统初始化脚本（完整闭环版）
  生成日期：2026-04-04
  说明：
  1) 统一使用 vadmin_pef_ 前缀。
  2) 包含基础信息（年级/班级/学生）与核心业务（标准/批次/成绩）。
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =========================================================
-- 1. 基础信息管理
-- =========================================================

CREATE TABLE IF NOT EXISTS `vadmin_pef_grade` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `grade_name` varchar(50) NOT NULL COMMENT '年级名称',
  `grade_code` varchar(50) DEFAULT NULL COMMENT '年级编码',
  `sort` int NOT NULL DEFAULT 0 COMMENT '排序',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pef_grade_name` (`grade_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考体测-年级';

CREATE TABLE IF NOT EXISTS `vadmin_pef_class` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `grade_id` int NOT NULL COMMENT '年级ID',
  `class_name` varchar(50) NOT NULL COMMENT '班级名称',
  `class_code` varchar(50) DEFAULT NULL COMMENT '班级编码',
  `coach_user_id` int DEFAULT NULL COMMENT '主教练用户ID',
  `sort` int NOT NULL DEFAULT 0 COMMENT '排序',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pef_class_code` (`class_code`),
  CONSTRAINT `fk_pef_class_grade` FOREIGN KEY (`grade_id`) REFERENCES `vadmin_pef_grade` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考体测-班级';

CREATE TABLE IF NOT EXISTS `vadmin_pef_student` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `student_no` varchar(50) NOT NULL COMMENT '学号',
  `name` varchar(50) NOT NULL COMMENT '姓名',
  `gender` varchar(8) NOT NULL COMMENT '性别：male,female',
  `birthday` date DEFAULT NULL COMMENT '出生日期',
  `grade_id` int NOT NULL COMMENT '年级ID',
  `class_id` int NOT NULL COMMENT '班级ID',
  `user_id` int DEFAULT NULL COMMENT '关联用户ID',
  `phone` varchar(20) DEFAULT NULL COMMENT '联系电话',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pef_student_no` (`student_no`),
  CONSTRAINT `fk_pef_student_grade` FOREIGN KEY (`grade_id`) REFERENCES `vadmin_pef_grade` (`id`),
  CONSTRAINT `fk_pef_student_class` FOREIGN KEY (`class_id`) REFERENCES `vadmin_pef_class` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考体测-学生花名册';

-- =========================================================
-- 2. 标准管理
-- =========================================================

CREATE TABLE IF NOT EXISTS `vadmin_pef_standard` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `biz_type` varchar(16) NOT NULL COMMENT '业务类型：pe=体考,fitness=体测',
  `name` varchar(120) NOT NULL COMMENT '标准名称',
  `region` varchar(64) NOT NULL COMMENT '地区',
  `year` int NOT NULL COMMENT '年份',
  `stage_type` varchar(16) NOT NULL COMMENT '学段：mid=初中,high=高中',
  `version` varchar(32) NOT NULL COMMENT '标准版本号',
  `status` varchar(16) NOT NULL DEFAULT 'draft' COMMENT '状态：draft,published,void',
  `source_type` varchar(16) NOT NULL DEFAULT 'manual' COMMENT '来源：pdf,excel,manual,copy',
  `conflict_policy` varchar(32) NOT NULL DEFAULT 'lower_priority' COMMENT '规则冲突策略',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `idx_pef_standard_biz` (`biz_type`,`region`,`year`,`stage_type`,`status`),
  KEY `idx_pef_standard_version` (`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考/体测标准主表';

CREATE TABLE IF NOT EXISTS `vadmin_pef_standard_item` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `standard_id` int NOT NULL COMMENT '标准ID',
  `item_code` varchar(64) NOT NULL COMMENT '项目编码',
  `item_name` varchar(64) NOT NULL COMMENT '项目名称',
  `gender` varchar(8) NOT NULL DEFAULT 'all' COMMENT '性别：male,female,all',
  `calc_mode` varchar(16) NOT NULL DEFAULT 'segment' COMMENT '计分模式：segment,threshold',
  `pass_threshold` decimal(10,3) DEFAULT NULL COMMENT '及格阈值',
  `excellent_threshold` decimal(10,3) DEFAULT NULL COMMENT '优秀阈值',
  `full_threshold` decimal(10,3) DEFAULT NULL COMMENT '满分阈值',
  `segment_json` json DEFAULT NULL COMMENT '分值段JSON(成绩->分值)',
  `is_required` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否必测',
  `is_gate_item` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否门槛项',
  `max_score` decimal(10,3) NOT NULL DEFAULT 0.000 COMMENT '该项目满分',
  `sort` int NOT NULL DEFAULT 0 COMMENT '排序',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `idx_pef_standard_item_sid` (`standard_id`,`item_code`,`gender`),
  CONSTRAINT `fk_pef_standard_item_standard` FOREIGN KEY (`standard_id`) REFERENCES `vadmin_pef_standard` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考/体测标准项目明细';

-- =========================================================
-- 3. 核心业务（批次与成绩）
-- =========================================================

CREATE TABLE IF NOT EXISTS `vadmin_pef_batch` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `biz_type` varchar(16) NOT NULL COMMENT '业务类型：pe=体考,fitness=体测',
  `batch_name` varchar(120) NOT NULL COMMENT '批次名称',
  `standard_id` int NOT NULL COMMENT '引用标准ID',
  `school_name` varchar(120) NOT NULL COMMENT '学校',
  `grade_name` varchar(64) NOT NULL COMMENT '年级',
  `class_name` varchar(64) NOT NULL COMMENT '班级',
  `stage_type` varchar(16) NOT NULL COMMENT '学段：mid/high',
  `start_date` date DEFAULT NULL COMMENT '开始日期',
  `end_date` date DEFAULT NULL COMMENT '结束日期',
  `status` varchar(16) NOT NULL DEFAULT 'draft' COMMENT '状态：draft,ongoing,finished',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `idx_pef_batch_biz` (`biz_type`,`standard_id`,`school_name`,`grade_name`,`class_name`),
  CONSTRAINT `fk_pef_batch_standard` FOREIGN KEY (`standard_id`) REFERENCES `vadmin_pef_standard` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考/体测批次表';

CREATE TABLE IF NOT EXISTS `vadmin_pef_score` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `biz_type` varchar(16) NOT NULL COMMENT '业务类型：pe=体考,fitness=体测',
  `batch_id` int NOT NULL COMMENT '批次ID',
  `student_no` varchar(64) NOT NULL COMMENT '学号',
  `student_name` varchar(64) NOT NULL COMMENT '学生姓名',
  `gender` varchar(8) NOT NULL COMMENT '性别：male,female',
  `mobile` varchar(32) DEFAULT NULL COMMENT '联系方式',
  `school_name` varchar(120) NOT NULL COMMENT '学校',
  `grade_name` varchar(64) NOT NULL COMMENT '年级',
  `class_name` varchar(64) NOT NULL COMMENT '班级',
  `item_code` varchar(64) NOT NULL COMMENT '项目编码',
  `item_name` varchar(64) NOT NULL COMMENT '项目名称',
  `raw_score` decimal(10,3) DEFAULT NULL COMMENT '成绩',
  `score_value` decimal(10,3) DEFAULT NULL COMMENT '分值',
  `is_pass` tinyint(1) DEFAULT NULL COMMENT '是否及格',
  `is_excellent` tinyint(1) DEFAULT NULL COMMENT '是否优秀',
  `is_full` tinyint(1) DEFAULT NULL COMMENT '是否满分',
  `teacher_comment` varchar(255) DEFAULT NULL COMMENT '老师评语',
  `test_date` date DEFAULT NULL COMMENT '测试日期',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pef_score_row` (`batch_id`,`student_no`,`item_code`,`is_delete`),
  KEY `idx_pef_score_query` (`biz_type`,`batch_id`,`school_name`,`grade_name`,`class_name`,`student_name`),
  CONSTRAINT `fk_pef_score_batch` FOREIGN KEY (`batch_id`) REFERENCES `vadmin_pef_batch` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考/体测成绩明细表';

-- =========================================================
-- 4. 字典初始化
-- =========================================================

INSERT INTO `vadmin_system_dict_type` (`dict_name`, `dict_type`, `disabled`, `remark`, `is_delete`)
SELECT '体考/体测批次类型', 'pe_exam_batch_type', 0, '体考/体测系统批次类型字典', 0
WHERE NOT EXISTS (
  SELECT 1 FROM `vadmin_system_dict_type` WHERE `dict_type` = 'pe_exam_batch_type' AND `is_delete` = 0
);

SET @pe_dict_type_id = (
  SELECT id FROM `vadmin_system_dict_type` WHERE `dict_type` = 'pe_exam_batch_type' AND `is_delete` = 0 LIMIT 1
);

INSERT INTO `vadmin_system_dict_details`
(`label`, `value`, `disabled`, `is_default`, `order`, `dict_type_id`, `remark`, `is_delete`)
SELECT '摸底测试', 'baseline', 0, 1, 1, @pe_dict_type_id, NULL, 0
WHERE NOT EXISTS (
  SELECT 1 FROM `vadmin_system_dict_details` WHERE `dict_type_id` = @pe_dict_type_id AND `value` = 'baseline' AND `is_delete` = 0
);

INSERT INTO `vadmin_system_dict_details`
(`label`, `value`, `disabled`, `is_default`, `order`, `dict_type_id`, `remark`, `is_delete`)
SELECT '阶段测试', 'stage', 0, 0, 2, @pe_dict_type_id, NULL, 0
WHERE NOT EXISTS (
  SELECT 1 FROM `vadmin_system_dict_details` WHERE `dict_type_id` = @pe_dict_type_id AND `value` = 'stage' AND `is_delete` = 0
);

INSERT INTO `vadmin_system_dict_details`
(`label`, `value`, `disabled`, `is_default`, `order`, `dict_type_id`, `remark`, `is_delete`)
SELECT '模拟考试', 'mock', 0, 0, 3, @pe_dict_type_id, NULL, 0
WHERE NOT EXISTS (
  SELECT 1 FROM `vadmin_system_dict_details` WHERE `dict_type_id` = @pe_dict_type_id AND `value` = 'mock' AND `is_delete` = 0
);

INSERT INTO `vadmin_system_dict_details`
(`label`, `value`, `disabled`, `is_default`, `order`, `dict_type_id`, `remark`, `is_delete`)
SELECT '正式考试', 'formal', 0, 0, 4, @pe_dict_type_id, NULL, 0
WHERE NOT EXISTS (
  SELECT 1 FROM `vadmin_system_dict_details` WHERE `dict_type_id` = @pe_dict_type_id AND `value` = 'formal' AND `is_delete` = 0
);

SET FOREIGN_KEY_CHECKS = 1;
