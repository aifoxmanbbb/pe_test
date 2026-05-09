-- 2026-05-09 Fix fitness pull-up / sit-up segment thresholds.
-- Source table: boys pull-up and girls 1-minute sit-up, unit = count, max item score = 10.
-- Blank cells in the source table are intentionally omitted.

SET NAMES utf8mb4;

DROP TEMPORARY TABLE IF EXISTS tmp_fitness_strength_segments;
CREATE TEMPORARY TABLE tmp_fitness_strength_segments (
  stage_type varchar(16) NOT NULL,
  item_code varchar(32) NOT NULL,
  gender varchar(16) NOT NULL,
  segment_json JSON NOT NULL,
  PRIMARY KEY (stage_type, item_code, gender)
);

INSERT INTO tmp_fitness_strength_segments (stage_type, item_code, gender, segment_json)
VALUES
('mid', 'pull_up', 'male', '[{"grade":"\\u521d\\u4e00","rules":[{"level":"\\u4f18\\u79c0","score":"100","range":"13"},{"level":"","score":"95","range":"12"},{"level":"","score":"90","range":"11"},{"level":"\\u826f\\u597d","score":"85","range":"10"},{"level":"","score":"80","range":"9"},{"level":"\\u53ca\\u683c","score":"76","range":"8"},{"level":"","score":"72","range":"7"},{"level":"","score":"68","range":"6"},{"level":"","score":"64","range":"5"},{"level":"","score":"60","range":"4"},{"level":"\\u4e0d\\u53ca\\u683c","score":"50","range":"3"},{"level":"","score":"40","range":"2"},{"level":"","score":"30","range":"1"}]},{"grade":"\\u521d\\u4e8c","rules":[{"level":"\\u4f18\\u79c0","score":"100","range":"14"},{"level":"","score":"95","range":"13"},{"level":"","score":"90","range":"12"},{"level":"\\u826f\\u597d","score":"85","range":"11"},{"level":"","score":"80","range":"10"},{"level":"\\u53ca\\u683c","score":"76","range":"9"},{"level":"","score":"72","range":"8"},{"level":"","score":"68","range":"7"},{"level":"","score":"64","range":"6"},{"level":"","score":"60","range":"5"},{"level":"\\u4e0d\\u53ca\\u683c","score":"50","range":"4"},{"level":"","score":"40","range":"3"},{"level":"","score":"30","range":"2"},{"level":"","score":"20","range":"1"}]},{"grade":"\\u521d\\u4e09","rules":[{"level":"\\u4f18\\u79c0","score":"100","range":"15"},{"level":"","score":"95","range":"14"},{"level":"","score":"90","range":"13"},{"level":"\\u826f\\u597d","score":"85","range":"12"},{"level":"","score":"80","range":"11"},{"level":"\\u53ca\\u683c","score":"76","range":"10"},{"level":"","score":"72","range":"9"},{"level":"","score":"68","range":"8"},{"level":"","score":"64","range":"7"},{"level":"","score":"60","range":"6"},{"level":"\\u4e0d\\u53ca\\u683c","score":"50","range":"5"},{"level":"","score":"40","range":"4"},{"level":"","score":"30","range":"3"},{"level":"","score":"20","range":"2"},{"level":"","score":"10","range":"1"}]}]'),
('high', 'pull_up', 'male', '[{"grade":"\\u9ad8\\u4e00","rules":[{"level":"\\u4f18\\u79c0","score":"100","range":"16"},{"level":"","score":"95","range":"15"},{"level":"","score":"90","range":"14"},{"level":"\\u826f\\u597d","score":"85","range":"13"},{"level":"","score":"80","range":"12"},{"level":"\\u53ca\\u683c","score":"76","range":"11"},{"level":"","score":"72","range":"10"},{"level":"","score":"68","range":"9"},{"level":"","score":"64","range":"8"},{"level":"","score":"60","range":"7"},{"level":"\\u4e0d\\u53ca\\u683c","score":"50","range":"6"},{"level":"","score":"40","range":"5"},{"level":"","score":"30","range":"4"},{"level":"","score":"20","range":"3"},{"level":"","score":"10","range":"2"}]},{"grade":"\\u9ad8\\u4e8c","rules":[{"level":"\\u4f18\\u79c0","score":"100","range":"17"},{"level":"","score":"95","range":"16"},{"level":"","score":"90","range":"15"},{"level":"\\u826f\\u597d","score":"85","range":"14"},{"level":"","score":"80","range":"13"},{"level":"\\u53ca\\u683c","score":"76","range":"12"},{"level":"","score":"72","range":"11"},{"level":"","score":"68","range":"10"},{"level":"","score":"64","range":"9"},{"level":"","score":"60","range":"8"},{"level":"\\u4e0d\\u53ca\\u683c","score":"50","range":"7"},{"level":"","score":"40","range":"6"},{"level":"","score":"30","range":"5"},{"level":"","score":"20","range":"4"},{"level":"","score":"10","range":"3"}]},{"grade":"\\u9ad8\\u4e09","rules":[{"level":"\\u4f18\\u79c0","score":"100","range":"18"},{"level":"","score":"95","range":"17"},{"level":"","score":"90","range":"16"},{"level":"\\u826f\\u597d","score":"85","range":"15"},{"level":"","score":"80","range":"14"},{"level":"\\u53ca\\u683c","score":"76","range":"13"},{"level":"","score":"72","range":"12"},{"level":"","score":"68","range":"11"},{"level":"","score":"64","range":"10"},{"level":"","score":"60","range":"9"},{"level":"\\u4e0d\\u53ca\\u683c","score":"50","range":"8"},{"level":"","score":"40","range":"7"},{"level":"","score":"30","range":"6"},{"level":"","score":"20","range":"5"},{"level":"","score":"10","range":"4"}]}]'),
('mid', 'sit_up', 'female', '[{"grade":"\\u521d\\u4e00","rules":[{"level":"\\u4f18\\u79c0","score":"100","range":"50"},{"level":"","score":"95","range":"48"},{"level":"","score":"90","range":"46"},{"level":"\\u826f\\u597d","score":"85","range":"43"},{"level":"","score":"80","range":"40"},{"level":"\\u53ca\\u683c","score":"78","range":"38"},{"level":"","score":"76","range":"36"},{"level":"","score":"74","range":"34"},{"level":"","score":"72","range":"32"},{"level":"","score":"70","range":"30"},{"level":"","score":"68","range":"28"},{"level":"","score":"66","range":"26"},{"level":"","score":"64","range":"24"},{"level":"","score":"62","range":"22"},{"level":"","score":"60","range":"20"},{"level":"\\u4e0d\\u53ca\\u683c","score":"50","range":"18"},{"level":"","score":"40","range":"16"},{"level":"","score":"30","range":"14"},{"level":"","score":"20","range":"12"},{"level":"","score":"10","range":"10"}]},{"grade":"\\u521d\\u4e8c","rules":[{"level":"\\u4f18\\u79c0","score":"100","range":"51"},{"level":"","score":"95","range":"49"},{"level":"","score":"90","range":"47"},{"level":"\\u826f\\u597d","score":"85","range":"44"},{"level":"","score":"80","range":"41"},{"level":"\\u53ca\\u683c","score":"78","range":"39"},{"level":"","score":"76","range":"37"},{"level":"","score":"74","range":"35"},{"level":"","score":"72","range":"33"},{"level":"","score":"70","range":"31"},{"level":"","score":"68","range":"29"},{"level":"","score":"66","range":"27"},{"level":"","score":"64","range":"25"},{"level":"","score":"62","range":"23"},{"level":"","score":"60","range":"21"},{"level":"\\u4e0d\\u53ca\\u683c","score":"50","range":"19"},{"level":"","score":"40","range":"17"},{"level":"","score":"30","range":"15"},{"level":"","score":"20","range":"13"},{"level":"","score":"10","range":"11"}]},{"grade":"\\u521d\\u4e09","rules":[{"level":"\\u4f18\\u79c0","score":"100","range":"52"},{"level":"","score":"95","range":"50"},{"level":"","score":"90","range":"48"},{"level":"\\u826f\\u597d","score":"85","range":"45"},{"level":"","score":"80","range":"42"},{"level":"\\u53ca\\u683c","score":"78","range":"40"},{"level":"","score":"76","range":"38"},{"level":"","score":"74","range":"36"},{"level":"","score":"72","range":"34"},{"level":"","score":"70","range":"32"},{"level":"","score":"68","range":"30"},{"level":"","score":"66","range":"28"},{"level":"","score":"64","range":"26"},{"level":"","score":"62","range":"24"},{"level":"","score":"60","range":"22"},{"level":"\\u4e0d\\u53ca\\u683c","score":"50","range":"20"},{"level":"","score":"40","range":"18"},{"level":"","score":"30","range":"16"},{"level":"","score":"20","range":"14"},{"level":"","score":"10","range":"12"}]}]'),
('high', 'sit_up', 'female', '[{"grade":"\\u9ad8\\u4e00","rules":[{"level":"\\u4f18\\u79c0","score":"100","range":"53"},{"level":"","score":"95","range":"51"},{"level":"","score":"90","range":"49"},{"level":"\\u826f\\u597d","score":"85","range":"46"},{"level":"","score":"80","range":"43"},{"level":"\\u53ca\\u683c","score":"78","range":"41"},{"level":"","score":"76","range":"39"},{"level":"","score":"74","range":"37"},{"level":"","score":"72","range":"35"},{"level":"","score":"70","range":"33"},{"level":"","score":"68","range":"31"},{"level":"","score":"66","range":"29"},{"level":"","score":"64","range":"27"},{"level":"","score":"62","range":"25"},{"level":"","score":"60","range":"23"},{"level":"\\u4e0d\\u53ca\\u683c","score":"50","range":"21"},{"level":"","score":"40","range":"19"},{"level":"","score":"30","range":"17"},{"level":"","score":"20","range":"15"},{"level":"","score":"10","range":"13"}]},{"grade":"\\u9ad8\\u4e8c","rules":[{"level":"\\u4f18\\u79c0","score":"100","range":"54"},{"level":"","score":"95","range":"52"},{"level":"","score":"90","range":"50"},{"level":"\\u826f\\u597d","score":"85","range":"47"},{"level":"","score":"80","range":"44"},{"level":"\\u53ca\\u683c","score":"78","range":"42"},{"level":"","score":"76","range":"40"},{"level":"","score":"74","range":"38"},{"level":"","score":"72","range":"36"},{"level":"","score":"70","range":"34"},{"level":"","score":"68","range":"32"},{"level":"","score":"66","range":"30"},{"level":"","score":"64","range":"28"},{"level":"","score":"62","range":"26"},{"level":"","score":"60","range":"24"},{"level":"\\u4e0d\\u53ca\\u683c","score":"50","range":"22"},{"level":"","score":"40","range":"20"},{"level":"","score":"30","range":"18"},{"level":"","score":"20","range":"16"},{"level":"","score":"10","range":"14"}]},{"grade":"\\u9ad8\\u4e09","rules":[{"level":"\\u4f18\\u79c0","score":"100","range":"55"},{"level":"","score":"95","range":"53"},{"level":"","score":"90","range":"51"},{"level":"\\u826f\\u597d","score":"85","range":"48"},{"level":"","score":"80","range":"45"},{"level":"\\u53ca\\u683c","score":"78","range":"43"},{"level":"","score":"76","range":"41"},{"level":"","score":"74","range":"39"},{"level":"","score":"72","range":"37"},{"level":"","score":"70","range":"35"},{"level":"","score":"68","range":"33"},{"level":"","score":"66","range":"31"},{"level":"","score":"64","range":"29"},{"level":"","score":"62","range":"27"},{"level":"","score":"60","range":"25"},{"level":"\\u4e0d\\u53ca\\u683c","score":"50","range":"23"},{"level":"","score":"40","range":"21"},{"level":"","score":"30","range":"19"},{"level":"","score":"20","range":"17"},{"level":"","score":"10","range":"15"}]}]');

