---
type: guide
---

# Obsidian Vault 引导

本 Vault 是 dev-flow-skills 项目的**模板源**。每个实际项目使用独立的 Vault。

## 架构

```
dev-flow-skills/vault/     ← 模板源（git 跟踪）
  ├── templates/              任务/资料/路线图模板
  └── GETTING-STARTED.md      本引导

各项目/vault/               ← 项目 vault（不跟踪）
  ├── tasks/                  项目任务节点
  ├── references/             项目资料节点
  ├── maps/                   项目路线图
  ├── templates/              从模板源复制
  ├── HOME.md                 项目知识库首页
  └── GETTING-STARTED.md      从模板源复制
```

## 新项目初始化

1. 安装 [Obsidian](https://github.com/obsidianmd/obsidian-releases/releases/latest)
2. 运行初始化脚本：
```bash
~/Projects/dev-flow-skills/scripts/init-project-vault.sh <项目路径>
```
3. 用 Obsidian 打开 `<项目路径>/vault/` 目录

> 不需要手动设置环境变量。task-node 通过 `resolve_vault()` 自动发现项目 vault：
> 优先级：`OBSIDIAN_VAULT_PATH` 环境变量 > 当前目录 `vault/` > Git 根目录 `vault/` > `~/.hermes/.env`

## 目录结构

| 目录 | 用途 | 模板 |
|------|------|------|
| `tasks/` | 任务节点 — 跟踪每个任务的状态、阶段、关联 | `templates/task-template.md` |
| `references/` | 资料节点 — 决策记录、经验教训、API 参考 | `templates/reference-template.md` |
| `maps/` | 路线图 — 阶段规划、里程碑 | `templates/map-template.md` |
| `templates/` | 模板 — 创建新节点时复制对应模板 | — |

## 节点关系

每个节点通过 YAML frontmatter 建立依赖关系：

- **blocked_by** — 前置任务（必须完成后才能开始本任务）
- **blocks** — 后续任务（本任务完成后才能开始下游）
- **related** — 关联资料（参考关系，不阻塞）

用 `[[节点ID]]` 语法创建双向链接，Obsidian 图谱视图可可视化关系网络。

## 创建新任务

1. 复制 `templates/task-template.md` 到 `tasks/T{编号}-{简述}.md`
2. 填写 YAML frontmatter（id、title、priority、phase 等）
3. 在 HOME.md 添加入口链接
4. 在对应路线图（maps/）中引用

## 任务状态流转

```
backlog → in_progress → review → done → cancelled
```

## 阶段映射

任务 `phase` 字段与 dev-flow 流程阶段对应：

| phase | dev-flow 阶段 |
|-------|--------------|
| discuss | 讨论阶段 — 需求澄清 |
| decide | 决策阶段 — 方案选择 |
| code | 编码阶段 — 分工执行 |
| review | 审查阶段 — 代码审查 |
| fix | 修复阶段 — 迭代修复 |
| ship | 交付阶段 — 验收发布 |

## Git 流程集成

任务模板内嵌 Git 流程触发字段（branch、pr、commits、merged、release），由 `dev-flow-git` 技能自动维护：

- **decide 完成** → 切出分支
- **code 完成** → 推送 + 创建 PR
- **review 通过** → PR approve
- **ship 确认** → merge + 打 tag
