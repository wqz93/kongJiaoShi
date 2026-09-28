# -*- coding: utf-8 -*-
"""把 SheetJS 内联进 app.html，生成单文件离线工具"""
import io, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
LIB = r"C:\Users\44231\.workbuddy\binaries\node\workspace\node_modules\xlsx\dist\xlsx.full.min.js"
OUT = os.path.join(BASE, "..", "outputs", "空教室查询工具.html")

app = io.open(os.path.join(BASE, "app.html"), encoding="utf-8").read()
lib = io.open(LIB, encoding="utf-8").read()
assert "/*XLSX_LIB*/" in app, "占位符缺失"
html = app.replace("/*XLSX_LIB*/", lib)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("OK ->", os.path.abspath(OUT), round(len(html.encode("utf-8")) / 1024), "KB")
