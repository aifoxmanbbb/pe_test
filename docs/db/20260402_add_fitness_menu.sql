-- 2026-04-02 体测管理系统菜单初始化脚本
-- 适用表: vadmin_auth_menu, vadmin_auth_role_menus

SET @now = NOW();

-- 1. 插入主目录：体测管理
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
SELECT '体测管理', 'ant-design:line-chart-outlined', '/fitness/overview', '#', '/fitness', 0, 0, 11, '0', NULL, 'fitness', 0, 1, 0, 0, 0, 1, @now, @now, 0
WHERE NOT EXISTS (SELECT 1 FROM `vadmin_auth_menu` WHERE `perms` = 'fitness');

SET @fitness_id = (SELECT id FROM `vadmin_auth_menu` WHERE `perms` = 'fitness' LIMIT 1);

-- 2. 插入子菜单：体测总览
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
SELECT '体测总览', NULL, NULL, 'views/Vadmin/Fitness/Overview/Overview', 'overview', 0, 0, 1, '1', @fitness_id, 'fitness.analysis.overview', 0, 1, 0, 0, 0, 0, @now, @now, 0
WHERE NOT EXISTS (SELECT 1 FROM `vadmin_auth_menu` WHERE `perms` = 'fitness.analysis.overview');

-- 3. 插入子菜单：体测录入
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
SELECT '体测录入', NULL, NULL, 'views/Vadmin/Fitness/Entry/Entry', 'entry', 0, 0, 2, '1', @fitness_id, 'fitness.score.entry', 0, 1, 0, 0, 0, 0, @now, @now, 0
WHERE NOT EXISTS (SELECT 1 FROM `vadmin_auth_menu` WHERE `perms` = 'fitness.score.entry');

-- 4. 插入子目录：统计分析
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
SELECT '统计分析', NULL, NULL, '#', 'analysis', 0, 0, 3, '0', @fitness_id, 'fitness.analysis', 0, 1, 0, 0, 0, 1, @now, @now, 0
WHERE NOT EXISTS (SELECT 1 FROM `vadmin_auth_menu` WHERE `perms` = 'fitness.analysis');

SET @fitness_analysis_id = (SELECT id FROM `vadmin_auth_menu` WHERE `perms` = 'fitness.analysis' LIMIT 1);

-- 5. 插入统计分析子项
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
SELECT '学生体测分析', NULL, NULL, 'views/Vadmin/Fitness/Analysis/Student/Student', 'student', 0, 0, 1, '1', @fitness_analysis_id, 'fitness.analysis.student', 0, 1, 0, 0, 0, 0, @now, @now, 0
WHERE NOT EXISTS (SELECT 1 FROM `vadmin_auth_menu` WHERE `perms` = 'fitness.analysis.student');

INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
SELECT '班级体测分析', NULL, NULL, 'views/Vadmin/Fitness/Analysis/Class/Class', 'class', 0, 0, 2, '1', @fitness_analysis_id, 'fitness.analysis.class', 0, 1, 0, 0, 0, 0, @now, @now, 0
WHERE NOT EXISTS (SELECT 1 FROM `vadmin_auth_menu` WHERE `perms` = 'fitness.analysis.class');

INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
SELECT '年级体测分析', NULL, NULL, 'views/Vadmin/Fitness/Analysis/Grade/Grade', 'grade', 0, 0, 3, '1', @fitness_analysis_id, 'fitness.analysis.grade', 0, 1, 0, 0, 0, 0, @now, @now, 0
WHERE NOT EXISTS (SELECT 1 FROM `vadmin_auth_menu` WHERE `perms` = 'fitness.analysis.grade');

-- 6. 插入体测报表中心
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
SELECT '体测报表中心', NULL, NULL, 'views/Vadmin/Fitness/Report/Report', 'report', 0, 0, 4, '1', @fitness_id, 'fitness.report.export', 0, 1, 0, 0, 0, 0, @now, @now, 0
WHERE NOT EXISTS (SELECT 1 FROM `vadmin_auth_menu` WHERE `perms` = 'fitness.report.export');

-- 7. 插入体测标准中心
INSERT INTO `vadmin_auth_menu` (`title`, `icon`, `redirect`, `component`, `path`, `disabled`, `hidden`, `order`, `menu_type`, `parent_id`, `perms`, `noCache`, `breadcrumb`, `affix`, `noTagsView`, `canTo`, `alwaysShow`, `create_datetime`, `update_datetime`, `is_delete`)
SELECT '体测标准中心', NULL, NULL, 'views/Vadmin/Fitness/Standard/Standard', 'standard', 0, 0, 5, '1', @fitness_id, 'fitness.standard.list', 0, 1, 0, 0, 0, 0, @now, @now, 0
WHERE NOT EXISTS (SELECT 1 FROM `vadmin_auth_menu` WHERE `perms` = 'fitness.standard.list');

-- 8. 为管理员角色 (admin) 分配菜单权限
SET @admin_role_id = (SELECT id FROM `vadmin_auth_role` WHERE `role_key` = 'admin' LIMIT 1);

INSERT INTO `vadmin_auth_role_menus` (`role_id`, `menu_id`)
SELECT @admin_role_id, id FROM `vadmin_auth_menu`
WHERE `perms` LIKE 'fitness%'
AND id NOT IN (SELECT menu_id FROM `vadmin_auth_role_menus` WHERE role_id = @admin_role_id);
