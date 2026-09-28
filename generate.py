# -*- coding: utf-8 -*-
import sys, io, os, html, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd

mx = pd.read_pickle("matrix.pkl")
em = pd.read_pickle("empty.pkl")
ns = pd.read_pickle("ns.pkl")

DAYS = ["周六", "周日"]
SLOTS = [("S1", "上午第1节", "08:30", "10:00"), ("S2", "上午第2节", "10:10", "11:40"),
         ("S3", "下午第1节", "14:00", "15:30"), ("S4", "下午第2节", "15:40", "17:10")]
ESLOTS = [("E1", "晚间第1节", "17:20", "18:50"), ("E2", "晚间第2节", "19:00", "20:30")]
COLS = []
for d in DAYS:
    for k, name, a, b in SLOTS:
        COLS.append((d, k, name, a, b))
ECOLS = []
for d in DAYS:
    for k, name, a, b in ESLOTS:
        ECOLS.append((d, k, name, a, b))

REGIONS = ["厦港校区", "镇海校区"]
RCOLOR = {"厦港校区": "#2f6fed", "镇海校区": "#e0762a"}

out = []
w = out.append

w("""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>周六日教室空档统计报告</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f5f6f8;color:#1f2328;font-family:"Microsoft YaHei","PingFang SC",-apple-system,Segoe UI,sans-serif;font-size:14px;line-height:1.6}
.wrap{max-width:1680px;margin:0 auto;padding:28px 22px 60px}
h1{font-size:24px;margin:0 0 6px;font-weight:700}
.sub{color:#6b7280;font-size:13px;margin-bottom:20px}
.rule{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 18px;margin-bottom:22px;color:#374151;font-size:13px}
.rule b{color:#111827}
.cards{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:26px}
.card{flex:1;min-width:330px;background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:18px 20px;border-left:5px solid #ccc}
.card h3{margin:0 0 12px;font-size:16px;display:flex;align-items:center;gap:8px}
.dot{width:10px;height:10px;border-radius:50%;display:inline-block}
.stats{display:flex;gap:10px;flex-wrap:wrap}
.stat{background:#f8fafc;border:1px solid #eef1f5;border-radius:8px;padding:8px 12px;min-width:88px}
.stat .n{font-size:20px;font-weight:700;line-height:1.2}
.stat .l{font-size:12px;color:#6b7280}
.stat.warn .n{color:#d92d20}.stat.ok .n{color:#12805c}.stat.info .n{color:#2f6fed}
h2{font-size:18px;margin:30px 0 12px;padding-left:10px;border-left:4px solid #2f6fed}
.toolbar{display:flex;gap:10px;align-items:center;margin:10px 0 12px;flex-wrap:wrap}
.toolbar input{padding:7px 12px;border:1px solid #d1d5db;border-radius:8px;width:220px;font-size:13px;outline:none}
.toolbar input:focus{border-color:#2f6fed}
.tag{font-size:12px;color:#6b7280;background:#fff;border:1px solid #e5e7eb;border-radius:20px;padding:4px 12px}
table{border-collapse:collapse;width:100%;background:#fff;font-size:12.5px}
.tbox{border:1px solid #e5e7eb;border-radius:10px;overflow:auto;margin-bottom:10px}
th,td{border:1px solid #e8eaed;padding:6px 8px;vertical-align:middle}
thead th{background:#eef2f7;color:#1f2937;font-weight:600;position:sticky;top:0;z-index:2;white-space:nowrap}
tbody th{background:#f8fafc;text-align:left;font-weight:600;white-space:nowrap;position:sticky;left:0;z-index:1}
td.empty{background:#fee4e2;color:#b42318;font-weight:600;text-align:center}
td.used{background:#eafaf1;color:#0a5c3e}
td.used.conflict{background:#fef0c7;color:#93370d}
td.even{background:#f2f4f7;color:#475467}
td.even.used{background:#eef4ff;color:#1e429f;background:#eef4ff}
td.used .cn{display:block;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:190px}
td.used .tn{display:block;font-size:11px;opacity:.75}
.badge{display:inline-block;padding:1px 8px;border-radius:20px;font-size:11.5px;font-weight:600}
.b-full{background:#e7f6ef;color:#12805c}.b-gap{background:#fee4e2;color:#b42318}
tr.gaprow td,tr.gaprow th{background:#fff}
.foot{margin-top:34px;color:#9aa1ab;font-size:12px;text-align:center}
.note{background:#fffaeb;border:1px solid #fedf89;border-radius:10px;padding:12px 16px;margin:14px 0;font-size:13px;color:#7a4b00}
.legend span{display:inline-block;margin-right:16px;font-size:12px}
.sw{display:inline-block;width:14px;height:14px;border-radius:3px;vertical-align:-2px;margin-right:5px;border:1px solid #d0d5dd}
</style></head><body><div class="wrap">
""")

