-- 2026-04-01 体考管理系统菜单初始化脚本
-- 适用表: vadmin_auth_menu, vadmin_auth_role_menus

SET @now = NOW();

-- 1. 插入主目录：体考管理
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
SELECT '体考管理', 'ant-design:dashboard-outlined', '/pe/overview', '#', '/pe', 0, 0, 10, '0', NULL, 'pe', 0, 1, 0, 0, 0, 1, @now, @now, 0
WHERE NOT EXISTS (SELECT 1 FROM `vadmin_auth_menu` WHERE `perms` = 'pe');

SET @pe_id = (SELECT id FROM `vadmin_auth_menu` WHERE `perms` = 'pe' LIMIT 1);

-- 2. 插入子菜单：成绩总览
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
SELECT '成绩总览', NULL, NULL, 'views/Vadmin/PE/Overview/Overview', 'overview', 0, 0, 1, '1', @pe_id, 'pe.analysis.overview', 0, 1, 0, 0, 0, 0, @now, @now, 0
WHERE NOT EXISTS (SELECT 1 FROM `vadmin_auth_menu` WHERE `perms` = 'pe.analysis.overview');

-- 3. 插入子菜单：成绩录入
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
SELECT '成绩录入', NULL, NULL, 'views/Vadmin/PE/Entry/Entry', 'entry', 0, 0, 2, '1', @pe_id, 'pe.score.entry', 0, 1, 0, 0, 0, 0, @now, @now, 0
WHERE NOT EXISTS (SELECT 1 FROM `vadmin_auth_menu` WHERE `perms` = 'pe.score.entry');

-- 4. 插入子目录：统计分析
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
SELECT '统计分析', NULL, NULL, '#', 'analysis', 0, 0, 3, '0', @pe_id, 'pe.analysis', 0, 1, 0, 0, 0, 1, @now, @now, 0
WHERE NOT EXISTS (SELECT 1 FROM `vadmin_auth_menu` WHERE `perms` = 'pe.analysis');

SET @analysis_id = (SELECT id FROM `vadmin_auth_menu` WHERE `perms` = 'pe.analysis' LIMIT 1);

-- 5. 插入统计分析子项
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
SELECT '学生阶段对比', NULL, NULL, 'views/Vadmin/PE/Analysis/Student/Student', 'student', 0, 0, 1, '1', @analysis_id, 'pe.analysis.student', 0, 1, 0, 0, 0, 0, @now, @now, 0
WHERE NOT EXISTS (SELECT 1 FROM `vadmin_auth_menu` WHERE `perms` = 'pe.analysis.student');

INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
SELECT '班级对比分析', NULL, NULL, 'views/Vadmin/PE/Analysis/Class/Class', 'class', 0, 0, 2, '1', @analysis_id, 'pe.analysis.class', 0, 1, 0, 0, 0, 0, @now, @now, 0
WHERE NOT EXISTS (SELECT 1 FROM `vadmin_auth_menu` WHERE `perms` = 'pe.analysis.class');

INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
SELECT '年级对比分析', NULL, NULL, 'views/Vadmin/PE/Analysis/Grade/Grade', 'grade', 0, 0, 3, '1', @analysis_id, 'pe.analysis.grade', 0, 1, 0, 0, 0, 0, @now, @now, 0
WHERE NOT EXISTS (SELECT 1 FROM `vadmin_auth_menu` WHERE `perms` = 'pe.analysis.grade');

-- 6. 插入报表中心
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
SELECT '报表中心', NULL, NULL, 'views/Vadmin/PE/Report/Report', 'report', 0, 0, 4, '1', @pe_id, 'pe.report', 0, 1, 0, 0, 0, 0, @now, @now, 0
WHERE NOT EXISTS (SELECT 1 FROM `vadmin_auth_menu` WHERE `perms` = 'pe.report');

-- 7. 插入评分标准
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
SELECT '评分标准', NULL, NULL, 'views/Vadmin/PE/Standard/Standard', 'standard', 0, 0, 5, '1', @pe_id, 'pe.standard', 0, 1, 0, 0, 0, 0, @now, @now, 0
WHERE NOT EXISTS (SELECT 1 FROM `vadmin_auth_menu` WHERE `perms` = 'pe.standard');

-- 8. 为管理员角色 (admin) 分配这些新菜单权限
SET @admin_role_id = (SELECT id FROM `vadmin_auth_role` WHERE `role_key` = 'admin' LIMIT 1);

INSERT INTO `vadmin_auth_role_menus` (`role_id`, `menu_id`)
SELECT @admin_role_id, id FROM `vadmin_auth_menu`
WHERE `perms` LIKE 'pe%'
AND id NOT IN (SELECT menu_id FROM `vadmin_auth_role_menus` WHERE role_id = @admin_role_id);
