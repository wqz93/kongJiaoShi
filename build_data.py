# -*- coding: utf-8 -*-
"""把 .tmp_zs_*.json 分块 + 教室功能数据整理成前端可用的 data.json"""
import json, glob, re, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ---------- 1. 招生简章 ----------
cells = []
for f in glob.glob(".tmp_zs_*.json"):
    d = json.load(open(f, encoding="utf-8"))
    cells += d["cells"]
rows = {}
for c in cells:
    v = c.get("string_value")
    if v in (None, ""):
        v = c.get("number_value")
    rows.setdefault(c["row"], {})[c["col"]] = v

DAYMAP = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "日": 7}

def norm_room(raw, campus):
    """把招生简章里的教室写法规范化，返回 (校区, 教室名)"""
    r = raw.strip()
    if not r:
        return None
    # 显式校区前缀
    if r.startswith("厦港"):
        campus = "厦港"
    elif r.startswith("镇海"):
        campus = "镇海"
    r = re.sub(r"^(厦港|镇海)教室", "", r)
    r = r.replace("镇海二楼大礼堂", "大礼堂").replace("镇海二楼礼堂02", "礼堂02")
    r = re.sub(r"^厦港", "", r)  # 厦港4楼大舞蹈排练厅 / 厦港少年宫小飞鹭剧场右侧
    if r in ("钢琴教室", "大礼堂", "礼堂02"):
        campus = "镇海"
    if r.startswith("思明小学"):
        campus = "厦港"
    return (campus, r)

classes = []
sessions = []
extra_rooms = {"厦港": set(), "镇海": set()}  # 招生简章里出现但教室功能表没有的教室

for r, d in sorted(rows.items()):
    if r == 1:
        continue
    name = str(d.get(1) or "").strip()
    if not name:
        continue
    area = str(d.get(3) or "")
    campus = "镇海" if "镇海" in area else "厦港"
    room_raw = str(d.get(14) or "").strip()
    time_txt = str(d.get(13) or "").strip()
    major = str(d.get(6) or "").strip()
    teacher = str(d.get(16) or "").strip()
    left = d.get(21)
    fee = d.get(28)

    # 多教室（换行分隔）
    room_keys = []
    for piece in re.split(r"[\n\r]+", room_raw):
        nr = norm_room(piece, campus)
        if nr:
            room_keys.append(nr[1])
            extra_rooms[nr[0]].add(nr[1])
    room_keys = sorted(set(room_keys))

    classes.append({
        "n": name, "c": campus, "major": major, "time": time_txt,
        "rooms": room_keys, "roomRaw": room_raw.replace("\n", " "),
        "t": teacher,
        "left": int(left) if isinstance(left, (int, float)) else None,
        "fee": int(fee) if isinstance(fee, (int, float)) else None,
    })

    # 解析上课时段：按行/段切分，每段内的所有星期共用该时间段
    for seg in re.split(r"[\n\r]+", time_txt):
        days = re.findall(r"周([一二三四五六日])", seg)
        m = re.search(r"(\d{1,2}):(\d{2})\s*[-~—]\s*(\d{1,2}):(\d{2})", seg)
        if not days or not m:
            continue
        s = int(m.group(1)) * 60 + int(m.group(2))
        e = int(m.group(3)) * 60 + int(m.group(4))
        for piece in re.split(r"[\n\r]+", room_raw):
            nr = norm_room(piece, campus)
            if not nr:
                continue
            for dd in days:
                sessions.append({"c": nr[0], "room": nr[1], "day": DAYMAP[dd], "s": s, "e": e})

# ---------- 2. 教室功能 ----------
ROOM_FUNC = {"厦港": [], "镇海": []}
# (教室, 功能) —— 来自 教室功能.xlsx
xg = [
    ("301", "桌椅"), ("302", "桌椅"), ("303", "桌椅"), ("306", "桌椅"),
    ("307", "桌椅"), ("307-2", "钢琴"), ("308", "桌椅"), ("309", "桌椅"),
    ("310", "桌椅"), ("311", "桌椅"), ("312", "桌椅"), ("313", "桌椅"),
    ("401", "桌椅"), ("402", "桌椅"), ("403", "桌椅"), ("404", "桌椅"),
    ("405", "桌椅"), ("406", "桌椅"), ("407", "桌椅"), ("409", "桌椅"),
    ("410", "桌椅"), ("411", "桌椅"), ("412", "桌椅"), ("413", "桌椅"),
    ("414", "桌椅"), ("415", "桌椅"),
]
zh = [
    ("101", "桌椅"), ("102", "钢琴、画架"), ("103", "桌椅"), ("104", "桌椅"),
    ("105", "桌椅"), ("106", "桌椅"), ("107", "桌椅"), ("108", "桌椅"),
    ("109", "桌椅"), ("201", "桌椅"), ("202", "桌椅"), ("203", "桌椅"),
    ("301", "瑜伽垫"), ("302", "瑜伽垫"), ("401", "桌椅"), ("402", "桌椅"),
    ("403", "桌椅"), ("钢琴教室", "钢琴"), ("大礼堂", "桌椅"), ("礼堂02", "桌椅"),
]
for campus, lst in (("厦港", xg), ("镇海", zh)):
    for name, func in lst:
        ROOM_FUNC[campus].append({
            "name": name,
            "funcs": [f.strip() for f in re.split(r"[、,，/]+", func) if f.strip()],
        })

# 招生简章里用到但功能表没登记的教室，补进来（功能标“未登记”）
known = {"厦港": {r["name"] for r in ROOM_FUNC["厦港"]},
         "镇海": {r["name"] for r in ROOM_FUNC["镇海"]}}
for campus in ("厦港", "镇海"):
    for rn in sorted(extra_rooms[campus] - known[campus]):
        ROOM_FUNC[campus].append({"name": rn, "funcs": ["未登记"]})

data = {"rooms": ROOM_FUNC, "classes": classes, "sessions": sessions}
json.dump(data, open("data.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("班级数:", len(classes))
print("课次(session)数:", len(sessions))
print("厦港教室:", len(ROOM_FUNC["厦港"]), "镇海教室:", len(ROOM_FUNC["镇海"]))
print("未登记教室:", [r["name"] for c in ROOM_FUNC.values() for r in c if r["funcs"] == ["未登记"]])
print("data.json 大小:", len(open("data.json", "rb").read()), "bytes")
