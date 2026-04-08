/*
  体考/体测系统模拟数据脚本
  生成日期：2026-04-06
  说明：用于全流程功能演示，包含学校、年级、班级、学生、标准、批次及成绩。
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. 模拟年级 (vadmin_pef_grade)
INSERT INTO `vadmin_pef_grade` (`grade_name`, `grade_code`, `sort`) VALUES 
('小学一年级', 'P1', 1),
('小学二年级', 'P2', 2),
('初三', 'M3', 9),
('高三', 'H3', 12);

-- 2. 模拟班级 (vadmin_pef_class)
-- 假设 ID 顺序为 1,2,3,4
INSERT INTO `vadmin_pef_class` (`grade_id`, `class_name`, `class_code`, `sort`) VALUES 
(1, '1年1班', 'P1-1', 1),
(1, '1年2班', 'P1-2', 2),
(2, '2年1班', 'P2-1', 1),
(3, '3年1班', 'M3-1', 1),
(3, '3年2班', 'M3-2', 2),
(4, '高三1班', 'H3-1', 1);

-- 3. 模拟学生 (vadmin_pef_student)
INSERT INTO `vadmin_pef_student` (`student_no`, `name`, `gender`, `grade_id`, `class_id`, `phone`) VALUES 
('20260101', '张小明', 'male', 1, 1, '13800000001'),
('20260102', '王小红', 'female', 1, 1, '13800000002'),
('20260103', '李小亮', 'male', 1, 2, '13800000003'),
('20260301', '周杰', 'male', 3, 4, '13800000004'),
('20260302', '蔡依', 'female', 3, 4, '13800000005'),
('20260303', '林俊', 'male', 3, 5, '13800000006'),
('20260401', '陈奕', 'male', 4, 6, '13800000007');

-- 4. 模拟评分标准 (vadmin_pef_standard)
INSERT INTO `vadmin_pef_standard` (`biz_type`, `name`, `region`, `year`, `stage_type`, `version`, `status`) VALUES 
('pe', '重庆初中体育2026标准', '重庆', 2026, 'mid', 'V1.0', 'published'),
('fitness', '国家学生体质健康标准-小学', '全国', 2026, 'primary', 'V2014', 'published');

SET @std_pe = (SELECT id FROM `vadmin_pef_standard` WHERE `biz_type` = 'pe' LIMIT 1);
SET @std_fit = (SELECT id FROM `vadmin_pef_standard` WHERE `biz_type` = 'fitness' LIMIT 1);

-- 5. 模拟标准项 (vadmin_pef_standard_item)
INSERT INTO `vadmin_pef_standard_item` (`standard_id`, `item_code`, `item_name`, `gender`, `calc_mode`, `segment_json`) VALUES 
(@std_pe, 'item_1', '1000米/800米', 'all', 'threshold', NULL),
(@std_pe, 'item_2', '跳绳', 'all', 'segment', '[{"score": 20, "value": 180}, {"score": 15, "value": 140}]'),
(@std_fit, 'item_1', '身高体重BMI', 'all', 'threshold', NULL),
(@std_fit, 'item_2', '肺活量', 'male', 'segment', '[{"score": 100, "value": 3000}, {"score": 60, "value": 2000}]');

-- 6. 模拟测试批次 (vadmin_pef_batch)
INSERT INTO `vadmin_pef_batch` (`biz_type`, `batch_name`, `standard_id`, `school_name`, `grade_name`, `class_name`, `stage_type`, `status`) VALUES 
('pe', '2026第一中学初三摸底', @std_pe, '第一中学', '初三', '3年1班', 'mid', 'ongoing'),
('fitness', '2026实验小学一年级体测', @std_fit, '实验小学', '小学一年级', '1年1班', 'primary', 'ongoing');

SET @batch_pe = (SELECT id FROM `vadmin_pef_batch` WHERE `biz_type` = 'pe' LIMIT 1);
SET @batch_fit = (SELECT id FROM `vadmin_pef_batch` WHERE `biz_type` = 'fitness' LIMIT 1);

-- 7. 模拟成绩记录 (vadmin_pef_score)
INSERT INTO `vadmin_pef_score` (`biz_type`, `batch_id`, `student_no`, `student_name`, `gender`, `school_name`, `grade_name`, `class_name`, `item_code`, `item_name`, `raw_score`, `score_value`) VALUES 
('pe', @batch_pe, '20260301', '周杰', 'male', '第一中学', '初三', '3年1班', 'item_2', '跳绳', '185', 20.0),
('pe', @batch_pe, '20260302', '蔡依', 'female', '第一中学', '初三', '3年1班', 'item_2', '跳绳', '175', 18.5),
('fitness', @batch_fit, '20260101', '张小明', 'male', '实验小学', '小学一年级', '1年1班', 'item_2', '肺活量', '2500', 85.0);

SET FOREIGN_KEY_CHECKS = 1;
