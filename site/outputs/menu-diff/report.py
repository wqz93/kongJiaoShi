import json, os

DIR = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(DIR, 'diff.json'), encoding='utf-8'))

# 语义映射：原型菜�� -> 线上对应（人工判定）
MAP = {
 '新建触达任务': '学员短信发送 / 教师短信发送 / 职工短信发送 / 摇号短信发送 / 全体学员短信发送 / 报名未缴费短信通知 / 自建组短信发送（7 类发送入口合并为一个任务）',
 '触达记录': '学员短信查询 / 教师短信查询 / 职工短信查询 / 摇号短信查询 / 全体学员短信查询 / 报名未缴费短信查询 / 自建组短信查询',
 '家长回复与咨询': '短信回复查询',
 '触达效果统计': '短信统计',
 '收件人组': '短信自建组管理',
 '通道与模板': '短信设置（长号设置）',
 '学员主题': '学员年龄统计 / 学员年龄比例 / 学员男女比例 / 生源地统计',
 '招生主题': '招生状况统计 / 新生统计 / 招生人数年度对比 / 报名门次',
 '教师主题': '职称统计 / 学历统计',
 '优先级设置': '自动打折设置（原型为打折优先级，线上为自动触发规则，能力不同）',
 '点到情况': '已点班级 / 未点到班级 / 应点未点（按状态拆分）',
 '电子协议与签名': '报名缴费签字管理',
 '退费审批': '财务审核 + 教务审核（拆为两级审核）',
 '打折规则': '限时自动打折 / 班级自动打折（线上为自动触发场景，非规则配置）',
 '家长端预览': '—（线上无对应，属原型新增能力）',
 '绑定率看板': '—（线上无对应，属原型新增能力）',
 '学员档案': '学员信息管理',
 '教师信息': '教师信息管理',
 '数据字典': '数据字典管理',
 '报名查询': '学员报名查询',
 '家长反馈': '点评汇总 + 家长投诉',
 '换班转班': '财务换班 + 财务换班日志',
 '收费结算表': '财务收费结算表',
 '年级升级': '年级升级（线上在学员管理下）',
 '培训班登记表': '培训班登记表（线上在教学统计分析下）',
 '教室登记表': '教室登记表（线上在教学统计分析下）',
 '教务管理行事表': '教务管理行事表（线上在教学统计分析下）',
 '年级升级': '年级升级',
 '触达中心': '短信管理（原型重构为统一触达，线上仍按对象拆分 18 项）',
 '打折规则': '自动打折（概念不同）',
 '指标中心': '教学统计分析 + 数据分析 + 数据中心（原型整合，线上分散在 3 处）',
 '电子协议与签名': '报名缴费签字管理',
 '单位介绍与报名向导': '单位介绍及报名向导（位置不同：新闻动态下 → 系统管理下）',
}

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

GROUP = [
    ('活动系统（wz）', ['综合活动', '单项网络活动', '在线答题', '假日营（地面）活动', '场馆活动管理'],
     '原型仅有「活动报名」（活动管理/报名管理/核销人员管理）3 项，线上活动系统含投票、调查、征集、答题闯关、PK赛等 12 项，原型完全未覆盖'),
    ('“双减”课后服务 / 托管（tg）', ['托管班管理', '托管班报名管理', '托管班财务管理', '托管班设置'],
     '托管类业务共 11 项菜单（开班/审核/发布/班级管理、报名、收费/缴费/结算、托管点、全局设置、协议设置），原型中完全没有'),
    ('统计分析类（edu + dat）', ['教学统计分析', '数据分析', '数据中心', '数据大屏'],
     '线上统计能力共 24 项菜单，散落在培训系统与数据中心两处；原型整合为「指标中心」5 项（招生/报名行为/学员/教师主题 + 数据大屏）'),
    ('智能场馆（jkpt）', ['系统设置', '基础信息'],
     '设备管理、学生/教师/职工头像、出入记录共 5 项，原型无对应'),
    ('系统维护（sys）', ['系统维护'],
     '用户/机构/角色管理与培训系统的「系统管理」重复，原型合并为一套'),
    ('短信与自动打折（edu）', ['短信管理', '自动打折'],
     '短信管理 18 项、自动打折 3 项；原型重构为「触达中心」8 项 +「打折规则」2 项'),
]

online_by_name = {m['name']: m for m in d['online']}

def menu_list(name, indent=0):
    m = online_by_name.get(name)
    if not m:
        return ''
    items = ''.join(
        f'<div class="oi" style="padding-left:{indent*16+14}px"><span class="dot"></span>{esc(c)}</div>'
        for c in m['children'])
    return items

def proto_list(name):
    m = next((x for x in d['proto'] if x['name'] == name), None)
    if not m:
        return '<div class="oi empty">（原型无此模块）</div>'
    return ''.join(f'<div class="oi"><span class="dot p"></span>{esc(c)}</div>' for c in m['children'])

