#!/usr/bin/python
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any
import re

@dataclass
class ScoreContext:
    biz_type: str
    stage_type: str
    gender: str
    item_code: str
    raw_value: float


class RuleEngine:
    """
    体考/体测统一评分引擎
    """

    @staticmethod
    def parse_time_to_seconds(text: str) -> float | None:
        """
        统一解析时间格式为秒数
        支持: 3'20", 3'20, 3分20秒, 200.5
        """
        if text is None: return None
        text = str(text).strip()
        if not text: return None
        
        # 1. 尝试匹配 分'秒" 或 分'秒
        m = re.match(r'^(\d+)[\'|分]\s*(\d+(?:\.\d+)?)[\"|秒]?$', text)
        if m:
            return float(m.group(1)) * 60 + float(m.group(2))
        
        # 2. 尝试匹配 纯秒数 (如 12.5)
        if re.fullmatch(r'\d+(\.\d+)?', text):
            return float(text)
            
        return None

    @staticmethod
    def _parse_range(range_str: str) -> dict[str, float]:
        """
        解析区间字符串，如 '13.5~18.1', '≤13.4', '≥20.4', '4\'32"'
        """
        range_str = str(range_str).strip()
        if not range_str:
            return {}

        # 处理时间格式的区间，如 "4'32\"~5'10\""
        if '~' in range_str:
            parts = range_str.split('~')
            v1 = RuleEngine.parse_time_to_seconds(parts[0])
            v2 = RuleEngine.parse_time_to_seconds(parts[1])
            if v1 is not None and v2 is not None:
                return {'min': min(v1, v2), 'max': max(v1, v2)}
        
        # 处理带比较符的
        for symbol in ['≤', '<=', '≥', '>=']:
            if range_str.startswith(symbol):
                v = RuleEngine.parse_time_to_seconds(range_str.replace(symbol, ''))
                if v is not None:
                    return {'max' if '≤' in symbol or '<' in symbol else 'min': v}
        
        # 处理单值 (可能是阈值)
        v = RuleEngine.parse_time_to_seconds(range_str)
        if v is not None:
            return {'exact': v}
            
        return {}

    @staticmethod
    def eval_by_threshold(raw_value: float, threshold: dict[str, Any]) -> dict[str, Any]:
        pass_v = float(threshold.get('pass', 0))
        excellent_v = float(threshold.get('excellent', 0))
        full_v = float(threshold.get('full', 0))

        # 简单的逻辑：默认分值越大越好，除非 full < pass
        is_lower_better = full_v > 0 and full_v < pass_v
        
        if is_lower_better:
            is_pass = raw_value <= pass_v
            is_excellent = raw_value <= excellent_v
            is_full = raw_value <= full_v
        else:
            is_pass = raw_value >= pass_v
            is_excellent = raw_value >= excellent_v
            is_full = raw_value >= full_v

        return {
            'score_value': raw_value,
            'is_pass': is_pass,
            'is_excellent': is_excellent,
            'is_full': is_full
        }

    @staticmethod
    def eval_by_segment(raw_value: float, segments: list[dict[str, Any]], grade_name: str = '', conflict_policy: str = 'lower_priority') -> dict[str, Any]:
        """
        通用分段计分
        """
        if not segments:
            return {}

        # 1. 预处理：如果是按年级划分的复杂格式
        target_rules = []
        if 'grade' in segments[0]:
            for seg in segments:
                if seg.get('grade') in grade_name or grade_name in str(seg.get('grade')):
                    target_rules = seg.get('rules', [])
                    break
            if not target_rules:
                target_rules = segments[0].get('rules', []) # 找不到匹配年级则默认取第一个
        else:
            target_rules = segments

        # 2. 匹配规则
        matched_scores = []
        
        # 判断是分值越高成绩越好，还是越低越好 (通常跑类成绩越小得分越高)
        # 通过采样前两条规则判定
        is_lower_better = False
        if len(target_rules) >= 2:
            r1 = target_rules[0]
            r2 = target_rules[1]
            v1 = RuleEngine.parse_time_to_seconds(r1.get('range', ''))
            v2 = RuleEngine.parse_time_to_seconds(r2.get('range', ''))
            s1 = float(r1.get('score', 0))
            s2 = float(r2.get('score', 0))
            if v1 is not None and v2 is not None:
                if (s1 > s2 and v1 < v2) or (s1 < s2 and v1 > v2):
                    is_lower_better = True

        for rule in target_rules:
            range_info = RuleEngine._parse_range(rule.get('range', ''))
            if not range_info: continue
            
            match = False
            if 'exact' in range_info:
                # 如果是单值，视为阈值
                if is_lower_better:
                    if raw_value <= range_info['exact']: match = True
                else:
                    if raw_value >= range_info['exact']: match = True
            else:
                v_min = range_info.get('min', float('-inf'))
                v_max = range_info.get('max', float('inf'))
                if v_min <= raw_value <= v_max:
                    match = True
            
            if match:
                matched_scores.append(float(rule.get('score', 0)))

        if not matched_scores:
            return {'score_value': 0, 'is_pass': False, 'is_excellent': False, 'is_full': False}

        # 取最高分 (通常计分逻辑是只要达到这个线就拿这个分)
        final_score = max(matched_scores)
        
        return {
            'score_value': final_score,
            'is_pass': final_score >= 60, # 这里的及格线通常针对100分制
            'is_excellent': final_score >= 80,
            'is_full': final_score >= 100
        }
