# 版本元信息

- 版本：`v2026-04-30-style-04-question-map`
- 风格：导航式学情地图
- 情绪方向：数据驱动感动家长
- 画面目标：把学习诊断可视化成导航路径图，从现状到目标，用报告引导正确方向。底部数据卡片用真实数据感动家长，激励持续使用。
- 人物设定：扁平风格动画小人物（chibi），占比不超过 5%，跨场景统一外观。
- 运行方式：图片生成后，可使用 `python scripts/render_all_samples.py 1 --comic-version v2026-04-30-style-04-question-map` 查看 PDF 样式。
- 图片要求：PNG，文件名必须为 `差生-中文.png`、`中等生-中文.png`、`优等生-中文.png`。
- 动态数据参数：
  - `{paper_count}` 试卷数量
  - `{question_count}` 题目数量
  - `{wrong_count}` 错题数量
  - `{kp_count}` 知识点数量
  - `{current_accuracy_text}` 当前正确率
  - `{target_accuracy_text}` 目标正确率
  - `{breakthrough_count}` 突破点数量
  - `{weakness_count}` 短板数量
  - `{kp_name_N}` / `{accuracy_N}` 知识点名称/正确率
  - `{action_N}` / `{action_desc_N}` 行动步骤名称/描述
