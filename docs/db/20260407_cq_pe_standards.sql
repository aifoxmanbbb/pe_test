/*
  重庆市体考评分标准初始化脚本
  生成日期：2026-04-06
  根据文件：重庆体考.txt 实际成绩与分数匹配关系生成
*/

SET NAMES utf8mb4;

-- =========================================================================
-- 1. 重庆高考体考（体育类专业统考）
-- 总分100分：身体素质（60%） + 专项素质（40%）
-- =========================================================================
INSERT INTO `vadmin_pef_standard` (`biz_type`, `name`, `region`, `year`, `stage_type`, `version`, `status`, `conflict_policy`, `remark`)
VALUES ('pe', '重庆市高考体育专业统考标准', '重庆市', 2026, 'high', 'V2026-高考', 'published', 'lower_priority', '身体素质(4项各25分)+专项(100分)');
SET @high_std_id = LAST_INSERT_ID();

INSERT INTO `vadmin_pef_standard_item` 
(`standard_id`, `item_code`, `item_name`, `gender`, `calc_mode`, `pass_threshold`, `excellent_threshold`, `full_threshold`, `is_required`, `is_gate_item`, `max_score`, `sort`)
VALUES 
-- 必考：100米跑 (男满分通常在11.3秒内，女12.8秒内)
(@high_std_id, '100m', '100米跑', 'male', 'segment', 13.5, 12.0, 11.3, 1, 0, 25.000, 1),
(@high_std_id, '100m', '100米跑', 'female', 'segment', 15.5, 13.5, 12.8, 1, 0, 25.000, 2),

-- 必考：800米跑 (男满分通常2分03秒(123s)，女2分26秒(146s))
(@high_std_id, '800m', '800米跑', 'male', 'segment', 155, 135, 123, 1, 0, 25.000, 3),
(@high_std_id, '800m', '800米跑', 'female', 'segment', 190, 160, 146, 1, 0, 25.000, 4),

-- 必考：立定跳远 (男满分通常2.85m以上，女2.40m以上)
(@high_std_id, 'jump', '立定跳远', 'male', 'segment', 2.30, 2.65, 2.85, 1, 0, 25.000, 5),
(@high_std_id, 'jump', '立定跳远', 'female', 'segment', 1.90, 2.20, 2.40, 1, 0, 25.000, 6),

-- 必考：原地向前掷实心球 (男满分预估14.5m，女10.0m)
(@high_std_id, 'ball', '原地向前掷实心球', 'male', 'segment', 9.00, 12.50, 14.50, 1, 0, 25.000, 7),
(@high_std_id, 'ball', '原地向前掷实心球', 'female', 'segment', 6.50, 8.50, 10.00, 1, 0, 25.000, 8),

-- 选考：专项素质 (11大类选1项，总分100分，此处作为一个总括录入项)
(@high_std_id, 'special', '专项素质(选考)', 'all', 'segment', 60.0, 85.0, 100.0, 1, 0, 100.000, 9);


-- =========================================================================
-- 2. 重庆中考体考（2026年现行）
-- 总分50分：门槛项目（不计分） + 计分项目（跳绳20+跳远15+实心球15）
-- =========================================================================
INSERT INTO `vadmin_pef_standard` (`biz_type`, `name`, `region`, `year`, `stage_type`, `version`, `status`, `conflict_policy`, `remark`)
VALUES ('pe', '重庆市中考体考标准（2026版）', '重庆市', 2026, 'mid', 'V2026-中考', 'published', 'lower_priority', '50分制，门槛+老三项');
SET @mid26_std_id = LAST_INSERT_ID();

