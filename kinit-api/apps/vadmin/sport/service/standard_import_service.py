#!/usr/bin/python
# -*- coding: utf-8 -*-

from openpyxl import load_workbook
from typing import List, Dict, Any
import io

class StandardImportService:
    @staticmethod
    def parse_standard_excel(file_content: bytes) -> List[Dict[str, Any]]:
        """
        解析评分标准 Excel 文件
        结构示例：
        项目名称 | 项目编码 | 性别 | 计分模式 | 满分阈值 | 优秀阈值 | 及格阈值 | 满分分值
        """
        wb = load_workbook(filename=io.BytesIO(file_content), data_only=True)
        sheet = wb.active
        items = []
        
        # 简单解析逻辑：假设第一行为表头，从第二行开始
        rows = list(sheet.rows)
        if len(rows) < 2:
            return []
            
        # 表头映射（根据实际模板调整）
        for row in rows[1:]:
            if not row[0].value:
                continue
            item = {
                'item_name': str(row[0].value),
                'item_code': str(row[1].value) if row[1].value else '',
                'gender': str(row[2].value) if row[2].value else 'all',
                'calc_mode': str(row[3].value) if row[3].value else 'threshold',
                'full_threshold': row[4].value,
                'excellent_threshold': row[5].value,
                'pass_threshold': row[6].value,
                'max_score': row[7].value if len(row) > 7 else 0,
                'is_required': True
            }
            items.append(item)
            
        return items