w('<h1>周六 / 周日 教室空档统计报告</h1>')
w('<div class="sub">数据源：招生简章.xls ｜ 共 %d 条班级记录 ｜ 按「区域」分校区独立统计</div>' % len(mx))

w("""<div class="rule">
<b>统计口径：</b>每天标准节次 4 节（<b>上午 2 节</b> 08:30-10:00 / 10:10-11:40，<b>下午 2 节</b> 14:00-15:30 / 15:40-17:10）；
晚间 2 节（17:20-18:50 / 19:00-20:30）为弹性时段，<b>不纳入考核</b>，仅作参考。<br>
<b>判定规则：</b>周六 + 周日，每个教室「上午 + 下午」应排满 <b>8 节</b>（4 节 × 2 天）。不足 8 节即判定为存在<b>空教室</b>，逐条列出空闲时间段。<br>
<b>时段归位：</b>课程时段与标准节次重叠 ≥ 30 分钟即视为占用该节次；跨节次的连堂课（如 08:30-11:30）同时占用所覆盖的多个节次。
</div>""")

# 概览卡片
w('<div class="cards">')
for rg in REGIONS:
    sub = mx[mx['区域'] == rg]
    sub_e = em[em['区域'] == rg] if len(em) else em
    nfull = int((sub['是否满课'] == '满课').sum())
    ngap = int((sub['是否满课'] == '有空档').sum())
    w('<div class="card" style="border-left-color:%s">' % RCOLOR[rg])
    w('<h3><span class="dot" style="background:%s"></span>%s</h3>' % (RCOLOR[rg], rg))
    w('<div class="stats">')
    w('<div class="stat info"><div class="n">%d</div><div class="l">教室总数</div></div>' % len(sub))
    w('<div class="stat ok"><div class="n">%d</div><div class="l">已满课(8/8)</div></div>' % nfull)
    w('<div class="stat warn"><div class="n">%d</div><div class="l">有空档教室</div></div>' % ngap)
    w('<div class="stat warn"><div class="n">%d</div><div class="l">空档节次</div></div>' % int(sub['空闲节数'].sum()))
    w('<div class="stat"><div class="n">%.0f%%</div><div class="l">周末排课率</div></div>' % (sub['已排节数'].sum() / (len(sub) * 8) * 100))
    w('</div></div>')
w('</div>')

w("""<div class="legend" style="margin-bottom:6px">
<span><i class="sw" style="background:#eafaf1"></i>已排课</span>
<span><i class="sw" style="background:#fee4e2"></i>空教室（重点）</span>
<span><i class="sw" style="background:#fef0c7"></i>同一时段多班冲突</span>
<span><i class="sw" style="background:#eef4ff"></i>晚间已排课（不计考核）</span>
<span><i class="sw" style="background:#f2f4f7"></i>晚间空闲（不计考核）</span>
</div>""")


def cell(lst):
    if not lst:
        return '<td class="empty">空</td>'
    cls = "used conflict" if len(lst) > 1 else "used"
    parts = []
    for x in lst:
        cn = x['班级名称']
        parts.append('<span class="cn" title="%s｜%s｜教师：%s｜已招 %s 人">%s</span><span class="tn">%s · %s</span>'
                     % (html.escape(cn), html.escape(str(x['专业'])), html.escape(str(x['教师'])),
                        html.escape(str(x['已招学员'])), html.escape(cn), html.escape(str(x['教师'])),
                        html.escape(str(x['原始时间']))))
    return '<td class="%s">%s</td>' % (cls, "".join(parts))


