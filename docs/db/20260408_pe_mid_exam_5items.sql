/*
  中考体考五项目评分标准初始化（男1000/女800/跳绳/跳远/实心球）
  生成日期：2026-04-08
  说明：
  1) 新建一版中考标准：V2026-中考-五项目评分
  2) 写入 vadmin_pef_standard_item 对应项目与阈值/分值段
*/

SET NAMES utf8mb4;

-- 如已存在同版本标准，先逻辑删除（避免重复版本冲突）
UPDATE `vadmin_pef_standard`
SET `is_delete` = 1
WHERE `biz_type` = 'pe'
  AND `stage_type` = 'mid'
  AND `version` = 'V2026-中考-五项目评分'
  AND `is_delete` = 0;

-- 新建标准主表
INSERT INTO `vadmin_pef_standard`
(`biz_type`, `name`, `region`, `year`, `stage_type`, `version`, `status`, `source_type`, `conflict_policy`, `remark`)
VALUES
('pe', '中考体考五项目评分标准（男1000/女800/跳绳/跳远/实心球）', '通用', 2026, 'mid', 'V2026-中考-五项目评分', 'published', 'manual', 'lower_priority', '门槛项+三计分项，按性别配置阈值与分值段');

SET @std_id = LAST_INSERT_ID();

-- 写入标准项目（对应 vadmin_pef_standard_item）
INSERT INTO `vadmin_pef_standard_item`
(`standard_id`, `item_code`, `item_name`, `gender`, `calc_mode`, `pass_threshold`, `excellent_threshold`, `full_threshold`, `segment_json`, `is_required`, `is_gate_item`, `max_score`, `sort`)
VALUES
-- 1) 门槛项：男生1000米
(@std_id, 'run_gate', '男生1000米', 'male', 'threshold', 295.000, 250.000, 220.000,
 NULL, 1, 1, 0.000, 1),

-- 2) 门槛项：女生800米
(@std_id, 'run_gate', '女生800米', 'female', 'threshold', 263.000, 230.000, 205.000,
 NULL, 1, 1, 0.000, 2),

-- 3) 1分钟跳绳（男女同标，20分）
(@std_id, 'rope', '1分钟跳绳', 'all', 'segment', 110.000, 155.000, 185.000,
 '[
   {"range":"0~109","score":0},
   {"range":"110~154","score":12},
   {"range":"155~184","score":16},
   {"range":"185~999","score":20}
 ]',
 1, 0, 20.000, 3),

-- 4) 立定跳远（男，15分）
(@std_id, 'jump', '立定跳远', 'male', 'segment', 1.850, 2.250, 2.400,
 '[
   {"range":"0~1.849","score":0},
   {"range":"1.850~2.249","score":9},
   {"range":"2.250~2.399","score":12},
   {"range":"2.400~5.000","score":15}
 ]',
 1, 0, 15.000, 4),

-- 5) 立定跳远（女，15分）
(@std_id, 'jump', '立定跳远', 'female', 'segment', 1.460, 1.850, 2.030,
 '[
   {"range":"0~1.459","score":0},
   {"range":"1.460~1.849","score":9},
   {"range":"1.850~2.029","score":12},
   {"range":"2.030~5.000","score":15}
 ]',
 1, 0, 15.000, 5),

-- 6) 掷实心球（男，15分）
(@std_id, 'ball', '掷实心球', 'male', 'segment', 5.600, 8.600, 9.700,
 '[
   {"range":"0~5.599","score":0},
   {"range":"5.600~8.599","score":9},
   {"range":"8.600~9.699","score":12},
   {"range":"9.700~30.000","score":15}
 ]',
 1, 0, 15.000, 6),

-- 7) 掷实心球（女，15分）
(@std_id, 'ball', '掷实心球', 'female', 'segment', 4.000, 5.800, 6.500,
 '[
   {"range":"0~3.999","score":0},
   {"range":"4.000~5.799","score":9},
   {"range":"5.800~6.499","score":12},
   {"range":"6.500~30.000","score":15}
 ]',
 1, 0, 15.000, 7);
