import json
import sys
from dataclasses import dataclass

import requests

BASE_URL = "http://127.0.0.1:9000"


@dataclass
class SessionInfo:
    telephone: str
    password: str
    token: str


def login(telephone: str, password: str) -> SessionInfo:
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"telephone": telephone, "password": password, "method": "0", "platform": "0"},
        timeout=20
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 200:
        raise RuntimeError(f"login failed: {telephone}: {data}")
    return SessionInfo(telephone=telephone, password=password, token=data["data"]["access_token"])


def api_get(session: SessionInfo, path: str, params=None):
    resp = requests.get(
        f"{BASE_URL}{path}",
        params=params,
        headers={"Authorization": f"Bearer {session.token}"},
        timeout=20
    )
    return resp


def api_post(session: SessionInfo, path: str, payload: dict):
    resp = requests.post(
        f"{BASE_URL}{path}",
        json=payload,
        headers={"Authorization": f"Bearer {session.token}"},
        timeout=20
    )
    return resp


def api_put(session: SessionInfo, path: str, payload: dict):
    resp = requests.put(
        f"{BASE_URL}{path}",
        json=payload,
        headers={"Authorization": f"Bearer {session.token}"},
        timeout=20
    )
    return resp


def flatten_titles(nodes):
    titles = []
    for node in nodes or []:
        title = node.get("title") or (node.get("meta") or {}).get("title")
        if title:
            titles.append(title)
        titles.extend(flatten_titles(node.get("children") or []))
    return titles


def ensure_ok(resp, label: str):
    try:
        data = resp.json()
    except Exception as exc:
        raise RuntimeError(f"{label} invalid json: {exc}") from exc
    if resp.status_code != 200 or data.get("code") != 200:
        raise RuntimeError(f"{label} failed: status={resp.status_code}, body={data}")
    return data


def ensure_forbidden(resp, label: str):
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}
    if resp.status_code == 200 and data.get("code") == 200:
        raise RuntimeError(f"{label} unexpectedly succeeded: {data}")


