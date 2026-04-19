CREATE TABLE IF NOT EXISTS `vadmin_pef_school_leaders` (
  `school_id` int NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`school_id`, `user_id`),
  KEY `idx_pef_school_leaders_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学校与校领导关联';

CREATE TABLE IF NOT EXISTS `vadmin_pef_class_coaches` (
  `class_id` int NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`class_id`, `user_id`),
  KEY `idx_pef_class_coaches_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='班级与老师教练关联';

INSERT INTO `vadmin_auth_role` (`name`, `role_key`, `data_range`, `disabled`, `order`, `desc`, `is_admin`, `create_datetime`, `update_datetime`, `delete_datetime`, `is_delete`)
SELECT '学校领导', 'school_leader', 0, 0, 110, '学校领导角色，仅可查看编辑本校体育数据', 0, NOW(), NOW(), NULL, 0
WHERE NOT EXISTS (
  SELECT 1 FROM `vadmin_auth_role` WHERE `role_key` = 'school_leader' AND `is_delete` = 0
);

INSERT INTO `vadmin_auth_role` (`name`, `role_key`, `data_range`, `disabled`, `order`, `desc`, `is_admin`, `create_datetime`, `update_datetime`, `delete_datetime`, `is_delete`)
SELECT '老师教练', 'teacher_coach', 0, 0, 120, '老师教练角色，仅可查看编辑关联班级体育数据', 0, NOW(), NOW(), NULL, 0
WHERE NOT EXISTS (
  SELECT 1 FROM `vadmin_auth_role` WHERE `role_key` = 'teacher_coach' AND `is_delete` = 0
);

INSERT INTO `vadmin_auth_role_menus` (`role_id`, `menu_id`)
SELECT r.`id`, m.`id`
FROM `vadmin_auth_role` r
JOIN `vadmin_auth_menu` m ON m.`perms` IN (
  'pe', 'pe.analysis.overview', 'pe.score.entry', 'pe.analysis', 'pe.analysis.student', 'pe.analysis.class', 'pe.analysis.grade', 'pe.batch',
  'fitness', 'fitness.analysis.overview', 'fitness.score.entry', 'fitness.analysis', 'fitness.analysis.student', 'fitness.analysis.class', 'fitness.analysis.grade', 'fitness.batch',
  'sport.student', 'sport.student.scores',
  'sport.foundation', 'sport.foundation.grade', 'sport.foundation.class', 'sport.foundation.student'
)
WHERE r.`role_key` = 'school_leader'
  AND r.`is_delete` = 0
  AND m.`is_delete` = 0
  AND NOT EXISTS (
    SELECT 1 FROM `vadmin_auth_role_menus` rm WHERE rm.`role_id` = r.`id` AND rm.`menu_id` = m.`id`
  );

INSERT INTO `vadmin_auth_role_menus` (`role_id`, `menu_id`)
SELECT r.`id`, m.`id`
FROM `vadmin_auth_role` r
JOIN `vadmin_auth_menu` m ON m.`perms` IN (
  'pe', 'pe.analysis.overview', 'pe.score.entry', 'pe.analysis', 'pe.analysis.student', 'pe.analysis.class', 'pe.analysis.grade', 'pe.batch',
  'fitness', 'fitness.analysis.overview', 'fitness.score.entry', 'fitness.analysis', 'fitness.analysis.student', 'fitness.analysis.class', 'fitness.analysis.grade', 'fitness.batch',
  'sport.student', 'sport.student.scores',
  'sport.foundation', 'sport.foundation.student'
)
WHERE r.`role_key` = 'teacher_coach'
  AND r.`is_delete` = 0
  AND m.`is_delete` = 0
  AND NOT EXISTS (
    SELECT 1 FROM `vadmin_auth_role_menus` rm WHERE rm.`role_id` = r.`id` AND rm.`menu_id` = m.`id`
  );