rows_top = []
for gname, items, note in GROUP:
    for it in items:
        m = online_by_name.get(it)
        if not m:
            continue
        rows_top.append((gname if it == items[0] else '', it, menu_list(it), note if it == items[0] else '', len(m['children'])))

# 仅原型有的一级
ONLINE_EQUIV = {
    '触达中心': '<div class="oi">短信管理（18 项，按学员/教师/职工/摇号/全体/自建组 6 类对象各自拆发送+查询）</div>',
    '打折规则': '<div class="oi">自动打折（3 项：限时自动打折 / 班级自动打折 / 自动打折设置）</div>',
    '指标中心': '<div class="oi">教学统计分析(11) + 数据分析(5) + 数据中心(6) + 数据大屏(1)</div>',
}
only_proto_blocks = ''
for x in d['only_proto_top']:
    n = len(next(m for m in d['proto'] if m['name'] == x)['children'])
    equiv = ONLINE_EQUIV.get(x, '<div class="oi empty">线上无对应</div>')
    only_proto_blocks += f'''
    <div class="card">
      <div class="card-hd"><span class="badge b-p">{esc(x)}</span><span class="muted">原型独有 · {n} 项</span></div>
      <div class="card-bd">
        <div class="lbl">原型内容</div>
        {proto_list(x)}
        <div class="lbl mt">线上现状</div>
        {equiv}
      </div>
    </div>'''

# 二级差异表
def mk_rows(items, cls):
    return ''.join(f'<tr><td class="{cls}">{esc(i)}</td></tr>' for i in items)

# 语义映射表
map_rows = ''
for k, v in MAP.items():
    if k in d['only_proto_sub']:
        map_rows += f'<tr><td class="pk">{esc(k)}</td><td class="ar">{esc(v)}</td></tr>'

sys_of = {}
for m in d['online']:
    sys_of[m['name']] = m['sys']

online_sub_rows = ''
for m in d['online']:
    for c in m['children']:
        if c in d['only_online_sub']:
            online_sub_rows += f'<tr><td class="sys">{esc(m["sys"])}</td><td class="mod">{esc(m["name"])}</td><td class="pk">{esc(c)}</td></tr>'

common_rows = ''
for m in d['online']:
    for c in m['children']:
        if c in d['common_sub']:
            common_rows += f'<tr><td class="sys">{esc(m["sys"])}</td><td class="mod">{esc(m["name"])}</td><td class="ok">{esc(c)}</td></tr>'

html = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>菜单差异对比报告 · 原型 vs 线上系统</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;background:#f5f7fa;color:#1f2328;line-height:1.6;padding:32px 20px}}
.wrap{{max-width:1240px;margin:0 auto}}
h1{{font-size:26px;font-weight:700;margin-bottom:6px}}
.sub{{color:#656d76;font-size:14px;margin-bottom:24px}}
.srcs{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:28px}}
.src{{background:#fff;border:1px solid #d8dee4;border-radius:8px;padding:10px 14px;font-size:12.5px}}
.src b{{display:block;font-size:11px;color:#656d76;font-weight:500;margin-bottom:3px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin-bottom:30px}}
.kpi{{background:#fff;border:1px solid #d8dee4;border-radius:10px;padding:16px}}
.kpi .v{{font-size:28px;font-weight:700;line-height:1.1}}
.kpi .k{{font-size:12.5px;color:#656d76;margin-top:4px}}
.kpi.a .v{{color:#0969da}} .kpi.b .v{{color:#8250df}} .kpi.c .v{{color:#1a7f37}} .kpi.d .v{{color:#bf3989}}
h2{{font-size:19px;margin:34px 0 6px;padding-bottom:8px;border-bottom:2px solid #d8dee4}}
h2 .n{{font-size:12px;font-weight:600;color:#fff;background:#1f2328;border-radius:20px;padding:2px 10px;margin-left:8px;vertical-align:2px}}
.note{{font-size:13.5px;color:#57606a;background:#f0f3f6;border-left:3px solid #8c959f;padding:10px 14px;border-radius:0 6px 6px 0;margin:12px 0 18px}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #d8dee4;border-radius:8px;overflow:hidden;font-size:13.5px}}
th{{background:#f6f8fa;text-align:left;padding:9px 12px;font-weight:600;font-size:12.5px;color:#57606a;border-bottom:1px solid #d8dee4}}
td{{padding:8px 12px;border-bottom:1px solid #eaeef2;vertical-align:top}}
tr:last-child td{{border-bottom:none}}
.sys{{color:#656d76;font-size:12.5px;white-space:nowrap}}
.mod{{font-weight:600;white-space:nowrap}}
.ok{{color:#1a7f37}} .pk{{color:#bf3989}} .ar{{color:#57606a;font-size:13px}}
.grp{{background:#f6f8fa;font-size:11.5px;color:#57606a;font-weight:600;white-space:nowrap}}
.card{{background:#fff;border:1px solid #d8dee4;border-radius:10px;margin-bottom:16px;overflow:hidden}}
.card-hd{{padding:11px 15px;border-bottom:1px solid #eaeef2;display:flex;align-items:center;gap:10px}}
.card-bd{{padding:13px 15px}}
.badge{{font-size:13px;font-weight:600;padding:3px 11px;border-radius:20px}}
.b-p{{background:#fdeef0;color:#bf3989}} .muted{{font-size:12.5px;color:#656d76}}
.lbl{{font-size:11px;color:#8c959f;font-weight:600;letter-spacing:.4px;margin-bottom:5px}}
.lbl.mt{{margin-top:12px}}
.oi{{font-size:13px;padding:3px 0;color:#1f2328}}
.oi .dot{{display:inline-block;width:4px;height:4px;border-radius:50%;background:#8c959f;margin:0 8px 2px 0}}
.oi .dot.p{{background:#bf3989}}
.oi.empty{{color:#8c959f;font-style:italic}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
@media(max-width:820px){{.cols{{grid-template-columns:1fr}}}}
ul.diffs{{font-size:13.5px;padding-left:20px}} ul.diffs li{{margin:4px 0}}
</style></head><body><div class="wrap">
<h1>菜单差异对比报告</h1>
<div class="sub">地址1（重建原型） vs 地址2（线上生产系统） · 生成于 2026-10-14 · 账号 吴奇志 / 厦门市思明区青少年宫</div>

<div class="srcs">
  <div class="src"><b>地址1 · 原型</b>file:///D:/SNG/新旧系统对比/prototype/index.html<br>智慧少年宫服务平台 · 重建方案可交互原型</div>
  <div class="src"><b>地址2 · 线上</b>https://www.qsnedu.com/edumanage/index<br>6 个子系统入口：培训/活动/数据中心/系统管理/双减课后服务/智能场馆</div>
</div>

<div class="kpis">
  <div class="kpi a"><div class="v">16 → 31</div><div class="k">一级菜单：原型 → 线上</div></div>
  <div class="kpi b"><div class="v">82 → 136</div><div class="k">二级菜单：原型 → 线上</div></div>
  <div class="kpi c"><div class="v">65</div><div class="k">双方共有菜单</div></div>
  <div class="kpi d"><div class="v">54</div><div class="k">线上独有菜单（3+18一级 / 71 二级）</div></div>
</div>

<div class="note">
<b>核心结论：</b>原型只重建了线上 6 个子系统中的<b>「培训管理系统」</b>一个域，且做了大量整合与重构；
<b>活动系统、"双减"课后服务（托管）、智能场馆</b>三个子系统在原型中<b>完全没有对应</b>；
统计分析、短信触达、自动打折三块被原型压缩合并，能力颗粒度明显粗于线上。
</div>

<h2>一、仅原型有的模块<span class="n">3 个</span></h2>
{only_proto_blocks}

<h2>二、仅线上有的模块<span class="n">18 个一级 / 71 个二级</span></h2>
<table>
<thead><tr><th style="width:110px">子系统</th><th style="width:130px">一级菜单</th><th style="width:34%">二级菜单明细</th><th>说明</th></tr></thead>
<tbody>
{''.join(f'''<tr><td class="grp">{esc(g)}</td><td class="mod">{esc(it)}</td><td>{menu_list(it)}</td><td class="ar">{esc(note)}</td></tr>''' for g, it, ml, note, cnt in rows_top)}
</tbody></table>

<h2>三、原型独有菜单 → 线上对应<span class="n">17 项</span></h2>
<div class="note">这些并非「凭空新增」，多数是原型对线上多个菜单做了<strong>合并重构</strong>，因此名称对不上但能力有重叠。右侧「线上无对应」标记的才是原型真正新增的能力。</div>
<table>
<thead><tr><th style="width:180px">原型菜单</th><th>线上对应能力</th></tr></thead>
<tbody>{map_rows}</tbody></table>

<h2>四、线上独有二级菜单全清单<span class="n">71 项</span></h2>
<table>
<thead><tr><th style="width:150px">子系统</th><th style="width:130px">一级菜单</th><th>二级菜单</th></tr></thead>
<tbody>{online_sub_rows}</tbody></table>

<h2>五、双方共有菜单<span class="n">65 项</span></h2>
<table>
<thead><tr><th style="width:150px">子系统</th><th style="width:130px">一级菜单</th><th>二级菜单</th></tr></thead>
<tbody>{common_rows}</tbody></table>
</div></body></html>'''

open(os.path.join(DIR, 'menu-diff-report.html'), 'w', encoding='utf-8').write(html)
print('报告已生成: menu-diff-report.html')
print('共有', len(d['common_sub']), '| 原型独有二级', len(d['only_proto_sub']), '| 线上独有二级', len(d['only_online_sub']))