# Outsourcing-PDF-layout

dida985 学情诊断报告 PDF 排版引擎。Python + Jinja2 + Playwright，将 JSON 数据渲染为 A4 PDF 报告。

数学和英语共用一套模板，通过 JSON 中的 `subject_name` 和 `page_visibility` 字段自动适配。

## 快速开始

```bash
# 安装依赖
pip install jinja2 playwright
playwright install chromium

# 渲染单个样本（HTML + PDF，输出在当前目录）
python3 scripts/render_standalone.py samples/json/math_parent.json -o output.html --pdf

# 批量渲染（数学报告）
python3 scripts/render_all_samples.py --学科 数学 --模式 报告

# 指定第 N 个样本渲染
python3 scripts/render_all_samples.py --学科 数学 --模式 报告 1

# 运行测试（NTFS 环境需串行）
python3 -m pytest scripts/ -p no:xdist -v
```

## 目录结构

```
├── scripts/           # Python 渲染引擎和测试
├── templates/
│   ├── pages/         # Jinja2 页面模板（22 个）
│   ├── css/           # 样式文件（26 个）
│   ├── macros/        # Jinja2 宏
│   ├── fonts/         # 字体文件
│   └── assets/        # 模板用图片（logo 等）
├── samples/
│   ├── json/          # 输入样本数据
│   └── output/        # 渲染输出（.gitignore）
├── docs/              # 项目文档
└── vault/             # dev-flow 任务管理（.gitignore）
```

## 技术栈

- **Python 3.11+** — 渲染脚本
- **Jinja2 3.1+** — 模板引擎
- **Playwright (Chromium)** — HTML → PDF 渲染
- **纯 CSS** — PDF 渲染样式，不需兼容浏览器

## 样本数据

| 文件 | 学科 | 说明 |
|------|------|------|
| `math_parent.json` | 数学 | 生产样本，完整数学家长版报告（20p） |
| `english_parent.json` | 英语 | 生产样本，完整英语家长版报告（22p） |

## 页面模块

| 模块 | 文件 | 说明 |
|------|------|------|
| M0 封面 | `m0_cover.jinja2` | 报告标题 + 学生信息 |
| 概览 | `m_overview.jinja2` | 数据分析概览 |
| 目录 | `m_toc.jinja2` | 目录 + 页码 |
| M1 摘要 | `m1_summary.jinja2` | 正确率 + P0 突破项 |
| M2 短板 | `m2_core_weakness.jinja2` | 核心短板排序表 |
| M3 钻取 | `m3_kp_drill.jinja2` | 知识点逐层展开 |
| M4 领域 | `m4_domains.jinja2` | 领域达标分析 |
| M5 考情 | `m5_city_compare.jinja2` | 城市考频对比（英语暂关） |
| M6 建议 | `m6_tiered_learning.jinja2` | 分层学习建议 |
| M7 可信度 | `m7_data_reliability.jinja2` | 数据覆盖率 + 汇总提示 |
| M8 附录 | `m8_appendix.jinja2` | 试卷清单 + 数据补充说明 |
| M9 逐题 | `m9_question_detail.jinja2` | 逐题详情 |
| M10 作文 | `m10_composition.jinja2` | 作文精讲（英语） |
| M11 阅读 | `m11_reading_deep.jinja2` | 阅读精讲（英语） |
| M00 蓝图 | `m00_student_diagnostic_blueprint.jinja2` | 学习诊断蓝图（场景模式） |
| M01 辅导 | `m01_tutoring_execution_blueprint.jinja2` | 辅导执行蓝图（场景模式） |
| 漫画场景 | `m2_comic_scene1.jinja2` / `m3_comic_scene2.jinja2` | 招生漫画页 |
| 画像 | `student_profile.jinja2` | 学生画像 |
| 提升预期 | `improvement_preview.jinja2` | 提升路线图 |
| 教师补充 | `m_teacher_supplement.jinja2` | 教师版增量 |
| 总报告 | `report_all_in_one.jinja2` | 家长版主报告容器 |

## CSS 加载顺序

```
1. base.css（全局基础）
2. m*.css / comic_*.css / improvement_*.css（模块样式，字母序）
3. shared_*.css（共享覆盖，最后加载，最高优先级）
```

## 渲染命令

```bash
# 家长版报告（主报告）
python3 scripts/render_all_samples.py --学科 数学 --模式 报告 [N]
python3 scripts/render_all_samples.py --学科 英语 --模式 报告 [N]

# 场景模式（招生蓝图，2 页）
python3 scripts/render_all_samples.py --学科 数学 --模式 场景 [N]
```

输出路径：`samples/output/<样本名>/<样本名>.pdf`（报告）或 `<样本名>_admissions_blueprint.pdf`（场景）

## 分页策略

各模块通过 `COMPACT_POLICY` 控制是否触发紧凑排版：

| 策略 | 模块 | 行为 |
|------|------|------|
| `always` | M1 | 始终紧凑 |
| `auto` | M4, M5, M6, M7 | 内容超限时自动紧凑 |
| `never` | M2, M3, M8, M9, M10, M11 | 不紧凑，自然分页 |

## 字号规则

所有打印模式字号 **不低于 9px**。`scripts/pdf_chrome_templates.py` 中的页眉/页脚同样遵守此规则。

## 文档索引

| 文档 | 说明 |
|------|------|
| `docs/需求文档.md` | 项目需求、排版规格 |
| `docs/engineering-standards.md` | 工程规范（命名、构建、Git commit） |
| `docs/report-data-contract.md` | 数据对账契约（JSON ↔ 模板） |
| `docs/visual-hierarchy-methodology.md` | 视觉层次方法论 |
| `docs/漫画图片功能使用说明.md` | 漫画场景页使用说明 |

## 开发约定

- **只改模板和 CSS，不改渲染逻辑（Python）**
- CSS 加载必须保持字母序，不能用前缀 hack
- NTFS 环境下 pytest 需串行运行（`-p no:xdist`）
- 详细规范见 `docs/engineering-standards.md`
