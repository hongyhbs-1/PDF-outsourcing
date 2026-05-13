# Report Data, Header Footer, and Reading Progress Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复报告数据对不上的问题，统一页眉页脚视觉风格，并补齐阅读进度边条。

**Architecture:** 先建立数据源到页面展示的对账机制，区分数据源问题、适配层问题、模板问题和计算口径问题。页眉页脚与阅读进度边条作为 PDF chrome 层处理，避免影响正文分页；进度边条优先使用 PDF 后处理叠加，保证能按物理页显示当前章节。

**Tech Stack:** Python, Jinja2, Playwright Chromium PDF, PyMuPDF, CSS, Windows PowerShell runtime.

---

## Execution Principles

- 不通过兜底值、写死值或静默降级掩盖数据问题。
- 所有数据不一致都必须归类为：源数据问题、适配层问题、模板取数字段问题、计算口径问题。
- 页眉页脚和阅读进度边条不能挤压正文，也不能改变正文分页。
- 最终验证必须使用 Windows 运行环境。

---

## Task 1: 建立数据对账清单

**Files:**
- Create: `docs/report-data-contract.md`
- Read: `samples/json/*.json`
- Read: `templates/pages/*.jinja2`
- Read: `scripts/render_standalone.py`
- Read: `scripts/html_renderer.py`

**Step 1: 梳理关键展示项**

在 `docs/report-data-contract.md` 建表，每个模块列出：

```text
模块 | 页面展示项 | JSON 路径 | 适配/计算位置 | 模板位置 | 预期格式 | 是否允许缺失
```

必须覆盖：

- 学生姓名、学科、报告日期、报告标题
- 总题数、错题数、正确数、试卷数
- 当前正确率、目标正确率、达标率、提升空间
- 核心短板数量、P0/P1/P2 短板项
- 六大领域正确率与状态
- 城市考情对照中的短板交集、频次、重合率
- 逐题分析中的总题数、错题数、试卷数、题号、知识点
- 数据可信度中的样本数、覆盖率、低样本提醒

**Step 2: 标记高风险字段**

在同一文档中标记以下高风险类型：

```text
默认值污染：模板 default 或适配层 setdefault 可能覆盖真实缺失
口径重复计算：同一指标在多个模板重复算
字段同名冲突：items/keys/values/get 等字段不能点号访问
旧字段残留：模板仍读取历史字段名
显示文案拼接：百分比、题数、试卷数被拼接成字符串后难对账
```

**Step 3: 人工抽样确认**

先用 `sample_01_math_25q.json` 和 `sample_04_english_rpt2_dual.json` 作为两类基线：

- sample_01：常规数学样本
- sample_04：英语长样本，数据量大，分页复杂

---

## Task 2: 添加数据一致性审计脚本

**Files:**
- Create: `scripts/audit_report_data_consistency.py`
- Create: `scripts/test_report_data_consistency.py`
- Modify only if needed: `scripts/render_standalone.py`

**Step 1: 写审计脚本**

脚本读取 `samples/json/*.json`，渲染 HTML，不生成 PDF，输出每个样本的对账结果：

```text
sample
module
metric
source_path
source_value
rendered_value
status: ok | source_missing | rendered_missing | mismatch | unchecked
```

脚本只做检测，不自动修复。

**Step 2: 审计范围先覆盖关键指标**

首版覆盖：

- M1：当前正确率、目标正确率、达标率、P0 突破项数量
- M4：六大领域名称、正确率、状态
- M5：核心短板数量、城市高频交集数量
- M7/M8：试卷数、题目数、覆盖率
- M9：总题数、错题数、正确数、试卷数

**Step 3: 写回归测试**

`scripts/test_report_data_consistency.py` 至少包含：

```python
def test_sample_04_key_counts_match_rendered_html():
    ...

def test_question_detail_counts_are_not_hardcoded():
    ...

def test_summary_accuracy_uses_payload_value():
    ...
```

测试不允许只断言“页面包含某个固定字符串”，要从 JSON 读取值后断言 HTML 展示值和源值一致。

