#!/usr/bin/python
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any


@dataclass
class ScoreContext:
    biz_type: str
    stage_type: str
    gender: str
    item_code: str
    raw_value: float


class RuleEngine:
    """
    体考/体测统一评分引擎（基础版）

    支持：
    1. threshold 模式：按及格/优秀/满分阈值判定
    2. segment 模式：按分值段映射成绩 -> 分值
    """

    @staticmethod
    def eval_by_threshold(raw_value: float, threshold: dict[str, Any]) -> dict[str, Any]:
        pass_v = float(threshold.get('pass', 0))
        excellent_v = float(threshold.get('excellent', 0))
        full_v = float(threshold.get('full', 0))

        is_pass = raw_value >= pass_v
        is_excellent = raw_value >= excellent_v
        is_full = raw_value >= full_v

        level = '不及格'
        if is_full:
            level = '满分'
        elif is_excellent:
            level = '优秀'
        elif is_pass:
            level = '及格'

        return {
            'score_value': raw_value,
            'is_pass': is_pass,
            'is_excellent': is_excellent,
            'is_full': is_full,
            'level': level
        }

    @staticmethod
    def eval_by_segment(raw_value: float, segments: list[dict[str, Any]], conflict_policy: str = 'lower_priority') -> dict[str, Any]:
        """
        segments 样例：
        [
          {"min": 185, "max": 999, "score": 20},
          {"min": 170, "max": 184.99, "score": 18}
        ]
        """
        matched: list[dict[str, Any]] = []
        for item in segments:
            min_v = float(item.get('min', float('-inf')))
            max_v = float(item.get('max', float('inf')))
            if min_v <= raw_value <= max_v:
                matched.append(item)

        if not matched:
            return {
                'score_value': 0,
                'is_pass': False,
                'is_excellent': False,
                'is_full': False,
                'level': '不及格'
            }

        scores = [float(m.get('score', 0)) for m in matched]
        score_value = min(scores) if conflict_policy == 'lower_priority' else max(scores)

        return {
            'score_value': score_value,
            'is_pass': score_value >= 60,
            'is_excellent': score_value >= 80,
            'is_full': score_value >= 100,
            'level': '满分' if score_value >= 100 else ('优秀' if score_value >= 80 else ('及格' if score_value >= 60 else '不及格'))
        }