INSERT INTO `vadmin_pef_standard_item` 
(`standard_id`, `item_code`, `item_name`, `gender`, `calc_mode`, `pass_threshold`, `excellent_threshold`, `full_threshold`, `is_required`, `is_gate_item`, `max_score`, `sort`)
VALUES 
-- 门槛项目 (必测不计分，男1000m及格通常4分55秒(295s)，女800m及格通常4分23秒(263s))
(@mid26_std_id, '1000m_gate', '男生1000米(门槛)', 'male', 'threshold', 295, NULL, NULL, 1, 1, 0.000, 1),
(@mid26_std_id, '800m_gate', '女生800米(门槛)', 'female', 'threshold', 263, NULL, NULL, 1, 1, 0.000, 2),

-- 计分项目一：1分钟跳绳 (男女满分均为185次，及格一般为60次)
(@mid26_std_id, 'rope', '1分钟跳绳', 'all', 'segment', 60, 150, 185, 1, 0, 20.000, 3),

-- 计分项目二：立定跳远 (男满分2.40m，女满分2.03m)
(@mid26_std_id, 'jump', '立定跳远', 'male', 'segment', 1.85, 2.25, 2.40, 1, 0, 15.000, 4),
(@mid26_std_id, 'jump', '立定跳远', 'female', 'segment', 1.46, 1.85, 2.03, 1, 0, 15.000, 5),

-- 计分项目三：掷实心球 (男满分9.70m，女满分6.50m)
(@mid26_std_id, 'ball', '掷实心球', 'male', 'segment', 5.60, 8.60, 9.70, 1, 0, 15.000, 6),
(@mid26_std_id, 'ball', '掷实心球', 'female', 'segment', 4.00, 5.80, 6.50, 1, 0, 15.000, 7);


-- =========================================================================
-- 3. 重庆中考体考新方案（2028年起，2必考+1选考）
-- 总分50分：立定跳远15 + 跳绳15 + 选考(8选1)20
-- =========================================================================
INSERT INTO `vadmin_pef_standard` (`biz_type`, `name`, `region`, `year`, `stage_type`, `version`, `status`, `conflict_policy`, `remark`)
VALUES ('pe', '重庆市中考体考标准（2028新方案）', '重庆市', 2028, 'mid', 'V2028-中考', 'draft', 'lower_priority', '50分制，2必考+1选考');
SET @mid28_std_id = LAST_INSERT_ID();

INSERT INTO `vadmin_pef_standard_item` 
(`standard_id`, `item_code`, `item_name`, `gender`, `calc_mode`, `pass_threshold`, `excellent_threshold`, `full_threshold`, `is_required`, `is_gate_item`, `max_score`, `sort`)
VALUES 
-- 必考项目
(@mid28_std_id, 'jump', '立定跳远', 'all', 'segment', 1.80, 2.20, 2.40, 1, 0, 15.000, 1),
(@mid28_std_id, 'rope', '1分钟跳绳', 'all', 'segment', 60, 150, 185, 1, 0, 15.000, 2),

-- 选考项目 (8选1，为了系统能够录入，is_required均设为0，由前端验证)
(@mid28_std_id, 'basketball', '篮球', 'all', 'segment', 12.0, 16.0, 20.0, 0, 0, 20.000, 3),
(@mid28_std_id, 'football', '足球', 'all', 'segment', 12.0, 16.0, 20.0, 0, 0, 20.000, 4),
(@mid28_std_id, 'volleyball', '排球', 'all', 'segment', 12.0, 16.0, 20.0, 0, 0, 20.000, 5),
(@mid28_std_id, 'badminton', '羽毛球', 'all', 'segment', 12.0, 16.0, 20.0, 0, 0, 20.000, 6),
(@mid28_std_id, 'table_tennis', '乒乓球', 'all', 'segment', 12.0, 16.0, 20.0, 0, 0, 20.000, 7),
(@mid28_std_id, 'tennis', '网球', 'all', 'segment', 12.0, 16.0, 20.0, 0, 0, 20.000, 8),
(@mid28_std_id, 'swim_100m', '100米游泳', 'all', 'segment', 12.0, 16.0, 20.0, 0, 0, 20.000, 9),
(@mid28_std_id, 'wushu', '武术', 'all', 'segment', 12.0, 16.0, 20.0, 0, 0, 20.000, 10);
