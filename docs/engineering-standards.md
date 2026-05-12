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
├── docs/             # 文档
├── prompts/          # 漫画场景 prompt
├── static/           # 漫画图片等静态资源
└── learning_blueprint_two_page_package/  # 独立交付包
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
- `learning_blueprint_builder.py`（720 行）
- `m7_data_reliability.css`（1781 行）

## 5. 构建产物管理

### 5.1 .gitignore 规则

```gitignore
# 构建输出
dist/
build/

# 顶层调试产物
output*.html
output*.pdf

# Python 缓存
__pycache__/
*.pyc

# 样本输出（生成产物）
samples/output/

# 脚本临时输出
scripts/_output/
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

## 7. 待优化项

以下项目风险较高，需在功能稳定后执行：

1. **大文件拆分**：`learning_blueprint_builder.py` → `builders/` 子包
2. **CSS 拆分**：`m7_data_reliability.css` → 提取 `shared_data_table.css`
3. **目录重组**：`static/` → `assets/comics/`，`tests/` 从 `scripts/` 分离
4. **模板命名统一**：`m_overview` → `mX_overview`（需确认模块编号）
