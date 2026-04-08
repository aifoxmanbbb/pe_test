import json

def parse_segment_cell(cell_str):
    """
    Parses strings like '13.5~18.1', '≤13.4', '≥20.4'
    Returns dict for segment, e.g. {'min': 13.5, 'max': 18.1} or {'max': 13.4} or {'min': 20.4}
    For time (like 1000m, string like 4'32"), it needs special parsing.
    """
    cell_str = str(cell_str).strip()
    if not cell_str:
        return None
        
    def parse_val(v):
        v = v.replace("'", ".").replace("\"", "") # For minutes/seconds
        try:
            return float(v)
        except:
            return 0.0

    if '~' in cell_str:
        parts = cell_str.split('~')
        return {'min': parse_val(parts[0]), 'max': parse_val(parts[1])}
    elif '≤' in cell_str or '<=' in cell_str:
        v = cell_str.replace('≤', '').replace('<=', '')
        return {'max': parse_val(v)}
    elif '≥' in cell_str or '>=' in cell_str:
        v = cell_str.replace('≥', '').replace('>=', '')
        return {'min': parse_val(v)}
    else:
        return {'exact': parse_val(cell_str)}

def generate_sql():
    with open('tables_debug.json', 'r', encoding='utf-8') as f:
        tables = json.load(f)
        
    table_metadata = [
        {"name": "BMI", "code": "bmi", "gender": "male", "type": "bmi"},
        {"name": "BMI", "code": "bmi", "gender": "female", "type": "bmi"},
        {"name": "肺活量", "code": "lung", "gender": "male", "type": "normal"},
        {"name": "肺活量", "code": "lung", "gender": "female", "type": "normal"},
        {"name": "50米跑", "code": "sprint", "gender": "male", "type": "time"},
        {"name": "50米跑", "code": "sprint", "gender": "female", "type": "time"},
        {"name": "坐位体前屈", "code": "sit", "gender": "male", "type": "normal"},
        {"name": "坐位体前屈", "code": "sit", "gender": "female", "type": "normal"},
        {"name": "1分钟跳绳", "code": "rope", "gender": "male", "type": "normal"},
        {"name": "1分钟跳绳", "code": "rope", "gender": "female", "type": "normal"},
        {"name": "1分钟仰卧起坐", "code": "sit_up", "gender": "female", "type": "normal"}, # Only female? Or only certain grades? The docx has them.
        {"name": "引体向上", "code": "pull_up", "gender": "male", "type": "normal"},
        {"name": "50米×8往返跑", "code": "run_50x8", "gender": "male", "type": "time"},
        {"name": "50米×8往返跑", "code": "run_50x8", "gender": "female", "type": "time"},
        {"name": "1000米跑", "code": "run_1000", "gender": "male", "type": "time"},
        {"name": "800米跑", "code": "run_800", "gender": "female", "type": "time"}
    ]
    
    stages = [
        {'id': '@primary_id', 'code': 'primary', 'name': '国家学生体质健康测试（小学）', 'grades': ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']},
        {'id': '@mid_id', 'code': 'mid', 'name': '国家学生体质健康测试（初中）', 'grades': ['初一', '初二', '初三']},
        {'id': '@high_id', 'code': 'high', 'name': '国家学生体质健康测试（高中）', 'grades': ['高一', '高二', '高三']},
        {'id': '@univ_id', 'code': 'university', 'name': '国家学生体质健康测试（大学）', 'grades': ['大学']}
    ]

    sql_lines = []
    sql_lines.append("SET NAMES utf8mb4;")
    sql_lines.append("SET FOREIGN_KEY_CHECKS = 0;")
    sql_lines.append("")
    
    for stage in stages:
        sql_lines.append(f"INSERT INTO `vadmin_pef_standard` (`biz_type`, `name`, `region`, `year`, `stage_type`, `version`, `status`, `conflict_policy`, `remark`)")
        sql_lines.append(f"VALUES ('fitness', '{stage['name']}', '全国', 2026, '{stage['code']}', 'V2014-国测', 'published', 'lower_priority', '国测标准2014版修订');")
        sql_lines.append(f"SET {stage['id']} = LAST_INSERT_ID();")
        sql_lines.append("")

    sort_idx = 1
    
    for table_idx, tbl in enumerate(tables):
        if table_idx >= len(table_metadata):
            continue
        meta = table_metadata[table_idx]
        
        headers = tbl[0]
        grade_cols = {}
        for c_idx, h in enumerate(headers):
            for stage in stages:
                if h in stage['grades']:
                    grade_cols.setdefault(stage['code'], []).append({'col': c_idx, 'grade': h})
        
        # Process rows into scores
        parsed_data = {}
        for r_idx in range(1, len(tbl)):
            row = tbl[r_idx]
            # Grade is in col 0, score in col 1 (or empty for BMI)
            grade_level = row[0]
            score_str = row[1] if len(row)>1 else ""
            
            for stage_code, cols in grade_cols.items():
                parsed_data.setdefault(stage_code, {})
                for col_info in cols:
                    c_idx = col_info['col']
                    if c_idx < len(row):
                        cell_val = row[c_idx]
                        if cell_val:
                            parsed_data[stage_code].setdefault(col_info['grade'], []).append({
                                'level': grade_level,
                                'score': score_str,
                                'val': cell_val
                            })
        
        # Now generate standard items for each stage
        for stage in stages:
            stage_code = stage['code']
            if stage_code not in parsed_data or not parsed_data[stage_code]:
                continue
            
            # Combine grade data into JSON segment
            segment_json = []
            for grade, rules in parsed_data[stage_code].items():
                grade_segments = []
                for rule in rules:
                    grade_segments.append({
                        'level': rule['level'],
                        'score': rule['score'],
                        'range': rule['val']
                    })
                segment_json.append({
                    'grade': grade,
                    'rules': grade_segments
                })
            
            json_str = json.dumps(segment_json, ensure_ascii=False)
            json_str_sql = json_str.replace('\\', '\\\\').replace("'", "''")
            
            # Calculate threshold (simplified logic, just take pass score from the first rule usually)
            # In actual system, segment_json will be parsed by RuleEngine
            sql_lines.append(f"INSERT INTO `vadmin_pef_standard_item` ")
            sql_lines.append(f"(`standard_id`, `item_code`, `item_name`, `gender`, `calc_mode`, `pass_threshold`, `excellent_threshold`, `full_threshold`, `segment_json`, `is_required`, `is_gate_item`, `max_score`, `sort`)")
            sql_lines.append(f"VALUES ({stage['id']}, '{meta['code']}', '{meta['name']}', '{meta['gender']}', 'segment', 60, 80, 100, '{json_str_sql}', 1, 0, 100, {sort_idx});")
            sort_idx += 1

    with open('../docs/db/20260407_national_fitness_standards.sql', 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_lines))
    print("SQL generated successfully.")

if __name__ == '__main__':
    generate_sql()