def ecell(lst):
    if not lst:
        return '<td class="even">·</td>'
    return '<td class="even used" title="%s">%s</td>' % (
        html.escape(" / ".join(x['班级名称'] for x in lst)),
        html.escape("".join(x['班级名称'][:14] for x in lst)))


# 每区域矩阵
for rg in REGIONS:
    sub = mx[mx['区域'] == rg].sort_values(['空闲节数', '教室'], ascending=[False, True])
    w('<h2 style="border-left-color:%s">%s ｜ 周末教室排课一览（%d 间教室）</h2>' % (RCOLOR[rg], rg, len(sub)))
    w('<div class="toolbar"><input class="q" data-t="%s" placeholder="输入教室名筛选…" oninput="flt(this)">'
      '<span class="tag">红色「空」= 该时段教室闲置</span></div>' % rg)
    w('<div class="tbox"><table class="mt" id="t-%s"><thead><tr>' % rg)
    w('<th>教室</th><th>已排<br>节数</th><th>空闲<br>节数</th><th>状态</th>')
    for d, k, name, a, b in COLS:
        w('<th>%s<br><span style="font-weight:400;font-size:11px">%s<br>%s-%s</span></th>' % (d, name, a, b))
    w('<th style="background:#f2f4f7">晚间<br>已排</th>')
    w('</tr></thead><tbody>')
    for _, r in sub.iterrows():
        w('<tr class="%s">' % ("gaprow" if r['空闲节数'] > 0 else ""))
        w('<th>%s</th>' % html.escape(r['教室']))
        w('<td style="text-align:center;font-weight:600">%d</td>' % r['已排节数'])
        w('<td style="text-align:center;font-weight:600;color:%s">%d</td>' % ('#b42318' if r['空闲节数'] else '#12805c', r['空闲节数']))
        w('<td style="text-align:center"><span class="badge %s">%s</span></td>' % ('b-full' if r['空闲节数'] == 0 else 'b-gap', r['是否满课']))
        for d, k, name, a, b in COLS:
            w(cell(r[f"{d} {name}\n{a}-{b}"] if isinstance(r[f"{d} {name}\n{a}-{b}"], list) else []))
        ec = sum(1 for d, k, name, a, b in ECOLS if isinstance(r[f"{d} {name}\n{a}-{b}"], list) and len(r[f"{d} {name}\n{a}-{b}"]))
        w('<td style="text-align:center;color:#1e429f;font-weight:600">%d / 4</td>' % ec)
        w('</tr>')
    w('</tbody></table></div>')

w("""<script>
function flt(inp){var t=document.getElementById('t-'+inp.dataset.t);var v=inp.value.trim();
 t.querySelectorAll('tbody tr').forEach(function(tr){tr.style.display = tr.cells[0].innerText.indexOf(v)>=0 ? '' : 'none';});}
</script>""")

# 空教室明细
w('<h2>空教室明细清单（共 %d 条）</h2>' % len(em))
if len(em):
    w('<div class="tbox"><table><thead><tr><th>#</th><th>区域</th><th>教室</th><th>星期</th><th>节次</th><th>时间段</th>'
      '<th>该教室已排</th><th>该教室空闲</th></tr></thead><tbody>')
    for i, r in em.iterrows():
        w('<tr><td>%d</td><td><span class="dot" style="background:%s"></span> %s</td><td><b>%s</b></td><td>%s</td><td>%s</td>'
          '<td><b>%s</b></td><td>%d / 8</td><td style="color:#b42318;font-weight:600">%d</td></tr>'
          % (i + 1, RCOLOR[r['区域']], r['区域'], html.escape(r['教室']), r['星期'], r['节次'],
             r['时间段'], r['该教室已排节数'], r['该教室空闲节数']))
    w('</tbody></table></div>')

# 重点提示
top = em.groupby(['区域', '教室']).size().reset_index(name='n').sort_values('n', ascending=False).head(8)
if len(top):
    w('<div class="note"><b>空档最多的教室 TOP 8：</b>')
    w('　'.join('%s（%s · %d 节空）' % (r['教室'], r['区域'], r['n']) for _, r in top.iterrows()))
    w('</div>')

