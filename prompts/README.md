# 提示词与图片保存结构

`prompts/scene1` 和 `prompts/scene2` 是早期提示词与样图目录，保留用于追溯，不再直接覆盖。

新的漫画提示词按版本保存：

```text
prompts/comic/versions/<version>/
  README.md
  _meta.md
  prompts/
    scene1/
      差生-中文.md
      中等生-中文.md
      优等生-中文.md
    scene2/
      差生-中文.md
      中等生-中文.md
      优等生-中文.md
```

当前版本：`prompts/comic/versions/v2026-04-29-filled-content/`

规则：

- 新提示词版本必须新建目录，不覆盖旧版本。
- 同一版本生成的 PNG 图片与对应 `.md` 提示词放在同一场景目录下，便于回溯提示词和图片的对应关系。
- 最终用于 PDF 的图片仍复制到 `static/comic/scene1/` 和 `static/comic/scene2/`。
- 机构占位名统一写在版本 `_meta.md`，正式机构名称确定后全文替换。
