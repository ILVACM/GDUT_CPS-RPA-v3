# -*- coding: utf-8 -*-
"""独立数值校对：直接从源 Excel 用 pandas 重算，与运行产出逐项比对。
不复用 ops/supervision_report 的任何函数，保证独立。
"""
import io
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import openpyxl
import pandas as pd

BASE = Path(r"D:\cps-gpes_rpa-20250312\v3\Test\zeng")
SRC = BASE / "履职表单20261017104155-source.xlsx"
OUT_X = BASE / "履职表单报告统计-202611030042.xlsx"
OUT_T = BASE / "履职表单报告统计-202611030042.txt"

COL_DEPT, COL_PERSON, COL_DATE = "部门", "检查人", "检查时间"
COL_PROF, COL_BAD, COL_STATUS = "专业名称", "不合格项", "工单状态"
S_CLOSED, S_DRAFT, S_FIXING = "已闭环", "草稿", "整改中"
SUF = ("总监项目部", "监理项目部")


def r1(x):
    return str(Decimal(repr(float(x)).replace('', '')).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP))


def r2(x):
    return str(Decimal(repr(float(x))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def r1s(x):
    d = Decimal(repr(float(x))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return f"{d:.1f}"


def r2s(x):
    d = Decimal(repr(float(x))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{d:.2f}"


def pdate(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (datetime, date)):
        return v if isinstance(v, date) and not isinstance(v, datetime) else v.date()
    s = str(v).strip()
    if not s:
        return None
    s = s.split(" ", 1)[0]
    for f in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, f).date()
        except ValueError:
            continue
    return None


def short(d):
    if not d:
        return "（未填写）"
    for s in SUF:
        if d.endswith(s):
            return d[:-len(s)]
    return d


def avg(n, p, d):
    return 0.0 if (p <= 0 or d <= 0) else n / p / d


print("=" * 70)
print("【1】源数据独立重算")
print("=" * 70)
df = pd.read_excel(SRC, sheet_name="0", header=0)
print(f"读取行数 = {len(df)}   列数 = {df.shape[1]}")
for c in (COL_DEPT, COL_PERSON, COL_DATE, COL_PROF, COL_BAD, COL_STATUS):
    print(f"  列存在 [{c}] = {c in df.columns}")

total = len(df)
persons_all = {str(x) for x in df[COL_PERSON].dropna() if str(x).strip()}
print(f"总表单数 = {total}")
print(f"全表去重人数 = {len(persons_all)}")

dates = [pdate(v) for v in df[COL_DATE]]
ok = [d for d in dates if d is not None]
dirty = total - len(ok)
dmin, dmax = min(ok), max(ok)
nat_days = (dmax - dmin).days + 1
wd_days = sum(1 for i in range(nat_days)
              if (dmin + pd.Timedelta(days=i)).weekday() < 5)
print(f"期间 = {dmin} ~ {dmax}   自然天数 = {nat_days}   周一至周五 = {wd_days}   脏日期 = {dirty}")

# 工作日口径
wd_mask = [d is not None and d.weekday() < 5 for d in dates]
wd_rows = sum(wd_mask)
persons_wd = {str(p) for p, m in zip(df[COL_PERSON], wd_mask) if m and str(p).strip()}
print(f"周一至周五行数 = {wd_rows}   其中去重人数 = {len(persons_wd)}")

bad = df[COL_BAD].apply(lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0)
bad_n = int(bad.sum())
closed_n = int((bad & (df[COL_STATUS] == S_CLOSED)).sum())
draft_n = int((df[COL_STATUS] == S_DRAFT).sum())
fixing_n = int((df[COL_STATUS] == S_FIXING).sum())
print(f"有问题表单 = {bad_n}   已闭环 = {closed_n}   草稿 = {draft_n}   整改中 = {fixing_n}")

eff_wd = wd_days
nat_avg = avg(total, len(persons_all), nat_days)
work_avg = avg(wd_rows, len(persons_wd), eff_wd)
print(f"自然日人均 = {r2s(nat_avg)}   工作日人均 = {r2s(work_avg)}（分母={eff_wd}）")
print(f"问题占比 = {r2s(bad_n / total * 100)}%   闭环占比 = {r2s(closed_n / bad_n * 100)}%")

print()
print("=" * 70)
print("【2】读运行产出")
print("=" * 70)
txt = OUT_T.read_text(encoding="utf-8-sig")
wb = openpyxl.load_workbook(OUT_X)
t1 = [[c.value for c in r] for r in wb[wb.sheetnames[0]].iter_rows()]
t2 = [[c.value for c in r] for r in wb[wb.sheetnames[1]].iter_rows()]
t3 = [[c.value for c in r] for r in wb[wb.sheetnames[2]].iter_rows()]

print("\n--- txt ---")
print(txt)

print()
print("=" * 70)
print("【3】逐项比对")
print("=" * 70)
chk = []


def ck(label, expect, actual):
    ok_ = str(expect) == str(actual)
    chk.append((ok_, label, expect, actual))
    print(f"  {'OK ' if ok_ else 'FAIL'}  {label}: 期望 {expect} / 实际 {actual}")


ck("txt 总表单数", f"共填写履职表单{total}张" in txt, True)
ck("txt 自然日人均", f"自然日平均每人每日填写表单{r2s(nat_avg)}张" in txt, True)
ck("txt 工作日人均", f"工作日平均每人每日填写表单{r2s(work_avg)}张" in txt, True)
ck("txt 有问题表单", f"有发现问题表单{bad_n}张" in txt, True)
ck("txt 问题占比", f"占比{r2s(bad_n/total*100)}%" in txt, True)
ck("txt 已闭环", f"已闭环{closed_n}张" in txt, True)
ck("txt 闭环占比", f"占比{r2s(closed_n/bad_n*100)}%" in txt, True)
ck("txt 草稿", f"其余有{draft_n}张草稿" in txt, True)
ck("txt 整改中", f"{fixing_n}张整改中" in txt, True)

# 表1
dept_stat = defaultdict(lambda: {"n": 0, "p": set(), "wn": 0, "wp": set()})
for i, row in df.iterrows():
    d = row[COL_DEPT]
    key = "" if (pd.isna(d) or str(d).strip() == "") else str(d)
    p = row[COL_PERSON]
    pk = "" if (pd.isna(p) or str(p).strip() == "") else str(p)
    s = dept_stat[key]
    s["n"] += 1
    if pk:
        s["p"].add(pk)
    if wd_mask[i]:
        s["wn"] += 1
        if pk:
            s["wp"].add(pk)

exp1 = []
for d, s in dept_stat.items():
    exp1.append((short(d), len(s["p"]),
                 avg(s["wn"], len(s["wp"]), eff_wd),
                 avg(s["n"], len(s["p"]), nat_days)))
exp1.sort(key=lambda r: (-r[2], -r[1], r[0]))

print(f"\n  表1 行数: 期望 {len(exp1)+1}（含合计）/ 实际 {len(t1)}")
chk.append((len(t1) == len(exp1) + 1, "表1 行数", len(exp1) + 1, len(t1)))

for i, (name, per, wa, na) in enumerate(exp1):
    got = t1[i + 1]
    ck(f"表1 行{i+1} 名称", name, got[0])
    ck(f"表1 行{i+1} 人数", per, got[1])
    ck(f"表1 行{i+1} 工作日人均", r1s(wa), got[2])
    ck(f"表1 行{i+1} 自然日人均", r1s(na), got[3])

ck("表1 合计人数", len(persons_all), t1[-1][1])
ck("表1 合计工作日人均", r1s(work_avg), t1[-1][2])
ck("表1 合计自然日人均", r1s(nat_avg), t1[-1][3])
ck("表1 合计标签", "合计", t1[-1][0])

# 表2
prof_cnt = Counter()
for v in df[COL_PROF]:
    k = "" if (pd.isna(v) or str(v).strip() == "") else str(v)
    prof_cnt[k] += 1
exp2 = sorted(prof_cnt.items(), key=lambda kv: (-kv[1], kv[0]))
print(f"\n  表2 行数: 期望 {len(exp2)+1}（含合计）/ 实际 {len(t2)}")
chk.append((len(t2) == len(exp2) + 1, "表2 行数", len(exp2) + 1, len(t2)))
for i, (k, v) in enumerate(exp2):
    got = t2[i + 1]
    ck(f"表2 行{i+1} 名称", ("（未填写）" if not k else k), got[0])
    ck(f"表2 行{i+1} 表单数", v, got[1])
    ck(f"表2 行{i+1} 占比", r1s(v / total * 100) + "%", got[2])
ck("表2 合计表单数", total, t2[-1][1])
ck("表2 合计占比", "100%", t2[-1][2])

# 表3
CN = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def dnum(s):
    if not s.startswith("第"):
        return None
    x = s[1:]
    if x == "十":
        return 10
    if x.startswith("十"):
        return 10 + CN[x[1:]] if len(x) == 2 and x[1:] in CN else None
    if "十" in x:
        a, _, b = x.partition("十")
        if a in CN and (b == "" or (len(b) == 1 and b in CN)):
            return CN[a] * 10 + (CN[b] if b else 0)
        return None
    return CN.get(x)


todo = defaultdict(lambda: {"draft": Counter(), "fix": Counter(), "blank": 0})
for i, row in df.iterrows():
    st = row[COL_STATUS]
    if st not in (S_DRAFT, S_FIXING):
        continue
    d = row[COL_DEPT]
    key = "" if (pd.isna(d) or str(d).strip() == "") else str(d)
    p = row[COL_PERSON]
    pk = "" if (pd.isna(p) or str(p).strip() == "") else str(p)
    b = todo[key]
    if pk:
        b["draft" if st == S_DRAFT else "fix"][pk] += 1
    else:
        b["blank"] += 1


def order3(d):
    n = dnum(short(d))
    if n is not None:
        return (0, n, "")
    return (1, -dept_stat[d]["n"], short(d))


exp3 = []
for d in sorted(dept_stat.keys(), key=order3):
    b = todo.get(d, {"draft": Counter(), "fix": Counter(), "blank": 0})
    n = sum(b["draft"].values()) + sum(b["fix"].values()) + b["blank"]

    def cell(c):
        if not c:
            return "/"
        items = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
        return "、".join(f"{k}（{v}张）" for k, v in items)
    exp3.append((f"{short(d)}（{n}张）", cell(b["draft"]), cell(b["fix"])))

print(f"\n  表3 行数: 期望 {len(exp3)} / 实际 {len(t3)-1}")
chk.append((len(t3) - 1 == len(exp3), "表3 行数", len(exp3), len(t3) - 1))
for i, (lab, a, b) in enumerate(exp3):
    got = t3[i + 1]
    ck(f"表3 行{i+1} 标签", lab, got[0])
    ck(f"表3 行{i+1} 草稿", a, got[1])
    ck(f"表3 行{i+1} 整改中", b, got[2])

print()
print("=" * 70)
n_fail = sum(1 for x in chk if not x[0])
print(f"比对总数 = {len(chk)}   失败 = {n_fail}")
if n_fail:
    print("失败明细：")
    for ok_, lab, e, a in chk:
        if not ok_:
            print(f"  FAIL {lab}: 期望 {e} / 实际 {a}")
else:
    print("✅ 全部一致")
