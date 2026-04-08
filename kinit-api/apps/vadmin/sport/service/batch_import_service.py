#!/usr/bin/python
# -*- coding: utf-8 -*-

from openpyxl import load_workbook
from typing import List, Dict, Any
import io

class BatchImportService:
    @staticmethod
    def parse_score_excel(file_content: bytes) -> List[Dict[str, Any]]:
        """
        解析成绩导入 Excel 文件
        结构示例：
        学号 | 姓名 | 性别 | 学校 | 年级 | 班级 | 项目编码 | 项目名称 | 成绩
        """
        wb = load_workbook(filename=io.BytesIO(file_content), data_only=True)
        sheet = wb.active
        scores = []
        
        rows = list(sheet.rows)
        if len(rows) < 2:
            return []
            
        for row in rows[1:]:
            if not row[0].value:
                continue
            score = {
                'student_no': str(row[0].value),
                'student_name': str(row[1].value),
                'gender': str(row[2].value),
                'school_name': str(row[3].value),
                'grade_name': str(row[4].value),
                'class_name': str(row[5].value),
                'item_code': str(row[6].value),
                'item_name': str(row[7].value),
                'raw_score': row[8].value
            }
            scores.append(score)
            
        return scores
