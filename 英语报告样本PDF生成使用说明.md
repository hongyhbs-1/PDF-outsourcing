# 英语报告样本 PDF 生成使用说明

本文说明如何使用项目内现有脚本渲染英语样本，以及为什么部分生成页会出现"缺失数据"。

## 1. 背景

当前项目的 PDF 生成链路是：

```text
JSON payload → Jinja2 模板渲染 HTML → Playwright/Chromium 打印 PDF
```

主要入口：

```bash
python scripts/render_all_samples.py <样本序号> --学科 英语 --模式 报告
```

输出位置：

```text
samples/output/<样本名>/<样本名>.html
samples/output/<样本名>/<样本名>.pdf
```

## 2. 常用生成命令

`render_all_samples.py` 会扫描 `samples/json/*.json`，选择指定样本生成 HTML 和 PDF。

生成某个英语样本的家长版主报告：

```bash
python scripts/render_all_samples.py <样本序号> --学科 英语 --模式 报告
```

生成某个英语样本的招生蓝图/场景页：

```bash
python scripts/render_all_samples.py <样本序号> --学科 英语 --模式 场景
```

其中：

- `<样本序号>`：按 `samples/json/*.json` 文件名排序后的样本位置。
- `--学科 英语`：要求所选 JSON 的学科为英语。
- `--模式 报告`：生成家长版主报告。
- `--模式 场景`：只生成招生蓝图/场景页。

输出示例：

```text
samples/output/<样本名>/<样本名>.html
samples/output/<样本名>/<样本名>.pdf
```

## 3. 为什么部分页面会缺数据

`english_integration_db_simplify_report.json`、`english_integration_db_result_json.json`、`english_integration_parent_report.json` 等文件来自生产系统的 `brief-report-rem` 精简报告结构。

它们的核心结构类似：

```json
{
  "schema_version": "render_payload.v1",
  "meta": {
    "render_template": "brief-report-rem"
  },
  "sections": {
    "section_1_high_freq": {},
    "section_2_domains": {},
    "section_3_breakthrough": {},
    "section_4_coverage": {}
  }
}
```

而当前项目的主模板 `templates/report_master.jinja2` 需要的是完整报告结构，例如：

```json
{
  "cover": {},
  "summary": {},
  "domains": {},
  "core_weakness": {},
  "kp_drill": {},
  "data_reliability": {},
  "appendix": {},
  "tiered_learning": {}
}
```

因此，当前脚本中做了一个兼容适配：把 `brief-report-rem` 精简结构尽量转换成当前完整模板能识别的字段。这个适配可以解决类似：

```text
'summary' is undefined
```

这类渲染中断错误，但不能凭空生成源 JSON 中不存在的数据。

## 4. 各缺失页面的具体原因

### 4.1 数据分析概览

“数据分析概览”页面依赖字段包括：

```text
cover.cover_meta.paper_count
cover.cover_meta.display_question_count
cover.cover_meta.total_questions
data_reliability.section_4_coverage.stats.l3_covered
data_reliability.section_4_coverage.stats.l3_total
appendix.difficulty.items
appendix.papers.items
```

但 `brief-report-rem` 精简 JSON 通常只提供：

```text
sections.section_4_coverage.stats.total_questions
sections.section_4_coverage.stats.l2_covered
sections.section_4_coverage.stats.l2_total
sections.section_4_coverage.stats.l2_covered_text
```

所以该页可能只显示部分统计，或显示兜底文案。

### 4.2 三、个性化突破路径

该页依赖核心短板/突破项数据。

对于 `english_integration_db_simplify_report.json`，源数据里的：

```text
sections.section_3_breakthrough.items
```

可能为空，并且可能带有：

```text
all_achieved: true
```

这表示原始精简报告认为当前没有需要优先展示的突破项。因此该页没有详细突破路径，不是 PDF 生成失败。

### 4.3 四、知识点短板钻取

当前完整模板需要：

```text
kp_drill.tables
kp_drill.domain_panels
kp_drill.path_example
```

但精简 JSON 不包含逐知识点钻取表格、领域面板、路径示例等详细数据。因此页面会显示空态或兜底内容。

### 4.4 八、附录：试卷难度分布与分析依据

附录页依赖：

```text
appendix.difficulty.items
appendix.papers.items
appendix.metric_definitions
```

精简 JSON 一般没有完整的试卷清单、难度分布、指标释义数据，所以附录无法完整展示。

## 5. 哪些 JSON 更适合当前完整模板

更适合当前 `report_master.jinja2` 完整模板的是原项目已有的英文完整样本：

```text
samples/json/sample_02_english_integration.json
samples/json/sample_03_english_separation.json
```

这些样本为生产系统 V5.1 sections 格式（brief-report-rem），通过 `render_standalone.py` 的适配层渲染，生成效果会比精简样本更完整。

## 6. 如果目标是复现原始 parent_report.pdf

如果目标是尽量复现：

```text
samples/word/03-英语报告样本/*/parent_report.pdf
```

更准确的方式不是使用当前完整报告模板，而是恢复/接入原始精简报告模板体系：

```text
brief-report-rem
精简版报告-index.html
精简报告版-common.css
精简报告版-index.rem.css
```

当前 `render_all_samples.py` 使用的是统一完整报告模板，因此只能做兼容渲染，不能 1:1 复刻原始精简报告。

## 7. 浏览器/Playwright 报错处理

如果生成 HTML 成功，但 PDF 阶段报错类似：

```text
Chromium distribution 'chrome' is not found
Run "playwright install chrome"
```

说明本机缺少 Playwright 可用的浏览器。可尝试：

```bash
playwright install chromium
```

或按报错提示执行：

```bash
playwright install chrome
```

然后重新运行生成命令。

## 8. 判断生成是否成功

成功时终端会看到类似：

```text
HTML: xxx bytes
PDF:  xxx bytes
成功: 1/1
```

如果只生成了 HTML，没有生成 PDF，通常是浏览器环境问题；如果页面内部分模块为空，通常是源 JSON 缺字段或模板结构不匹配问题。