if len(ns):
    w('<h2>未匹配标准节次的周末课程（需人工确认）</h2>')
    w('<div class="tbox"><table><thead><tr><th>区域</th><th>教室</th><th>班级名称</th><th>专业</th><th>教师</th><th>上课时间</th></tr></thead><tbody>')
    for _, r in ns.iterrows():
        w('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td><b>%s</b></td></tr>'
          % (r['区域'], html.escape(r['教室']), html.escape(r['班级名称']), r['专业'], r['教师'], html.escape(r['上课时间'])))
    w('</tbody></table></div>')

w('<div class="foot">生成时间：2026-09-28 ｜ 统计节次：周六/周日 上午+下午 共 8 节/教室</div>')
w('</div></body></html>')

os.makedirs("outputs", exist_ok=True)
hp = os.path.join("outputs", "周六日教室空档统计报告.html")
with open(hp, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("HTML ->", hp)

# ---------- Excel ----------
xp = os.path.join("outputs", "周六日教室空档统计.xlsx")
with pd.ExcelWriter(xp, engine="xlsxwriter") as wtr:
    bk = wtr.book
    fmt_h = bk.add_format({"bold": True, "bg_color": "#EEF2F7", "border": 1,
                           "align": "center", "valign": "vcenter", "text_wrap": True, "font_size": 11})
    fmt_c = bk.add_format({"border": 1, "valign": "vcenter", "text_wrap": True, "font_size": 10})
    fmt_cn = bk.add_format({"border": 1, "align": "center", "valign": "vcenter", "font_size": 10})
    fmt_empty = bk.add_format({"border": 1, "align": "center", "bg_color": "#FEE4E2",
                               "font_color": "#B42318", "bold": True, "valign": "vcenter", "font_size": 10})
    fmt_used = bk.add_format({"border": 1, "bg_color": "#EAFAF1", "valign": "vcenter",
                              "text_wrap": True, "font_size": 10})

    if len(em):
        t = em[["区域", "教室", "星期", "节次", "时间段", "该教室已排节数", "该教室空闲节数"]].copy()
        t.columns = ["区域", "教室", "星期", "节次", "时间段", "该教室已排节数(满8)", "该教室空闲节数"]
        t.to_excel(wtr, sheet_name="空教室明细", index=False, startrow=1, header=False)
        ws = wtr.sheets["空教室明细"]
        for j, c in enumerate(t.columns):
            ws.write(0, j, c, fmt_h)
        for j, wd in enumerate([12, 22, 8, 12, 14, 16, 14]):
            ws.set_column(j, j, wd, fmt_cn if j in (2, 5, 6) else fmt_c)
        ws.freeze_panes(1, 0); ws.autofilter(0, 0, len(t), len(t.columns) - 1)

    for rg in REGIONS:
        sub = mx[mx['区域'] == rg].sort_values(['空闲节数', '教室'], ascending=[False, True])
        cols = ["教室", "已排节数", "空闲节数", "是否满课"]
        for d, k, name, a, b in COLS + ECOLS:
            cols.append(f"{d} {name}\n{a}-{b}")
        t = sub[cols].copy()
        for c in cols[4:]:
            t[c] = t[c].apply(lambda v: " / ".join(f"{x['班级名称']}（{x['教师']} {x['原始时间']}）"
                                                   for x in v) if isinstance(v, list) and len(v) else "")
        t.columns = ["教室", "已排节数", "空闲节数", "是否满课"] + \
                    [c.replace(" ", "\n", 1) for c in cols[4:]]
        t.to_excel(wtr, sheet_name=rg, index=False, startrow=1, header=False)
        ws = wtr.sheets[rg]
        for j, c in enumerate(t.columns):
            ws.write(0, j, c, fmt_h)
        ws.set_column(0, 0, 22, fmt_c); ws.set_column(1, 3, 8, fmt_cn)
        ws.set_column(4, len(t.columns) - 1, 20, fmt_used)
        ws.freeze_panes(1, 1); ws.set_row(0, 42)
        ws.autofilter(0, 0, len(t), len(t.columns) - 1)

    if len(ns):
        ns.to_excel(wtr, sheet_name="非标准时段课程", index=False)
        wtr.sheets["非标准时段课程"].set_column(0, 5, 26, fmt_c)
print("XLSX ->", xp)
