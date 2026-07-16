---
name: gerrit
description: >-
  在 AOSP（repo 管理的多仓库）工作区里操作 Gerrit：把同一个 topic 下的所有 change
  按依赖顺序 cherry-pick 到各自对应的项目目录——自动查询 topic、自动把 project 映射到
  本地路径、按 relation chain 排序、跳过已应用的 change、冲突后可续跑。当用户说
  「把 gerrit 上 topic X 的 patch 都摘下来」「cherry-pick 某个 topic」「拉某个 topic
  的所有 change 到本地」时使用；单个 change 的摘取也适用。
---

# gerrit

核心是 `scripts/gerrit_topic_pick.py`（纯 python3 标准库，无第三方依赖），
在 repo 工作区内任意目录运行即可。

## 前置条件

- 当前目录在一个 **repo 工作区**内（向上能找到 `.repo/`），`repo`、`git`、`ssh` 在 PATH 里。
- **Gerrit 地址**按此顺序确定：`--gerrit` 参数 → `GERRIT_URL` 环境变量 → manifest 里
  remote 的 `review="..."` 属性（脚本自动解析 `repo manifest -o -`）。公司内部 Gerrit
  一般 manifest 里就有，不用手动传。接受 `host`、`user@host:port`、`ssh://` 或
  `http(s)://` URL（只取主机名），ssh 端口默认 29418。
- **认证**：查询走 **SSH**（`ssh -p 29418 <host> gerrit query`），用的就是平时
  `repo sync` / 提交代码的那把 ssh key，通常不需要额外配置。可先验证连通性：

  ```bash
  ssh -p 29418 <gerrit-host> gerrit version
  ```

  平时 `repo sync` 走 ssh 能正常同步的话，说明认证已经通了，无需任何额外配置。
  若 ssh 用户名和 Gerrit 账号不一致导致认证失败，用 `--gerrit user@host` 显式指定
  用户名即可。

## 禁止事项

- **绝不修改机器上的任何配置文件**：`~/.ssh/config`、`~/.gitconfig`、`~/.netrc`、
  repo/manifest 配置等一律只读。认证或连通性有问题时，把错误和建议报告给用户，
  由用户自己处理；命令行能解决的（如 `--gerrit user@host`）优先走命令行参数。
- 不执行 `repo sync`、`git reset`、`git checkout` 等会改动用户现有工作状态的命令，
  除非用户明确要求（如回滚）。skill 对工作区的写操作仅限 cherry-pick 本身。
- cherry-pick 会落在各项目**当前检出的分支**上。先确认用户各项目在正确分支上；若在
  detached HEAD，建议先 `repo start <topic-branch> --all`（或只在受影响项目上建分支）。

## 工作流

1. **确认参数**：向用户要 topic 名；Gerrit 地址、目标分支过滤（`--branch`）通常可自动
   推断/省略，不确定再问。
2. **先 dry-run 看计划**：

   ```bash
   python3 scripts/gerrit_topic_pick.py <topic> --dry-run
   ```

   输出每个 change 的「编号/patchset、project、标题、映射到的本地目录」及应用顺序。
   有 SKIP（本地 manifest 没有该 project）或 change 数量意外时，先把计划给用户确认。
3. **正式执行**：去掉 `--dry-run` 重跑。脚本对每个 change 执行
   `repo download --cherry-pick <project> <num>/<patchset>`。
4. **冲突处理**：某个 change 冲突时脚本停下并打印出错目录。进入该目录
   `git status` → 解决冲突 → `git add` → `git cherry-pick --continue`，
   然后**重跑同一条命令**——已应用的 change 会按 Change-Id 自动跳过，不会重复摘取。

## 参数速查

| 参数 | 说明 |
| --- | --- |
| `topic`（必填） | Gerrit topic 名 |
| `--gerrit HOST` | Gerrit 地址：`host` / `user@host:port` / `ssh://` / `http(s)://` |
| `--status open\|merged\|any` | 按状态过滤，默认 `open` |
| `--branch BRANCH` | 只摘取目标为该分支的 change（topic 跨分支复用时需要） |
| `--dry-run` | 只打印计划不执行 |
| `--continue-on-fail` | 单个 change 失败后继续摘取其余的（默认失败即停） |

## 脚本行为要点

- 查询：`ssh -p <port> <host> gerrit query --format=JSON --current-patch-set
  topic:"<topic>" status:open`，逐行解析 JSON 并丢弃末尾 stats 行。
- 顺序：同一 relation chain 内 parent 先应用（按 currentPatchSet 的 parent commit
  拓扑排序），其余按 change 编号升序。
- project → 本地目录：解析 `repo list` 的 `path : project` 映射。
- 幂等：应用前先 `git log --grep "Change-Id: <id>"` 检查，已存在则跳过。

## 手动兜底（脚本不可用时）

查询 topic 下的 change：

```bash
ssh -p 29418 <gerrit-host> gerrit query --format=JSON --current-patch-set \
  'topic:"<topic>"' status:open
```

单个 change 摘取（二选一）：

```bash
# 方式一：repo 自带（推荐，自动找目录）
repo download --cherry-pick <project> <change-number>/<patchset>

# 方式二：裸 git（NN 是 change 编号的后两位）
cd <项目目录>
git fetch <gerrit-url>/<project> refs/changes/<NN>/<change-number>/<patchset>
git cherry-pick FETCH_HEAD
```

回滚：单个 change 用 `git -C <目录> reset --hard HEAD~1`（或 `cherry-pick --abort`）；
整个 topic 弄乱了可对受影响项目 `repo sync <project>...` 恢复。
