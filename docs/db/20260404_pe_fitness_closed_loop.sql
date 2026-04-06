-- 2026-04-04 体考/体测闭环业务表
-- 用途：标准管理 -> 批次管理 -> 成绩录入 -> 统计分析

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `vadmin_pef_standard` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `biz_type` varchar(16) NOT NULL COMMENT '业务类型：pe=体考,fitness=体测',
  `name` varchar(120) NOT NULL COMMENT '标准名称',
  `region` varchar(64) NOT NULL COMMENT '地区',
  `year` int NOT NULL COMMENT '年份',
  `stage_type` varchar(16) NOT NULL COMMENT '学段：mid=初中,high=高中',
  `version` varchar(32) NOT NULL COMMENT '标准版本号',
  `status` varchar(16) NOT NULL DEFAULT 'draft' COMMENT '状态：draft,published,void',
  `source_type` varchar(16) NOT NULL DEFAULT 'manual' COMMENT '来源：pdf,excel,manual,copy',
  `conflict_policy` varchar(32) NOT NULL DEFAULT 'lower_priority' COMMENT '规则冲突策略',
  `remark` varchar(255) NULL COMMENT '备注',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `idx_pef_standard_biz` (`biz_type`,`region`,`year`,`stage_type`,`status`),
  KEY `idx_pef_standard_version` (`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考/体测标准主表';

CREATE TABLE IF NOT EXISTS `vadmin_pef_standard_item` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `standard_id` bigint NOT NULL COMMENT '标准ID',
  `item_code` varchar(64) NOT NULL COMMENT '项目编码',
  `item_name` varchar(64) NOT NULL COMMENT '项目名称',
  `gender` varchar(8) NOT NULL DEFAULT 'all' COMMENT '性别：male,female,all',
  `calc_mode` varchar(16) NOT NULL DEFAULT 'segment' COMMENT '计分模式：segment,threshold',
  `pass_threshold` decimal(10,3) NULL COMMENT '及格阈值',
  `excellent_threshold` decimal(10,3) NULL COMMENT '优秀阈值',
  `full_threshold` decimal(10,3) NULL COMMENT '满分阈值',
  `segment_json` json NULL COMMENT '分值段JSON(成绩->分值)',
  `is_required` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否必测',
  `is_gate_item` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否门槛项',
  `max_score` decimal(10,3) NOT NULL DEFAULT 0 COMMENT '该项目满分',
  `sort` int NOT NULL DEFAULT 0 COMMENT '排序',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `idx_pef_standard_item_sid` (`standard_id`,`item_code`,`gender`),
  CONSTRAINT `fk_pef_standard_item_standard` FOREIGN KEY (`standard_id`) REFERENCES `vadmin_pef_standard` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考/体测标准项目明细';

CREATE TABLE IF NOT EXISTS `vadmin_pef_batch` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `biz_type` varchar(16) NOT NULL COMMENT '业务类型：pe=体考,fitness=体测',
  `batch_name` varchar(120) NOT NULL COMMENT '批次名称',
  `standard_id` bigint NOT NULL COMMENT '引用标准ID',
  `school_name` varchar(120) NOT NULL COMMENT '学校',
  `grade_name` varchar(64) NOT NULL COMMENT '年级',
  `class_name` varchar(64) NOT NULL COMMENT '班级',
  `stage_type` varchar(16) NOT NULL COMMENT '学段：mid/high',
  `start_date` date NULL COMMENT '开始日期',
  `end_date` date NULL COMMENT '结束日期',
  `status` varchar(16) NOT NULL DEFAULT 'draft' COMMENT '状态：draft,ongoing,finished',
  `remark` varchar(255) NULL COMMENT '备注',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `idx_pef_batch_biz` (`biz_type`,`standard_id`,`school_name`,`grade_name`,`class_name`),
  CONSTRAINT `fk_pef_batch_standard` FOREIGN KEY (`standard_id`) REFERENCES `vadmin_pef_standard` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考/体测批次表';

CREATE TABLE IF NOT EXISTS `vadmin_pef_score` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `biz_type` varchar(16) NOT NULL COMMENT '业务类型：pe=体考,fitness=体测',
  `batch_id` bigint NOT NULL COMMENT '批次ID',
  `student_no` varchar(64) NOT NULL COMMENT '学号',
  `student_name` varchar(64) NOT NULL COMMENT '学生姓名',
  `gender` varchar(8) NOT NULL COMMENT '性别：male,female',
  `mobile` varchar(32) NULL COMMENT '联系方式',
  `school_name` varchar(120) NOT NULL COMMENT '学校',
  `grade_name` varchar(64) NOT NULL COMMENT '年级',
  `class_name` varchar(64) NOT NULL COMMENT '班级',
  `item_code` varchar(64) NOT NULL COMMENT '项目编码',
  `item_name` varchar(64) NOT NULL COMMENT '项目名称',
  `raw_score` decimal(10,3) NULL COMMENT '成绩',
  `score_value` decimal(10,3) NULL COMMENT '分值',
  `is_pass` tinyint(1) NULL COMMENT '是否及格',
  `is_excellent` tinyint(1) NULL COMMENT '是否优秀',
  `is_full` tinyint(1) NULL COMMENT '是否满分',
  `teacher_comment` varchar(255) NULL COMMENT '老师评语',
  `test_date` date NULL COMMENT '测试日期',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pef_score_row` (`batch_id`,`student_no`,`item_code`,`is_delete`),
  KEY `idx_pef_score_query` (`biz_type`,`batch_id`,`school_name`,`grade_name`,`class_name`,`student_name`),
  CONSTRAINT `fk_pef_score_batch` FOREIGN KEY (`batch_id`) REFERENCES `vadmin_pef_batch` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考/体测成绩明细表';

SET FOREIGN_KEY_CHECKS = 1;

