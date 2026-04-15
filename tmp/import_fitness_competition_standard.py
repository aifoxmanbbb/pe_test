#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pymysql

sys.path.insert(0, r"D:\workspace_other\pe_test\kinit-api")
from application.config.production import MYSQL_DB, MYSQL_HOST, MYSQL_PASSWORD, MYSQL_PORT, MYSQL_USER

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TMP_DIR = Path(r"D:\workspace_other\pe_test\tmp")
DOCX_PATH = next(TMP_DIR.glob("*初一至高三*.docx"))
VERSION = "V2026-达标赛"
YEAR = 2026
REGION = "全国"
REMARK = f"由文档《{DOCX_PATH.name}》导入"

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

STAGE_CONFIG = {
    "mid": {
        "name": "学生体质健康达标比赛评分标准（初中）",
        "grades": ["初一", "初二", "初三"],
    },
    "high": {
        "name": "学生体质健康达标比赛评分标准（高中）",
        "grades": ["高一", "高二", "高三"],
    },
}

TABLE_SPECS = [
    {"table_index": 0, "items": [{"item_code": "bmi", "item_name": "BMI", "gender": "male"}, {"item_code": "bmi", "item_name": "BMI", "gender": "female"}]},
    {"table_index": 1, "items": [{"item_code": "lung", "item_name": "肺活量", "gender": "male"}, {"item_code": "lung", "item_name": "肺活量", "gender": "female"}]},
    {"table_index": 2, "items": [{"item_code": "sprint", "item_name": "50米跑", "gender": "male"}, {"item_code": "sprint", "item_name": "50米跑", "gender": "female"}]},
    {"table_index": 3, "items": [{"item_code": "sit", "item_name": "坐位体前屈", "gender": "male"}, {"item_code": "sit", "item_name": "坐位体前屈", "gender": "female"}]},
    {"table_index": 4, "items": [{"item_code": "jump", "item_name": "立定跳远", "gender": "male"}, {"item_code": "jump", "item_name": "立定跳远", "gender": "female"}]},
    {"table_index": 5, "items": [{"item_code": "pull_up", "item_name": "引体向上", "gender": "male"}, {"item_code": "sit_up", "item_name": "1分钟仰卧起坐", "gender": "female"}]},
    {"table_index": 6, "items": [{"item_code": "run_1000", "item_name": "1000米跑", "gender": "male"}, {"item_code": "run_800", "item_name": "800米跑", "gender": "female"}]},
]


def get_text(node: ET.Element) -> str:
    texts = []
    for text_node in node.findall(".//w:t", NS):
        if text_node.text:
            texts.append(text_node.text)
    return "".join(texts).strip()


def parse_docx_tables(docx_path: Path) -> list[list[list[str]]]:
    with zipfile.ZipFile(docx_path) as docx:
        root = ET.fromstring(docx.read("word/document.xml"))

    tables: list[list[list[str]]] = []
    for tbl in root.findall(".//w:tbl", NS):
        rows: list[list[str]] = []
        for tr in tbl.findall("./w:tr", NS):
            row: list[str] = []
            for tc in tr.findall("./w:tc", NS):
                row.append(get_text(tc))
            rows.append(row)
        tables.append(rows)
    return tables


def normalize_score(score_text: str) -> str:
    score_text = str(score_text or "").strip()
    if score_text == "":
        return "0"
    return score_text


def build_header_map(header_row: list[str]) -> dict[tuple[str, str], int]:
    mapping: dict[tuple[str, str], int] = {}
    for idx, cell in enumerate(header_row):
        text = str(cell or "").strip()
        if not text or "(" not in text or ")" not in text:
            continue
        grade, gender_text = text.split("(", 1)
        grade = grade.strip()
        gender_text = gender_text.replace(")", "").strip()
        gender = "male" if gender_text == "男" else "female" if gender_text == "女" else ""
        if grade and gender:
            mapping[(grade, gender)] = idx
    return mapping


def build_segment_rows(table_rows: list[list[str]], gender: str, stage_grades: list[str]) -> list[dict]:
    header_map = build_header_map(table_rows[1])
    segments: list[dict] = []
    for grade in stage_grades:
        col_idx = header_map.get((grade, gender))
        if col_idx is None:
            continue
        rules: list[dict] = []
        for row in table_rows[2:]:
            if col_idx >= len(row):
                continue
            range_text = str(row[col_idx] or "").strip()
            if not range_text:
                continue
            rules.append({
                "level": str(row[0] or "").strip(),
                "range": range_text,
                "score": normalize_score(row[1] if len(row) > 1 else ""),
                "weight_score": str(row[-1] or "").strip() if row else "",
            })
        segments.append({"grade": grade, "rules": rules})
    return segments


