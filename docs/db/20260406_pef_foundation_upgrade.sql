-- 2026-04-06 体育基础档案升级脚本
-- 1. 新增学校表，并为年级/班级/学生增加物理关联
-- 2. 补全档案管理菜单

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. 创建学校表
CREATE TABLE IF NOT EXISTS `vadmin_pef_school` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `school_name` varchar(120) NOT NULL UNIQUE COMMENT '学校名称',
  `school_code` varchar(50) COMMENT '学校代码',
  `region` varchar(100) COMMENT '所属地区',
  `stage_types` varchar(64) DEFAULT 'mid,high' COMMENT '学段集合：primary,mid,high,university',
  `sort` int NOT NULL DEFAULT 0,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_delete` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体考体测-学校';

-- 2. 为现有表补全 school_id 字段 (增加存在性检查)
-- 注意：如果字段已存在，执行可能会报错，请根据实际情况调整
ALTER TABLE `vadmin_pef_grade` ADD COLUMN `school_id` int NOT NULL COMMENT '所属学校ID' AFTER `id`;
ALTER TABLE `vadmin_pef_class` ADD COLUMN `school_id` int NOT NULL COMMENT '所属学校ID' AFTER `id`;
ALTER TABLE `vadmin_pef_student` ADD COLUMN `school_id` int NOT NULL COMMENT '所属学校ID' AFTER `birthday`;

-- 3. 建立外键约束
ALTER TABLE `vadmin_pef_grade` ADD CONSTRAINT `fk_grade_school` FOREIGN KEY (`school_id`) REFERENCES `vadmin_pef_school` (`id`);
ALTER TABLE `vadmin_pef_class` ADD CONSTRAINT `fk_class_school` FOREIGN KEY (`school_id`) REFERENCES `vadmin_pef_school` (`id`);
ALTER TABLE `vadmin_pef_student` ADD CONSTRAINT `fk_student_school` FOREIGN KEY (`school_id`) REFERENCES `vadmin_pef_school` (`id`);

-- 4. 菜单初始化
SET @now = NOW();

-- 清理旧菜单 (防重复)
DELETE FROM `vadmin_auth_role_menus` WHERE `menu_id` IN (SELECT id FROM `vadmin_auth_menu` WHERE `perms` LIKE 'sport.foundation%');
DELETE FROM `vadmin_auth_menu` WHERE `perms` LIKE 'sport.foundation%';

-- 插入顶级目录：体育基础档案 (必须指向 Layout 才能打开子页面)
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
VALUES ('体育基础档案', 'ant-design:database-outlined', '/sport/foundation/school', 'Layout', '/sport/foundation', 0, 0, 13, '0', NULL, 'sport.foundation', 0, 1, 0, 0, 0, 1, @now, @now, 0);
SET @found_root = LAST_INSERT_ID();

-- 插入子菜单
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
VALUES 
('学校管理', NULL, NULL, 'views/Vadmin/Sport/School/School', 'school', 0, 0, 1, '1', @found_root, 'sport.foundation.school', 0, 1, 0, 0, 0, 0, @now, @now, 0),
('年级管理', NULL, NULL, 'views/Vadmin/Sport/Grade/Grade', 'grade', 0, 0, 2, '1', @found_root, 'sport.foundation.grade', 0, 1, 0, 0, 0, 0, @now, @now, 0),
('班级管理', NULL, NULL, 'views/Vadmin/Sport/Class/Class', 'class', 0, 0, 3, '1', @found_root, 'sport.foundation.class', 0, 1, 0, 0, 0, 0, @now, @now, 0),
('学生管理', NULL, NULL, 'views/Vadmin/Sport/Student/Student', 'student', 0, 0, 4, '1', @found_root, 'sport.foundation.student', 0, 1, 0, 0, 0, 0, @now, @now, 0);

-- 5. 分配权限
SET @admin_role_id = (SELECT id FROM `vadmin_auth_role` WHERE `role_key` = 'admin' LIMIT 1);
INSERT INTO `vadmin_auth_role_menus` (`role_id`, `menu_id`)
SELECT @admin_role_id, id FROM `vadmin_auth_menu` WHERE `perms` LIKE 'sport.foundation%';

SET FOREIGN_KEY_CHECKS = 1;
