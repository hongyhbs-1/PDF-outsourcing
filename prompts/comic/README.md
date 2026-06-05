# 漫画提示词版本库

本目录用于保存漫画图片的提示词版本和对应生成图。旧目录 `prompts/scene1`、`prompts/scene2` 不删除、不覆盖，后续迭代都在 `versions/` 下新建版本目录。

版本命名建议：

```text
vYYYY-MM-DD-<short-purpose>
```

示例：

```text
v2026-04-29-filled-content
```

每个版本必须包含：

- `_meta.md`：记录机构占位名、生成策略、替换说明。
- `prompts/scene1`：场景1三类学生提示词。
- `prompts/scene2`：场景2三类学生提示词。

生成图片与提示词放在同一目录，统一使用 PNG：

```text
prompts/scene1/差生-中文.md
prompts/scene1/差生-中文.png
prompts/scene1/中等生-中文.md
prompts/scene1/中等生-中文.png
prompts/scene1/优等生-中文.md
prompts/scene1/优等生-中文.png
```

生成满意后，将对应图片复制到：

```text
static/comic/scene1/
static/comic/scene2/
```