**Step 4: Windows 运行**

Run:

```powershell
powershell.exe -NoProfile -Command "Set-Location 'E:\python\jiedan\outsourcing-pdf-layout'; python .\scripts\test_report_data_consistency.py"
```

Expected:

```text
初次运行允许失败，失败项必须说明字段路径和页面展示值。
```

---

## Task 3: 修复数据不一致

**Files:**
- Modify: `scripts/render_standalone.py` if render context wiring is wrong
- Modify: `scripts/html_renderer.py` if alternate renderer wiring is wrong
- Modify: `templates/pages/*.jinja2` if template reads wrong fields
- Modify: `scripts/test_report_data_consistency.py`
- Update: `docs/report-data-contract.md`

**Step 1: 按类型修复**

修复规则：

```text
源数据缺失：记录在 docs/report-data-contract.md，不在模板中伪造结果
适配层取错：修 scripts/render_standalone.py 或 scripts/html_renderer.py
模板字段错：修对应 templates/pages/*.jinja2
计算口径不同：抽出统一计算或统一读取一个字段
默认值污染：只对非关键展示项允许 default；关键指标缺失要明确显示“数据缺失”或让测试暴露
```

**Step 2: 每修一个模块跑对应测试**

Run:

```powershell
powershell.exe -NoProfile -Command "Set-Location 'E:\python\jiedan\outsourcing-pdf-layout'; python .\scripts\test_report_data_consistency.py"
```

Expected:

```text
已修模块通过，未修模块仍可失败但必须在审计报告中可定位。
```

**Step 3: 全样本 HTML 审计**

Run:

```powershell
powershell.exe -NoProfile -Command "Set-Location 'E:\python\jiedan\outsourcing-pdf-layout'; python .\scripts\audit_report_data_consistency.py"
```

Expected:

```text
所有代码层 mismatch 清零。
源数据缺失项单独列出，不混入代码问题。
```

---

## Task 4: 统一页眉页脚视觉

**Files:**
- Create: `scripts/pdf_chrome_templates.py`
- Modify: `scripts/render_standalone.py`
- Modify: `scripts/pdf_service.py`
- Create: `scripts/test_pdf_chrome_templates.py`

**Step 1: 抽出共享 PDF chrome helper**

将 `render_standalone.py` 与 `pdf_service.py` 中重复的 header/footer CSS 和 template 抽到：

```text
scripts/pdf_chrome_templates.py
```

提供：

```python
def build_header_template(meta: dict) -> str: ...
def build_footer_template(meta: dict) -> str: ...
def build_pdf_margins() -> dict: ...
```

**Step 2: 新视觉规则**

页眉：

- 顶部轻量信息，不抢正文
- 左：报告短标题
- 中：学生称呼或学科
- 右：报告定位短语
- 下方使用 1px 细线，青绿色为主，浅沙色短线点缀

页脚：

- 左：报告名称或版权信息
- 中：页码胶囊 `第 x / y 页`
- 右：报告日期
- 文字颜色低饱和灰蓝，页码使用浅青底

推荐色值：

```text
text-muted: #6B7A86
text-strong: #12344D
teal: #1F6F78
teal-soft: #D0E8E8
sand: #D9B36A
line: #DDE5E8
```

**Step 3: 写测试**

`scripts/test_pdf_chrome_templates.py` 检查：

- `render_standalone.py` 和 `pdf_service.py` 都调用共享 helper
- header/footer 模板包含页码、日期、报告标题
- 样式不包含大面积背景、高饱和颜色、`position:absolute` 覆盖正文
- margin 与 header/footer 高度匹配

Run:

```powershell
powershell.exe -NoProfile -Command "Set-Location 'E:\python\jiedan\outsourcing-pdf-layout'; python .\scripts\test_pdf_chrome_templates.py"
```

Expected:

```text
All tests pass.
```

---

## Task 5: 补齐阅读进度边条

