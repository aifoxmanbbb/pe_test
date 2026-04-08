-- 2026-04-07 菜单清理脚本
-- 目的：逻辑删除“仪表盘、工作台、数据概览、用户分布”菜单

SET NAMES utf8mb4;

UPDATE `vadmin_auth_menu` 
SET `is_delete` = 1 
WHERE `title` IN ('仪表盘', '工作台', '数据概览', '用户分布');

-- 同时清理对应的权限关联，防止侧边栏残留
DELETE FROM `vadmin_auth_role_menus` 
WHERE `menu_id` IN (SELECT id FROM `vadmin_auth_menu` WHERE `is_delete` = 1);
