#!/usr/bin/python
# -*- coding: utf-8 -*-

from openpyxl import load_workbook
from typing import List, Dict, Any
import io
from types import SimpleNamespace
from sqlalchemy import select, false
from xlsxwriter.utility import xl_col_to_name
from apps.vadmin.sport.models import (
    VadminPefClass,
    VadminPefGrade,
    VadminPefSchool,
    VadminPefStudent,
    VadminSportBatch,
    VadminSportStandardItem
)
from apps.vadmin.sport.service.rule_engine import RuleEngine
from apps.vadmin.sport.service.scope_service import match_scope_by_name

class BatchImportService:
    SCORE_HEADERS = [
        ("学号", "student_no"),
        ("姓名", "student_name"),
        ("性别", "gender"),
        ("学校", "school_name"),
        ("年级", "grade_name"),
        ("班级", "class_name"),
        ("项目名称", "item_name"),
        ("成绩", "raw_score")
    ]
    SCORE_REQUIRED_LABELS = {label for label, _ in SCORE_HEADERS}
    UNLIMITED_VALUES = {'', '*', 'all', '全部', '不限', '不区分', '全校', '全部学校', '全年级', '全部年级', '全部班级'}
    FITNESS_REMOVED_ITEM_CODES = {'run_50x8'}
    FITNESS_REMOVED_ITEM_NAMES = {'50米×8往返跑', '50米x8往返跑', '50x8往返跑'}
    FITNESS_VIRTUAL_ITEMS = [
        {"item_code": "height", "item_name": "身高", "gender": "all", "calc_mode": "record", "sort": -2},
        {"item_code": "weight", "item_name": "体重", "gender": "all", "calc_mode": "record", "sort": -1}
    ]

    @staticmethod
    def _clean_cell(value) -> str:
        if value is None:
            return ''
        text = str(value).strip()
        if text.endswith('.0') and text[:-2].isdigit():
            return text[:-2]
        return text

    @staticmethod
    def _normalize_header(value) -> str:
        text = BatchImportService._clean_cell(value)
        return text.replace('*', '').replace(' ', '').replace('\u3000', '')

    @staticmethod
    def _is_unlimited(value) -> bool:
        return BatchImportService._clean_cell(value).lower() in BatchImportService.UNLIMITED_VALUES

    @staticmethod
    def _normalize_gender(value) -> str:
        text = BatchImportService._clean_cell(value).lower()
        if text in {'male', 'm', '1', '男', 'Ã§â€Â·'}:
            return 'male'
        if text in {'female', 'f', '0', '2', '女', 'Ã¥Â¥Â³'}:
            return 'female'
        return 'all'

    @staticmethod
    def _option_list(values: list[str]) -> list[dict[str, str]]:
        result: list[dict[str, str]] = []
        seen: set[str] = set()
        for value in values:
            text = BatchImportService._clean_cell(value)
            if text and text not in seen:
                seen.add(text)
                result.append({"label": text, "value": text})
        return result

    @staticmethod
    def is_removed_fitness_item(item) -> bool:
        code = BatchImportService._clean_cell(getattr(item, "item_code", "")).lower()
        name = BatchImportService._clean_cell(getattr(item, "item_name", ""))
        return code in BatchImportService.FITNESS_REMOVED_ITEM_CODES or name in BatchImportService.FITNESS_REMOVED_ITEM_NAMES

    @staticmethod
    def normalize_standard_items(biz_type: str, standard_id: int | None, items: list) -> list:
        normalized = list(items or [])
        if biz_type != 'fitness':
            return normalized

        normalized = [item for item in normalized if not BatchImportService.is_removed_fitness_item(item)]
        existing_codes = {
            BatchImportService._clean_cell(getattr(item, "item_code", "")).lower()
            for item in normalized
        }
        for virtual_item in BatchImportService.FITNESS_VIRTUAL_ITEMS:
            if virtual_item["item_code"] in existing_codes:
                continue
            normalized.append(SimpleNamespace(
                standard_id=standard_id,
                item_code=virtual_item["item_code"],
                item_name=virtual_item["item_name"],
                gender=virtual_item["gender"],
                calc_mode=virtual_item["calc_mode"],
                pass_threshold=None,
                excellent_threshold=None,
                full_threshold=None,
                segment_json=[],
                is_required=True,
                is_gate_item=False,
                max_score=0,
                sort=virtual_item["sort"]
            ))
        return sorted(normalized, key=lambda item: (getattr(item, "sort", 0) or 0, getattr(item, "id", 0) or 0))

    @staticmethod
    def _score_template_headers() -> list[dict]:
        return [
            {"label": label, "field": field, "required": True}
            for label, field in BatchImportService.SCORE_HEADERS
        ]

    @staticmethod
    def format_score_errors(errors: list[str]) -> str:
        if not errors:
            return ""
        visible_errors = errors[:30]
        suffix = f"；另有 {len(errors) - len(visible_errors)} 条错误" if len(errors) > len(visible_errors) else ""
        return f"导入校验失败：{'；'.join(visible_errors)}{suffix}"

    @staticmethod
    def _in_batch_scope(batch: VadminSportBatch, school_name: str, grade_name: str, class_name: str) -> bool:
        return (
            (BatchImportService._is_unlimited(batch.school_name) or batch.school_name == school_name)
            and (BatchImportService._is_unlimited(batch.grade_name) or batch.grade_name == grade_name)
            and (BatchImportService._is_unlimited(batch.class_name) or batch.class_name == class_name)
        )

    @staticmethod
    async def _load_scope_rows(db, auth, batch: VadminSportBatch) -> list[tuple[str, str, str]]:
        rows = (await db.execute(
            select(VadminPefSchool.school_name, VadminPefGrade.grade_name, VadminPefClass.class_name)
            .select_from(VadminPefClass)
            .join(VadminPefGrade, VadminPefClass.grade_id == VadminPefGrade.id)
            .join(VadminPefSchool, VadminPefClass.school_id == VadminPefSchool.id)
            .where(
                VadminPefSchool.is_delete == false(),
                VadminPefGrade.is_delete == false(),
                VadminPefClass.is_delete == false(),
                VadminPefSchool.is_active == True,
                VadminPefGrade.is_active == True,
                VadminPefClass.is_active == True
            )
            .order_by(VadminPefSchool.sort.asc(), VadminPefGrade.sort.asc(), VadminPefClass.sort.asc())
        )).all()
        result: list[tuple[str, str, str]] = []
        for school_name, grade_name, class_name in rows:
            school = BatchImportService._clean_cell(school_name)
            grade = BatchImportService._clean_cell(grade_name)
            cls = BatchImportService._clean_cell(class_name)
            if not BatchImportService._in_batch_scope(batch, school, grade, cls):
                continue
            if not match_scope_by_name(auth, school, cls):
                continue
            result.append((school, grade, cls))
        return result

    @staticmethod
    def _build_scope_option_maps(scope_rows: list[tuple[str, str, str]]) -> dict[str, Any]:
        schools: list[str] = []
        grades_by_school: dict[str, list[str]] = {}
        classes_by_school_grade: dict[str, list[str]] = {}
        for school, grade, cls in scope_rows:
            if school not in schools:
                schools.append(school)
            grades_by_school.setdefault(school, [])
            if grade not in grades_by_school[school]:
                grades_by_school[school].append(grade)
            key = f"{school}|{grade}"
            classes_by_school_grade.setdefault(key, [])
            if cls not in classes_by_school_grade[key]:
                classes_by_school_grade[key].append(cls)
        return {
            "schools": schools,
            "grades_by_school": grades_by_school,
            "classes_by_school_grade": classes_by_school_grade
        }

    @staticmethod
    def apply_score_template_validations(writer, options: dict[str, Any], max_row: int = 1000) -> None:
        if not writer or not writer.wb or not writer.sheet:
            return
        wb = writer.wb
        sheet = writer.sheet
        option_sheet = wb.add_worksheet("_score_options")
        option_sheet.hide()

        def write_column(col: int, values: list[str]) -> str | None:
            clean_values: list[str] = []
            seen_values: set[str] = set()
            for item in values:
                value = BatchImportService._clean_cell(item)
                if value and value not in seen_values:
                    seen_values.add(value)
                    clean_values.append(value)
            for row_idx, value in enumerate(clean_values):
                option_sheet.write(row_idx, col, value)
            if not clean_values:
                return None
            col_name = xl_col_to_name(col)
            return f"='_score_options'!${col_name}$1:${col_name}${len(clean_values)}"

        school_source = write_column(0, options.get("schools") or [])
        student_no_source = write_column(2, options.get("student_nos") or [])
        student_name_source = write_column(3, options.get("student_names") or [])
        gender_source = write_column(4, ["男", "女"])
        item_name_source = write_column(6, options.get("item_names") or [])

        if student_no_source:
            sheet.data_validation(1, 0, max_row, 0, {'validate': 'list', 'source': student_no_source})
        if student_name_source:
            sheet.data_validation(1, 1, max_row, 1, {'validate': 'list', 'source': student_name_source})
        if gender_source:
            sheet.data_validation(1, 2, max_row, 2, {'validate': 'list', 'source': gender_source})
        if school_source:
            sheet.data_validation(1, 3, max_row, 3, {'validate': 'list', 'source': school_source})
        if item_name_source:
            sheet.data_validation(1, 6, max_row, 6, {'validate': 'list', 'source': item_name_source})

        grade_start_col = 10
        schools = options.get("schools") or []
        grades_by_school = options.get("grades_by_school") or {}
        for index, school in enumerate(schools):
            col = grade_start_col + index
            option_sheet.write(0, col, school)
            for row_idx, grade in enumerate(grades_by_school.get(school) or [], start=1):
                option_sheet.write(row_idx, col, grade)
        if schools:
            start_col = xl_col_to_name(grade_start_col)
            end_col = xl_col_to_name(grade_start_col + len(schools) - 1)
            grade_formula = (
                f"=OFFSET('_score_options'!${start_col}$2,0,"
                f"MATCH($D2,'_score_options'!${start_col}$1:${end_col}$1,0)-1,"
                f"COUNTA(OFFSET('_score_options'!${start_col}$2:${start_col}$1000,0,"
                f"MATCH($D2,'_score_options'!${start_col}$1:${end_col}$1,0)-1)),1)"
            )
            sheet.data_validation(1, 4, max_row, 4, {'validate': 'list', 'source': grade_formula})

        class_start_col = 80
        class_keys = list((options.get("classes_by_school_grade") or {}).keys())
        classes_by_school_grade = options.get("classes_by_school_grade") or {}
        for index, key in enumerate(class_keys):
            col = class_start_col + index
            option_sheet.write(0, col, key)
            for row_idx, cls in enumerate(classes_by_school_grade.get(key) or [], start=1):
                option_sheet.write(row_idx, col, cls)
        if class_keys:
            start_col = xl_col_to_name(class_start_col)
            end_col = xl_col_to_name(class_start_col + len(class_keys) - 1)
            class_formula = (
                f"=OFFSET('_score_options'!${start_col}$2,0,"
                f"MATCH($D2&\"|\"&$E2,'_score_options'!${start_col}$1:${end_col}$1,0)-1,"
                f"COUNTA(OFFSET('_score_options'!${start_col}$2:${start_col}$1000,0,"
                f"MATCH($D2&\"|\"&$E2,'_score_options'!${start_col}$1:${end_col}$1,0)-1)),1)"
            )
            sheet.data_validation(1, 5, max_row, 5, {'validate': 'list', 'source': class_formula})

    @staticmethod
    async def _load_batch(db, auth, biz_type: str, batch_id: int | None) -> VadminSportBatch:
        if not batch_id:
            raise ValueError("请先选择批次")
        batch = await db.scalar(select(VadminSportBatch).where(
            VadminSportBatch.id == batch_id,
            VadminSportBatch.biz_type == biz_type,
            VadminSportBatch.is_delete == false()
        ))
        if not batch:
            raise ValueError("批次不存在")
        if (
            not (BatchImportService._is_unlimited(batch.school_name) and BatchImportService._is_unlimited(batch.class_name))
            and not match_scope_by_name(auth, batch.school_name, batch.class_name)
        ):
            raise ValueError("无权限操作该批次")
        return batch

    @staticmethod
    async def build_score_template_config(db, auth, biz_type: str, batch_id: int | None) -> tuple[list[dict], dict[str, Any]]:
        batch = await BatchImportService._load_batch(db, auth, biz_type, batch_id)
        headers = BatchImportService._score_template_headers()
        scope_rows = await BatchImportService._load_scope_rows(db, auth, batch)
        scope_options = BatchImportService._build_scope_option_maps(scope_rows)
        student_rows = (await db.execute(
            select(VadminPefStudent, VadminPefSchool.school_name, VadminPefGrade.grade_name, VadminPefClass.class_name)
            .select_from(VadminPefStudent)
            .join(VadminPefSchool, VadminPefStudent.school_id == VadminPefSchool.id)
            .join(VadminPefGrade, VadminPefStudent.grade_id == VadminPefGrade.id)
            .join(VadminPefClass, VadminPefStudent.class_id == VadminPefClass.id)
            .where(
                VadminPefStudent.is_delete == false(),
                VadminPefSchool.is_delete == false(),
                VadminPefGrade.is_delete == false(),
                VadminPefClass.is_delete == false()
            )
            .order_by(VadminPefStudent.student_no.asc())
        )).all()
        standard_items = (await db.scalars(select(VadminSportStandardItem).where(
            VadminSportStandardItem.standard_id == batch.standard_id,
            VadminSportStandardItem.is_delete == false()
        ).order_by(VadminSportStandardItem.sort.asc(), VadminSportStandardItem.id.asc()))).all()
        standard_items = BatchImportService.normalize_standard_items(biz_type, batch.standard_id, standard_items)

        scoped_student_rows = [
            row for row in student_rows
            if BatchImportService._in_batch_scope(batch, row[1], row[2], row[3])
            and match_scope_by_name(auth, row[1], row[3])
        ]
        students = [row[0] for row in scoped_student_rows]
        options = {
            **scope_options,
            "student_nos": [item.student_no for item in students],
            "student_names": [item.name for item in students],
            "item_names": [item.item_name for item in standard_items]
        }
        return headers, options

    @staticmethod
    async def build_score_template_headers(db, auth, biz_type: str, batch_id: int | None) -> list[dict]:
        headers, _ = await BatchImportService.build_score_template_config(db, auth, biz_type, batch_id)
        return headers

    @staticmethod
    async def validate_score_rows(db, auth, biz_type: str, batch_id: int | None, scores: list[dict]) -> tuple[VadminSportBatch, list[dict], list[str]]:
        batch = await BatchImportService._load_batch(db, auth, biz_type, batch_id)
        student_rows = (await db.execute(
            select(VadminPefStudent, VadminPefSchool.school_name, VadminPefGrade.grade_name, VadminPefClass.class_name)
            .select_from(VadminPefStudent)
            .join(VadminPefSchool, VadminPefStudent.school_id == VadminPefSchool.id)
            .join(VadminPefGrade, VadminPefStudent.grade_id == VadminPefGrade.id)
            .join(VadminPefClass, VadminPefStudent.class_id == VadminPefClass.id)
            .where(
                VadminPefStudent.is_delete == false(),
                VadminPefSchool.is_delete == false(),
                VadminPefGrade.is_delete == false(),
                VadminPefClass.is_delete == false()
            )
        )).all()
        student_map = {BatchImportService._clean_cell(row[0].student_no): row for row in student_rows}
        standard_items = (await db.scalars(select(VadminSportStandardItem).where(
            VadminSportStandardItem.standard_id == batch.standard_id,
            VadminSportStandardItem.is_delete == false()
        ))).all()
        standard_items = BatchImportService.normalize_standard_items(biz_type, batch.standard_id, standard_items)
        item_name_map: dict[str, list[VadminSportStandardItem]] = {}
        for item in standard_items:
            item_name_map.setdefault(BatchImportService._clean_cell(item.item_name), []).append(item)

        errors: list[str] = []
        normalized_scores: list[dict] = []
        for index, score in enumerate(scores, start=1):
            row_number = score.get("_row_number") or (index + 1)
            row_errors: list[str] = []
            student_no = BatchImportService._clean_cell(score.get("student_no"))
            student_name = BatchImportService._clean_cell(score.get("student_name"))
            gender = BatchImportService._clean_cell(score.get("gender"))
            school_name = BatchImportService._clean_cell(score.get("school_name"))
            grade_name = BatchImportService._clean_cell(score.get("grade_name"))
            class_name = BatchImportService._clean_cell(score.get("class_name"))
            item_name = BatchImportService._clean_cell(score.get("item_name"))
            raw_score = score.get("raw_score")

            if not BatchImportService._is_unlimited(batch.school_name) and school_name != batch.school_name:
                row_errors.append(f"学校需与批次一致：{batch.school_name}")
            if not BatchImportService._is_unlimited(batch.grade_name) and grade_name != batch.grade_name:
                row_errors.append(f"年级需与批次一致：{batch.grade_name}")
            if not BatchImportService._is_unlimited(batch.class_name) and class_name != batch.class_name:
                row_errors.append(f"班级需与批次一致：{batch.class_name}")
            if not match_scope_by_name(auth, school_name, class_name):
                row_errors.append("无权限导入该学校/班级数据")

            student_row = student_map.get(student_no)
            if not student_row:
                row_errors.append(f"学号不存在于学生档案：{student_no}")
            else:
                student, real_school, real_grade, real_class = student_row
                if student.name != student_name:
                    row_errors.append(f"姓名与学生档案不一致，应为：{student.name}")
                if BatchImportService._normalize_gender(student.gender) != BatchImportService._normalize_gender(gender):
                    row_errors.append("性别与学生档案不一致")
                if real_school != school_name:
                    row_errors.append(f"学校与学生档案不一致，应为：{real_school}")
                if real_grade != grade_name:
                    row_errors.append(f"年级与学生档案不一致，应为：{real_grade}")
                if real_class != class_name:
                    row_errors.append(f"班级与学生档案不一致，应为：{real_class}")

            item_rules = item_name_map.get(item_name) or []
            selected_item = None
            if not item_rules:
                row_errors.append(f"项目名称不属于当前批次标准：{item_name}")
            else:
                target_gender = BatchImportService._normalize_gender(gender)
                selected_item = next(
                    (
                        item for item in item_rules
                        if BatchImportService._normalize_gender(item.gender) in {target_gender, 'all'}
                    ),
                    None
                )
                if not selected_item:
                    row_errors.append("该项目不适用于该学生性别")

            if BatchImportService._clean_cell(raw_score) == "":
                row_errors.append("成绩不能为空")
            elif RuleEngine.parse_time_to_seconds(raw_score) is None:
                row_errors.append(f"成绩格式不正确：{raw_score}")

            if row_errors:
                errors.append(f"第 {row_number} 行：{'；'.join(row_errors)}")
                continue

            normalized = dict(score)
            normalized.pop("_row_number", None)
            if student_row:
                student, real_school, real_grade, real_class = student_row
                normalized.update({
                    "student_no": student.student_no,
                    "student_name": student.name,
                    "gender": student.gender,
                    "mobile": student.phone,
                    "school_name": real_school,
                    "grade_name": real_grade,
                    "class_name": real_class
                })
            if selected_item:
                normalized.update({
                    "item_code": selected_item.item_code,
                    "item_name": selected_item.item_name
                })
            normalized_scores.append(normalized)
        return batch, normalized_scores, errors

    @staticmethod
    def parse_score_excel(file_content: bytes) -> List[Dict[str, Any]]:
        """
        解析成绩导入 Excel 文件
        结构示例：
        学号 | 姓名 | 性别 | 学校 | 年级 | 班级 | 项目名称 | 成绩
        """
        try:
            wb = load_workbook(filename=io.BytesIO(file_content), data_only=True)
        except Exception:
            raise ValueError("Excel 文件解析失败，请确认上传的是 .xlsx 模板文件")
        sheet = wb.active
        scores = []

        rows = list(sheet.iter_rows())
        if len(rows) < 2:
            raise ValueError("Excel 文件中没有可导入的数据")

        header_map: dict[str, int] = {}
        for index, cell in enumerate(rows[0]):
            label = BatchImportService._normalize_header(cell.value)
            if label:
                header_map[label] = index

        missing_headers = [
            label for label, _ in BatchImportService.SCORE_HEADERS
            if BatchImportService._normalize_header(label) not in header_map
        ]
        if missing_headers:
            raise ValueError(f"模板表头缺少：{'、'.join(missing_headers)}")
        for row_number, row in enumerate(rows[1:], start=2):
            raw_row_values = [cell.value for cell in row]
            if not any(BatchImportService._clean_cell(value) for value in raw_row_values):
                continue

            score: dict[str, Any] = {}
            row_errors: list[str] = []
            for label, field in BatchImportService.SCORE_HEADERS:
                col_index = header_map[BatchImportService._normalize_header(label)]
                raw_value = row[col_index].value if col_index < len(row) else None
                cleaned_value = BatchImportService._clean_cell(raw_value)
                if label in BatchImportService.SCORE_REQUIRED_LABELS and not cleaned_value:
                    row_errors.append(f"{label}不能为空")
                score[field] = raw_value if field == "raw_score" else cleaned_value
            if row_errors:
                raise ValueError(f"第 {row_number} 行：{'；'.join(row_errors)}")

            score["_row_number"] = row_number
            scores.append(score)

        if not scores:
            raise ValueError("Excel 文件中没有可导入的数据")
        return scores