def build_payload(tables: list[list[list[str]]]) -> dict[str, list[dict]]:
    stage_items: dict[str, list[dict]] = {"mid": [], "high": []}
    sort_map = {"mid": 1, "high": 1}

    for spec in TABLE_SPECS:
        rows = tables[spec["table_index"]]
        for item in spec["items"]:
            for stage_type, cfg in STAGE_CONFIG.items():
                segments = build_segment_rows(rows, item["gender"], cfg["grades"])
                if not segments:
                    continue
                stage_items[stage_type].append({
                    "item_code": item["item_code"],
                    "item_name": item["item_name"],
                    "gender": item["gender"],
                    "calc_mode": "segment",
                    "pass_threshold": 60,
                    "excellent_threshold": 80,
                    "full_threshold": 100,
                    "segment_json": segments,
                    "is_required": 1,
                    "is_gate_item": 0,
                    "max_score": 100,
                    "sort": sort_map[stage_type],
                })
                sort_map[stage_type] += 1
    return stage_items


def upsert_standard(cur, stage_type: str, items: list[dict]) -> int:
    cfg = STAGE_CONFIG[stage_type]
    cur.execute(
        """
        SELECT id
        FROM vadmin_pef_standard
        WHERE biz_type='fitness' AND stage_type=%s AND name=%s AND version=%s AND is_delete=0
        ORDER BY id DESC
        LIMIT 1
        """,
        (stage_type, cfg["name"], VERSION),
    )
    row = cur.fetchone()

    if row:
        standard_id = row[0]
        cur.execute(
            """
            UPDATE vadmin_pef_standard
            SET region=%s, year=%s, status='published', source_type='docx', conflict_policy='lower_priority', remark=%s
            WHERE id=%s
            """,
            (REGION, YEAR, REMARK, standard_id),
        )
        cur.execute("DELETE FROM vadmin_pef_standard_item WHERE standard_id=%s", (standard_id,))
    else:
        cur.execute(
            """
            INSERT INTO vadmin_pef_standard
            (biz_type, name, region, year, stage_type, version, status, source_type, conflict_policy, remark, is_delete)
            VALUES ('fitness', %s, %s, %s, %s, %s, 'published', 'docx', 'lower_priority', %s, 0)
            """,
            (cfg["name"], REGION, YEAR, stage_type, VERSION, REMARK),
        )
        standard_id = cur.lastrowid

    for item in items:
        cur.execute(
            """
            INSERT INTO vadmin_pef_standard_item
            (standard_id, item_code, item_name, gender, calc_mode, pass_threshold, excellent_threshold, full_threshold,
             segment_json, is_required, is_gate_item, max_score, sort, is_delete)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
            """,
            (
                standard_id,
                item["item_code"],
                item["item_name"],
                item["gender"],
                item["calc_mode"],
                item["pass_threshold"],
                item["excellent_threshold"],
                item["full_threshold"],
                json.dumps(item["segment_json"], ensure_ascii=False),
                item["is_required"],
                item["is_gate_item"],
                item["max_score"],
                item["sort"],
            ),
        )
    return standard_id


def main() -> None:
    if not DOCX_PATH.exists():
        raise FileNotFoundError(f"docx not found: {DOCX_PATH}")

    tables = parse_docx_tables(DOCX_PATH)
    if len(tables) != 7:
        raise RuntimeError(f"unexpected table count: {len(tables)}")

    stage_items = build_payload(tables)
    preview_path = DOCX_PATH.with_suffix(".import.preview.json")
    preview_path.write_text(json.dumps(stage_items, ensure_ascii=False, indent=2), encoding="utf-8")

    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=int(MYSQL_PORT),
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        charset="utf8mb4",
        autocommit=False,
    )
    try:
        with conn.cursor() as cur:
            result = {}
            for stage_type in ("mid", "high"):
                result[stage_type] = {
                    "standard_id": upsert_standard(cur, stage_type, stage_items[stage_type]),
                    "item_count": len(stage_items[stage_type]),
                }
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print(json.dumps({
        "docx": str(DOCX_PATH),
        "preview": str(preview_path),
        "version": VERSION,
        "result": result,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
