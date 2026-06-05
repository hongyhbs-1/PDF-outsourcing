# 中文实施说明

## 目标

将报告开局页拆成两页：

- 第 1 页：学生学情诊断全景蓝图
- 第 2 页：补习执行与追踪蓝图

这两页用于告诉家长：本报告不是普通错题/分数分析，而是把 AI 诊断、老师执行、机构补习方案、持续追踪整合成可执行的学习导航。

## 为什么不用整页 PNG 底图

不建议使用整页 PNG 叠加文字。原因：

1. 动态文字容易溢出。
2. PDF 打印清晰度不稳定。
3. 不同学生状态颜色无法动态变化。
4. 后续数学、英语、作文专项扩展困难。

推荐方案：

```text
Jinja2 模板 + CSS Grid + Inline SVG + Python view model builder
```

## 接入步骤

### 1. 复制文件

```text
src_v2/services/learning_blueprint_builder.py
→ 项目 src_v2/services/learning_blueprint_builder.py

templates_v2/m00_student_diagnostic_blueprint.jinja2
→ 项目 templates_v2/m00_student_diagnostic_blueprint.jinja2

templates_v2/m01_tutoring_execution_blueprint.jinja2
→ 项目 templates_v2/m01_tutoring_execution_blueprint.jinja2

templates_v2/css/m00_learning_blueprint.css
→ 项目 templates_v2/css/m00_learning_blueprint.css
```

### 2. 修改 html_renderer.py

在 `render_html()` 中，渲染 context 创建后增加：

```python
from src_v2.services.learning_blueprint_builder import build_learning_blueprints

context.update(build_learning_blueprints(payload))
```

建议放在：

```python
context["render_payload"] = payload
```

之后。

### 3. 修改 report_master.jinja2

在封面后、正式报告模块前加入：

```jinja2
{% include "m00_student_diagnostic_blueprint.jinja2" %}
{% include "m01_tutoring_execution_blueprint.jinja2" %}
```

如果封面、目录、总览页不需要右侧 Edge Tabs，模板内已经包含 `.edge-tabs-mask`，可遮挡固定标签。

## 样式说明

`m00_learning_blueprint.css` 使用现有设计变量：

```css
--color-page-bg
--color-card-bg
--color-border-chart
--color-title-blue
--color-primary-teal
--color-warning
```

因此与当前报告浅底、白卡、青蓝、橙色提示体系保持一致。

## 渲染预览

运行：

```bash
python scripts/build_learning_blueprint_preview.py
```

会生成：

```text
examples/learning_blueprint_preview.html
```