UPDATE vadmin_pef_standard_item si
JOIN vadmin_pef_standard s ON s.id = si.standard_id
JOIN tmp_fitness_strength_segments seg
  ON seg.stage_type = s.stage_type
 AND seg.item_code = si.item_code
 AND seg.gender = si.gender
SET
  si.calc_mode = 'segment',
  si.pass_threshold = NULL,
  si.excellent_threshold = NULL,
  si.full_threshold = NULL,
  si.segment_json = seg.segment_json,
  si.max_score = 10,
  si.update_datetime = NOW()
WHERE s.biz_type = 'fitness'
  AND s.is_delete = 0
  AND si.is_delete = 0
  AND s.stage_type IN ('mid', 'high')
  AND si.item_code IN ('pull_up', 'sit_up')
  AND si.gender IN ('male', 'female');

SELECT
  s.name AS standard_name,
  s.stage_type,
  si.item_code,
  si.item_name,
  si.gender,
  si.max_score,
  JSON_UNQUOTE(JSON_EXTRACT(si.segment_json, '$[0].rules[0].range')) AS first_full_mark
FROM vadmin_pef_standard s
JOIN vadmin_pef_standard_item si ON si.standard_id = s.id
WHERE s.biz_type = 'fitness'
  AND s.is_delete = 0
  AND si.is_delete = 0
  AND s.stage_type IN ('mid', 'high')
  AND si.item_code IN ('pull_up', 'sit_up')
ORDER BY s.stage_type, si.item_code, si.gender;
