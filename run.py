# -*- coding: utf-8 -*-
"""
招生简章 —— 周六/周日 教室空档统计
规则：
  每天标准节次：上午2节 + 下午2节 = 4节；晚上2节为弹性，不纳入考核
  周六+周日 每个教室 上午+下午 至少应排满 8 节
  未达 8 节的教室 -> 存在空教室，逐条列出空闲时间段
"""
import sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd

SRC = r"E:\桌面\temp1790577877287招生简章.xls"

# ---------- 标准时段定义 ----------
SLOTS = [   # (key, 名称, 起, 止, 是否计入考核)
    ("S1", "上午第1节", "08:30", "10:00", True),
    ("S2", "上午第2节", "10:10", "11:40", True),
    ("S3", "下午第1节", "14:00", "15:30", True),
    ("S4", "下午第2节", "15:40", "17:10", True),
    ("E1", "晚间第1节", "17:20", "18:50", False),
    ("E2", "晚间第2节", "19:00", "20:30", False),
]
DAYS = ["周六", "周日"]
MIN_OVERLAP = 30          # 与标准节次重叠 >=30 分钟视为占用该节次


def mm(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


SLOT_MIN = {k: (mm(a), mm(b), name, counted) for k, name, a, b, counted in SLOTS}
SLOT_NAME = {k: name for k, name, a, b, c in SLOTS}

# ---------- 读数据 ----------
df = pd.read_excel(SRC, sheet_name='Sheet0', header=1, engine='xlrd')
df = df.dropna(how='all').reset_index(drop=True)
df['区域'] = df['区域'].astype(str).str.replace('【', '').str.replace('】报名入口', '', regex=False)
df['教室'] = df['教室'].astype(str).str.strip()
df['上课时间'] = df['上课时间'].astype(str).str.strip()
df['班级名称'] = df['班级名称'].astype(str).str.strip()

TIME_RE = re.compile(r'((?:周[一二三四五六日天]、?)+)\s*(\d{1,2}:\d{2})\s*[-~—]\s*(\d{1,2}:\d{2})')

occupancy = {}     # (区域, 教室, 周几, slot) -> [班级信息]
nonstandard = []   # 未能归入标准节次的周末课程

for _, r in df.iterrows():
    region = r['区域']
    rooms = [x.strip() for x in re.split(r'[\r\n]+', r['教室']) if x.strip()]
    tparts = [x.strip() for x in re.split(r'[\r\n]+', r['上课时间']) if x.strip()]

    parsed = []
    for tp in tparts:
        for m in TIME_RE.finditer(tp):
            days = re.findall(r'周[一二三四五六日天]', m.group(1))
            days = ['周日' if d == '周天' else d for d in days]
            s, e = mm(m.group(2)), mm(m.group(3))
            parsed.append((days, s, e, tp))

    # 教室与时间配对：数量一致则按顺序配对，否则笛卡尔积
    if len(rooms) > 1 and len(rooms) == len(parsed):
        pairs = list(zip(rooms, parsed))
    else:
        pairs = [(rm, pt) for rm in rooms for pt in parsed]

    for room, (days, s, e, raw) in pairs:
        wd = [d for d in days if d in DAYS]
        if not wd:
            continue
        hit = []
        for k, (a, b, name, counted) in SLOT_MIN.items():
            ov = max(0, min(e, b) - max(s, a))
            if ov >= MIN_OVERLAP:
                hit.append(k)
        if not hit:
            nonstandard.append({
                "区域": region, "教室": room, "班级名称": r['班级名称'],
                "专业": r['专业'], "教师": r['教师'], "上课时间": raw,
            })
            continue
        info = {
            "班级名称": r['班级名称'], "专业": r['专业'], "程度": r['程度'],
            "教师": r['教师'], "状态": r['状态'], "已招学员": r['已招学员'],
            "网招人数": r['网招人数'], "剩余名额": r['剩余名额'],
            "课次": r['课次'], "学费": r['学费'], "原始时间": raw,
        }
        for d in wd:
            for k in hit:
                occupancy.setdefault((region, room, d, k), []).append(info)

# ---------- 汇总 ----------
# 教室全集取自所有行（含仅周一至周五排课的教室，其周末应视为整周空置）
all_rooms = set()
for _, r in df.iterrows():
    for x in re.split(r'[\r\n]+', r['教室']):
        x = x.strip()
        if x and x != 'nan':
            all_rooms.add((r['区域'], x))
regions = sorted({rg for rg, _ in all_rooms})
rooms_by_region = {rg: sorted(rm for r2, rm in all_rooms if r2 == rg) for rg in regions}

rows_matrix, rows_empty = [], []
for rg in regions:
    for room in rooms_by_region[rg]:
        day_cnt = 0
        empty_slots = []
        row = {"区域": rg, "教室": room}
        for d in DAYS:
            for k, name, a, b, counted in SLOTS:
                lst = occupancy.get((rg, room, d, k), [])
                row[f"{d} {name}\n{a}-{b}"] = lst if lst else None
                if counted and lst:
                    day_cnt += 1
                if counted and not lst:
                    empty_slots.append((d, k))
        row["已排节数"] = day_cnt
        row["空闲节数"] = 8 - day_cnt
        row["是否满课"] = "满课" if day_cnt >= 8 else "有空档"
        rows_matrix.append(row)

        for d, k in empty_slots:
            k_name, a, b = SLOT_NAME[k], dict((x[0], (x[2], x[3])) for x in SLOTS)[k][0], \
                           dict((x[0], (x[2], x[3])) for x in SLOTS)[k][1]
            rows_empty.append({
                "区域": rg, "教室": room, "星期": d, "节次": k_name,
                "时间段": f"{a}-{b}", "该教室空闲节数": 8 - day_cnt,
                "该教室已排节数": day_cnt,
            })

df_matrix = pd.DataFrame(rows_matrix)
df_empty = pd.DataFrame(rows_empty).sort_values(
    ["区域", "该教室空闲节数", "教室", "星期", "时间段"], ascending=[True, False, True, True, True]
).reset_index(drop=True) if rows_empty else pd.DataFrame()

df_ns = pd.DataFrame(nonstandard)

# ---------- 控制台输出 ----------
print("=" * 90)
print("区域：", regions)
for rg in regions:
    sub = df_matrix[df_matrix['区域'] == rg]
    print(f"\n【{rg}】教室数 {len(sub)}，满课 {int((sub['是否满课'] == '满课').sum())}，"
          f"有空档 {int((sub['是否满课'] == '有空档').sum())}，"
          f"空档节次合计 {int(sub['空闲节数'].sum())}")
print("\n空档明细条数：", len(df_empty))
print("非标准时段条数：", len(df_ns))

# ---------- 导出 ----------
df_matrix.to_pickle("matrix.pkl")
df_empty.to_pickle("empty.pkl")
df_ns.to_pickle("ns.pkl")
print("\n已导出中间结果")
