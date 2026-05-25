# Outsourcing-PDF-layout

dida985 学情诊断报告 PDF 排版引擎。Python + Jinja2 + Playwright，将 JSON 数据渲染为 A4 PDF 报告。

数学和英语共用一套模板，通过 JSON 中的 `subject_name` 和 `page_visibility` 字段自动适配。

## 快速开始

```bash
# 安装依赖
pip install jinja2 playwright
playwright install chromium

# 渲染单个样本
python scripts/render_standalone.py samples/json/sample_01_math.json -o output.html --pdf

# 批量渲染全部样本
python scripts/render_all_samples.py

# 指定样本编号渲染
python scripts/render_all_samples.py 1

# 运行测试（57 个）
python -m pytest scripts/test_*.py -v
```
## 目录结构

```
├── scripts/           # Python 渲染引擎和测试
├── templates/
│   ├── pages/         # Jinja2 页面模板（22 个）
│   ├── css/           # 样式文件（23 个，base + 模块 + shared）
│   ├── macros/        # Jinja2 宏
│   ├── fonts/         # 字体文件
│   └── assets/        # 模板用图片（logo 等）
├── samples/
│   ├── json/          # 输入样本数据（3 个 JSON）
│   └── output/        # 渲染输出（.gitignore）
├── static/            # 漫画图片等静态资源
├── prompts/           # 漫画场景 prompt
├── docs/              # 项目文档
├── vault/             # dev-flow 任务管理
└── tests/             # 测试文件（待迁移）
```

## 技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| Python | 3.11+ | 渲染脚本 |
| Jinja2 | 3.1+ | 模板引擎 |
| Playwright | latest | HTML → PDF（Chromium） |
| CSS | 纯 CSS | PDF 渲染，不需兼容浏览器 |

## 样本数据

| 文件 | 学科 | 说明 |
|------|------|------|
| `sample_01_math.json` | 数学 | 生产样本，完整数学报告 |
| `sample_02_english_integration.json` | 英语 | brief-report-rem 格式，integration 类型 |
| `sample_03_english_separation.json` | 英语 | brief-report-rem 格式，separation 类型 |

> 英语样本为 V5.1 sections 结构，需要 `render_standalone.py` 的 brief-report 适配层渲染。

## 页面模块

| 模块 | 文件 | 说明 |
|------|------|------|
| M0 封面 | `m0_cover.jinja2` | 报告标题 + 学生信息 |
| 概览 | `m_overview.jinja2` | 数据分析概览 |
| 目录 | `m_toc.jinja2` | 目录 + 页码 |
| M1 摘要 | `m1_summary.jinja2` | 正确率 + P0 突破项 |
| M2 短板 | `m2_core_weakness.jinja2` | 核心短板排序表 |
| 漫画1 | `m2_comic_scene1.jinja2` | 学习困境（按等级显示） |
| M3 钻取 | `m3_kp_drill.jinja2` | 知识点逐层展开 |
| 漫画2 | `m3_comic_scene2.jinja2` | 学习成长 |
| M4 领域 | `m4_domains.jinja2` | 领域达标分析 |
| M5 考情 | `m5_city_compare.jinja2` | 城市考频对比（英语暂关） |
| M6 建议 | `m6_tiered_learning.jinja2` | 分层学习建议 |
| M7 可信度 | `m7_data_reliability.jinja2` | 数据覆盖率 |
| M8 附录 | `m8_appendix.jinja2` | 试卷清单 |
| M9 逐题 | `m9_question_detail.jinja2` | 逐题详情 |
| M10 作文 | `m10_composition.jinja2` | 作文精讲（英语） |
| M11 阅读 | `m11_reading_deep.jinja2` | 阅读精讲（英语） |
| M00 蓝图 | `m00_student_diagnostic_blueprint.jinja2` | 学习诊断蓝图 |
| M01 辅导 | `m01_tutoring_execution_blueprint.jinja2` | 辅导执行蓝图 |
| 画像 | `student_profile.jinja2` | 学生画像 |
| 提升预期 | `improvement_preview.jinja2` | 提升路线图 |
| 教师补充 | `m_teacher_supplement.jinja2` | 教师版增量 |

## CSS 加载顺序

```
1. base.css（全局基础）
2. m*.css / comic_*.css / improvement_*.css（模块样式，字母序）
3. shared_*.css（共享覆盖，最后加载，最高优先级）
```

## 文档索引

| 文档 | 说明 |
|------|------|
| `docs/需求文档.md` | 项目需求、排版规格 |
| `docs/engineering-standards.md` | 工程规范（命名、构建、Git commit） |
| `docs/report-data-contract.md` | 数据对账契约（JSON ↔ 模板） |
| `prompts/README.md` | 漫画 prompt 版本管理 |

## 开发约定

- **只改模板和 CSS，不改渲染逻辑（Python）**
- CSS 加载必须保持字母序，不能用前缀 hack
- 详细规范见 `docs/engineering-standards.md`