**Files:**
- Create: `scripts/pdf_progress_rail.py`
- Modify: `scripts/render_standalone.py`
- Modify: `scripts/pdf_service.py`
- Create: `scripts/test_pdf_progress_rail.py`

**Step 1: 采用 PDF 后处理叠加**

不要把阅读进度边条放入 HTML 正文流，避免影响分页和内容宽度。

使用 PyMuPDF 在 PDF 生成后叠加右侧进度边条：

```text
输入：PDF bytes + toc_pages + total_pages
输出：带阅读进度边条的 PDF bytes
```

**Step 2: 章节范围规则**

基于目录锚点生成章节范围：

```text
toc-m1  一、诊断摘要
toc-m4  二、六大领域达标分析
toc-m2  三、核心短板清单
toc-m3  四、知识点短板钻取
toc-m5  五、城市考情对照
toc-m6  六、分层学习建议
toc-m9  七、逐题分析明细
toc-m7  八、数据可信度说明
toc-m8  附录
toc-m10 英语作文专项
toc-m11 阅读理解深度分析
```

当前物理页落在哪个范围，就高亮对应节点。

**Step 3: 视觉规则**

- 放在页面右侧安全区，不能压正文。
- 竖向细线宽度 1px。
- 节点直径 3-4px。
- 当前章节用青绿色实心节点和短标签。
- 非当前章节用浅灰蓝节点。
- 封面、漫画页、目录页可以不显示，或显示极淡 rail。

**Step 4: 写测试**

`scripts/test_pdf_progress_rail.py` 检查：

- 能根据 `toc_pages` 生成有序章节范围
- 页码落点能映射到正确章节
- 封面/目录页默认不显示当前章节高亮
- 输出 PDF 页数不变

Run:

```powershell
powershell.exe -NoProfile -Command "Set-Location 'E:\python\jiedan\outsourcing-pdf-layout'; python .\scripts\test_pdf_progress_rail.py"
```

Expected:

```text
All tests pass.
```

---

## Task 6: 视觉验收与回归生成

**Files:**
- Output: `samples/output/*/*.html`
- Output: `samples/output/*/*.pdf`

**Step 1: 跑完整测试**

Run:

```powershell
powershell.exe -NoProfile -Command "Set-Location 'E:\python\jiedan\outsourcing-pdf-layout'; python .\scripts\test_pdf_pagination_regressions.py; python .\scripts\test_html_preview_width.py; python .\scripts\test_render_all_samples_cli.py; python .\scripts\test_report_density_layout.py; python .\scripts\test_report_data_consistency.py; python .\scripts\test_pdf_chrome_templates.py; python .\scripts\test_pdf_progress_rail.py"
```

Expected:

```text
All tests pass.
```

**Step 2: 重新生成全部样本**

Run:

```powershell
powershell.exe -NoProfile -Command "Set-Location 'E:\python\jiedan\outsourcing-pdf-layout'; python .\scripts\render_all_samples.py"
```

Expected:

```text
8 / 8 samples generated successfully.
```

**Step 3: 抽样截图检查**

用 PyMuPDF 导出：

```text
sample_01：封面后正文页、M1、M5、M9、最后页
sample_04：提升预期、M1、M4、M9、最后页
sample_06：M10/M11 英语深度页
sample_08：长样本最后页
```

检查项：

- 数据展示与审计结果一致
- 页眉页脚风格统一，不抢正文
- 阅读进度边条存在且当前章节高亮正确
- 边条不压正文、不遮挡图表、不影响页码
- PDF 页数没有异常增加
- 不出现“一页内容被拆成下一页小尾巴”的回归

---

## Acceptance Criteria

- 数据审计脚本能对 8 个样本输出清晰对账结果。
- 所有代码层数据 mismatch 清零；源数据缺失单独记录。
- 页眉页脚由共享 helper 输出，两个 PDF 入口风格一致。
- 阅读进度边条出现在正文页，当前章节高亮正确，PDF 页数不变。
- Windows 环境完整测试通过。
- `render_all_samples.py` 全量 8 个样本生成成功。

