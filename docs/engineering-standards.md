# 工程规范

本文档定义 Outsourcing-PDF-layout 项目的代码组织、命名、构建产物管理等工程规范。

## 1. 目录命名

统一使用 **snake_case**，不例外。

```
项目根目录/
├── scripts/          # Python 排版引擎和渲染脚本
├── templates/        # Jinja2 模板 + CSS + 字体 + 资源
│   ├── pages/        # Jinja2 页面模板
│   ├── css/          # 样式文件
│   ├── macros/       # Jinja2 宏
│   ├── fonts/        # 字体文件
│   └── assets/       # 模板用图片（logo 等）
├── samples/          # 输入样本数据（JSON）
│   ├── json/         # 样本 JSON 文件
│   └── output/       # 渲染输出（.gitignore）
├── docs/             # 文档
├── prompts/          # 漫画场景 prompt
├── static/           # 漫画图片等静态资源
├── vault/            # dev-flow 任务管理（Obsidian vault）
└── tests/            # 测试文件（待迁移）
```

## 2. 文件命名

### 2.1 模板文件（templates/pages/）

格式：`{模块编号}_{功能描述}.jinja2`

- 模块编号必须连续（M0、M1、M2…）
- 不允许存在无编号的模板

| 模块 | 文件名 |
|------|--------|
| M0 封面 | `m0_cover.jinja2` |
| 概览 | `m_overview.jinja2` |
| 目录 | `m_toc.jinja2` |
| M1 摘要 | `m1_summary.jinja2` |
| M7 可信度 | `m7_data_reliability.jinja2` |

### 2.2 CSS 文件（templates/css/）

**一个模板一个 CSS 文件**，命名与模板一一对应。

- 模块样式：`m0_cover.css`、`m7_data_reliability.css`
- 共享样式：`shared_` 前缀（如 `shared_icon_enhancements.css`）
- 全局基础：`base.css`

**禁止**使用字母排序 hack（如 `zy_`/`zz_` 前缀）。共享覆盖通过 `shared_` 前缀 + `load_css()` 显式最后加载。

### 2.3 Python 文件（scripts/）

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| 入口脚本 | 功能描述即可 | `render_standalone.py`、`render_all_samples.py` |
| 服务模块 | 功能描述 | `html_renderer.py`、`pdf_service.py` |
| 测试文件 | `test_` 前缀 | `test_pdf_chrome_templates.py` |
| 子包目录 | snake_case | `golden_typeset/` |

## 3. CSS 加载顺序

`render_standalone.py` 的 `load_css()` 函数控制 CSS 加载优先级：

```
Stage 1: base.css（全局基础）
Stage 2: sorted(其余 *.css)（模块样式，字母序）
Stage 3: shared_*.css（共享覆盖，最高优先级，最后加载）
```

**关键约束**：Stage 2 必须保持 `sorted()` 字母序，不能改为按前缀分组。因为 `comic_*`/`improvement_*` 在字母序中排在 `m*` 之前，改变顺序会影响 CSS cascade 优先级。

`html_renderer.py` 只加载 `base.css` + `m*.css`，不加载 shared 覆盖。这是既定行为。

## 4. 单文件大小上限

| 类型 | 上限 | 超出处理 |
|------|------|---------|
| Python | 400 行 | 拆分为子模块 |
| CSS | 600 行 | 提取 shared 样式 |
| Jinja2 | 400 行 | 提取 macro |

当前超标文件（待后续优化）：
- `learning_blueprint_builder.py`（872 行）
- `m7_data_reliability.css`（1966 行）

## 5. 构建产物管理

### 5.1 .gitignore 规则

```gitignore
# 构建输出
dist/
build/

# 顶层调试产物
output*.html
output*.pdf
test_fix.html
v1_output.*

# Python 缓存
__pycache__/
*.pyc
*.pyo

# 样本输出（生成产物）
samples/output/
samples/html/
samples/pdf/

# 脚本临时输出
scripts/_output/

# AI 工具配置（跨环境不共享）
.agents/
.claude/
.cursor/
.pi/
.trellis/
AGENTS.md
```

### 5.2 输出目录约定

- 渲染输出默认在 `samples/output/{sample_name}/` 下
- 临时调试文件禁止提交到 git
- 调试时在项目根目录生成的 `output*.html/pdf` 必须在完成后删除

## 6. 已清理的历史遗留

| 项目 | 处理方式 | 日期 |
|------|---------|------|
| `templates_v2/` | 删除（空目录） | 2026-05-12 |
| `scripts/_output/` | 删除 + 加入 .gitignore | 2026-05-12 |
| 顶层 18 个 output\* 文件（120MB） | 删除 + 加入 .gitignore | 2026-05-12 |
| `zy_report_icon_enhancements.css` | 重命名为 `shared_icon_enhancements.css` | 2026-05-12 |
| `zz_chapter_title_underlines.css` | 重命名为 `shared_chapter_underlines.css` | 2026-05-12 |
| `learning_blueprint_two_page_package/` | 删除（已完成交付） | 2026-05-08 |
| `docs/漫画图片功能使用说明.md` | 删除（内容已过时） | 2026-05-08 |

## 7. Git Commit 规范

### 格式

```
<type>: <简短描述>

<可选详细说明>
```

### Type 列表

| Type | 用途 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: add M10 composition module` |
| `fix` | Bug 修复 | `fix: Section 07 layout collision` |
| `refactor` | 重构（不改功能） | `refactor: CSS rename zy/zz → shared_` |
| `style` | 样式调整（不改逻辑） | `style: icon size 13→16px` |
| `docs` | 文档 | `docs: add engineering standards` |
| `test` | 测试 | `test: add pagination regression test` |
| `chore` | 构建/工具/杂项 | `chore: update .gitignore` |

### 规则

- 描述用中文或英文均可，保持一条 commit 一致
- 破坏性变更加 `BREAKING CHANGE:` 前缀或 footer 说明
- 关联模块编号（如 `fix(m4): ...`、`feat(m10): ...`）

## 8. 优化路线图

### P1（先做）

| 项目 | 工时 | 前置 | 状态 |
|------|------|------|------|
| Git Commit 规范 | 0.5h | 无 | ✅ 已补充 |
| 归档 learning_blueprint_two_page_package/ | 0.5h | 无 | 待执行 |
| 测试文件分离到 tests/ | 1h | 无 | 待执行 |

### P2（功能稳定后）

| 项目 | 工时 | 前置 |
|------|------|------|
| learning_blueprint_builder.py 拆分 | 2h | 功能稳定 |
| m7_data_reliability.css 拆分 | 2h | 功能稳定 |
| m4/m5/m6 CSS 拆分 | 3h | m7 试点成功 |
| 模板命名统一 | 2h | A 项完成 |
| 入口脚本拆分 | 1h | 无 |
| static/ → assets/comics/ | 0.5h | 可与模板命名同步 |
| CSS/模板代码风格规范 | 1h | CSS 拆分完成 |

### 核心原则

先做零风险高回报的（规范、归档），再做结构重组（tests分离），最后做需要全面回归测试的（大文件拆分、模板重命名）