def main():
    admin = login("15802375679", "kinit2022")
    leader = login("15802370001", "kinit2022")
    coach = login("15802370002", "kinit2022")

    school_rows = ensure_ok(api_get(admin, "/vadmin/sport/school/list"), "admin school list")["data"]
    class_rows = ensure_ok(api_get(admin, "/vadmin/sport/class/list"), "admin class list")["data"]

    school_a = next(item for item in school_rows if item["school_name"] == "巴蜀中学")
    class_a = next(item for item in class_rows if item["id"] == 4)

    school_payload = {
        "school_name": school_a["school_name"],
        "school_code": school_a.get("school_code"),
        "region": school_a.get("region"),
        "stage_types": school_a.get("stage_types"),
        "sort": school_a.get("sort") or 0,
        "is_active": school_a.get("is_active", True),
        "leader_user_ids": [11, 12]
    }
    ensure_ok(api_put(admin, f"/vadmin/sport/school/{school_a['id']}", school_payload), "admin update school leaders")

    class_payload = {
        "school_id": class_a["school_id"],
        "grade_id": class_a["grade_id"],
        "class_name": class_a["class_name"],
        "class_code": class_a.get("class_code"),
        "sort": class_a.get("sort") or 0,
        "is_active": class_a.get("is_active", True),
        "remark": None,
        "coach_user_ids": [13, 14]
    }
    ensure_ok(api_put(admin, f"/vadmin/sport/class/{class_a['id']}", class_payload), "admin update class coaches")

    demo_student_no = "SCOPE-DEMO-001"
    admin_students = ensure_ok(api_get(admin, "/vadmin/sport/student/list", {"page": 1, "limit": 200}), "admin student list")["data"]["items"]
    demo_student = next((item for item in admin_students if item["student_no"] == demo_student_no), None)
    student_payload = {
        "student_no": demo_student_no,
        "name": "权限验证学生",
        "gender": "男",
        "school_id": class_a["school_id"],
        "grade_id": class_a["grade_id"],
        "class_id": class_a["id"],
        "phone": "15802370111",
        "birthday": None,
        "is_active": True,
        "remark": "role-scope-check"
    }
    if demo_student:
        ensure_ok(api_put(admin, f"/vadmin/sport/student/{demo_student['id']}", student_payload), "admin update demo student")
    else:
        ensure_ok(api_post(admin, "/vadmin/sport/student", student_payload), "admin create demo student")

    leader_menus = ensure_ok(api_get(leader, "/auth/getMenuList"), "leader menus")["data"]
    leader_titles = flatten_titles(leader_menus)
    if "权限管理" in leader_titles:
        raise RuntimeError("leader unexpectedly saw 权限管理")
    if "学校管理" in leader_titles:
        raise RuntimeError("leader unexpectedly saw 学校管理")
    if "年级管理" not in leader_titles or "班级管理" not in leader_titles or "学生管理" not in leader_titles:
        raise RuntimeError(f"leader menu missing required items: {leader_titles}")

    coach_menus = ensure_ok(api_get(coach, "/auth/getMenuList"), "coach menus")["data"]
    coach_titles = flatten_titles(coach_menus)
    if "权限管理" in coach_titles or "学校管理" in coach_titles or "年级管理" in coach_titles or "班级管理" in coach_titles:
        raise RuntimeError(f"coach unexpectedly saw restricted menus: {coach_titles}")
    if "学生管理" not in coach_titles:
        raise RuntimeError(f"coach menu missing 学生管理: {coach_titles}")

    leader_students = ensure_ok(api_get(leader, "/vadmin/sport/student/list", {"page": 1, "limit": 300}), "leader student list")["data"]["items"]
    if not any(item["student_no"] == demo_student_no for item in leader_students):
        raise RuntimeError("leader cannot see demo student")
    if any(item["school_name"] == "清华中学" for item in leader_students):
        raise RuntimeError("leader saw out-of-scope school student")

    coach_students = ensure_ok(api_get(coach, "/vadmin/sport/student/list", {"page": 1, "limit": 300}), "coach student list")["data"]["items"]
    if not any(item["student_no"] == demo_student_no for item in coach_students):
        raise RuntimeError("coach cannot see demo student")
    if any(item["class_id"] not in {4, 5} for item in coach_students):
        raise RuntimeError("coach saw out-of-scope class student")

    demo_student = next(item for item in coach_students if item["student_no"] == demo_student_no)
    coach_edit_payload = {
        "student_no": demo_student["student_no"],
        "name": "权限验证学生-教练编辑",
        "gender": demo_student["gender"],
        "school_id": demo_student["school_id"],
        "grade_id": demo_student["grade_id"],
        "class_id": demo_student["class_id"],
        "phone": demo_student["phone"],
        "birthday": None,
        "is_active": demo_student["is_active"],
        "remark": "coach-edited"
    }
    ensure_ok(api_put(coach, f"/vadmin/sport/student/{demo_student['id']}", coach_edit_payload), "coach edit student")

    ensure_forbidden(api_get(leader, "/vadmin/sport/school/list"), "leader school list forbidden")
    ensure_forbidden(api_get(coach, "/vadmin/sport/class/list"), "coach class list forbidden")

    leader_pe_batches = ensure_ok(api_get(leader, "/vadmin/pe/batch/list", {"page": 1, "limit": 50}), "leader pe batch list")["data"]["items"]
    if any(item["school_name"] == "清华中学" for item in leader_pe_batches):
        raise RuntimeError("leader saw out-of-scope pe batch")

    coach_fitness_batches = ensure_ok(api_get(coach, "/vadmin/fitness/batch/list", {"page": 1, "limit": 50}), "coach fitness batch list")["data"]["items"]
    if any(item["class_name"] not in {"3年1班", "3年2班"} and item["school_name"] == "巴蜀中学" for item in coach_fitness_batches):
        raise RuntimeError("coach saw out-of-scope fitness batch")

    print(json.dumps({
        "status": "ok",
        "leader_menu_titles": leader_titles,
        "coach_menu_titles": coach_titles,
        "leader_student_total": len(leader_students),
        "coach_student_total": len(coach_students),
        "leader_pe_batch_total": len(leader_pe_batches),
        "coach_fitness_batch_total": len(coach_fitness_batches)
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
