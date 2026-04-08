-- 2026-04-06 增量更新脚本
-- 目的：为年级、班级、学生表补全 school_id 字段

SET FOREIGN_KEY_CHECKS = 0;

-- 1. 为年级表增加学校关联
ALTER TABLE `vadmin_pef_grade` ADD COLUMN `school_id` int NOT NULL COMMENT '所属学校ID' AFTER `id`;
ALTER TABLE `vadmin_pef_grade` ADD CONSTRAINT `fk_pef_grade_school` FOREIGN KEY (`school_id`) REFERENCES `vadmin_pef_school` (`id`);

-- 2. 为班级表增加学校关联
ALTER TABLE `vadmin_pef_class` ADD COLUMN `school_id` int NOT NULL COMMENT '所属学校ID' AFTER `id`;
ALTER TABLE `vadmin_pef_class` ADD CONSTRAINT `fk_pef_class_school` FOREIGN KEY (`school_id`) REFERENCES `vadmin_pef_school` (`id`);

-- 3. 为学生表增加学校关联
ALTER TABLE `vadmin_pef_student` ADD COLUMN `school_id` int NOT NULL COMMENT '所属学校ID' AFTER `birthday`;
ALTER TABLE `vadmin_pef_student` ADD CONSTRAINT `fk_pef_student_school` FOREIGN KEY (`school_id`) REFERENCES `vadmin_pef_school` (`id`);

SET FOREIGN_KEY_CHECKS = 1;
