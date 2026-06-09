# 框图 / 架构图（Block / architecture diagrams）

用 `scripts/drawio.py` 里的 `BlockDiagram` 构建器画“方框 + 箭头”：系统架构、模块拆解、
数据流、组件关系。

## 模型

- `block(label, col, row, color=...)` 在网格上放一个带标签的方框，返回它的 id。
- `connect(src, dst, label="", directed=True, dashed=False)` 连接两个方框。
  `directed=False` 画成普通直线（例如总线 / 双向连接）。
- `group(label, members)` 在一组方框*背后*画一个带标签的虚线容器，用来表示边界
  （一个服务、一层、一个子系统）。

颜色：`blue green orange yellow purple red gray`（draw.io 原生调色板）。用颜色编码角色——
例如 blue=应用、green=网关、gray=数据存储。

## 布局

网格坐标：`col` 是列（x），`row` 是行（y）。间距已替你处理好。不规则布局可改为显式传
`x=`/`y=`。

## 示例

```python
import sys; sys.path.insert(0, "<skill>/scripts")
from drawio import BlockDiagram

bd = BlockDiagram("系统架构")
web  = bd.block("Web / App",   col=0, row=0, color="blue")
gw   = bd.block("API 网关",     col=1, row=0, color="green")
order = bd.block("订单服务",     col=2, row=0)
user  = bd.block("用户服务",     col=2, row=1)
pg    = bd.block("PostgreSQL",  col=3, row=0, color="gray")
redis = bd.block("Redis",       col=3, row=1, color="gray")

bd.connect(web, gw, "HTTPS")
bd.connect(gw, order, "gRPC")
bd.connect(gw, user, "gRPC")
bd.connect(order, pg, "SQL")
bd.connect(user, redis, "cache")

bd.group("后端服务", [order, user])      # dashed boundary
bd.group("数据层",   [pg, redis])
bd.save("architecture.drawio")
```

## 提示

- 放好成员方框**之后**再调用 `group()`——它根据成员位置计算边界。
- 一个方框一个概念；细节放到标签第二行（`"订单服务\n(Go, 8081)"`）。
- 严格的从左到右流水线：所有节点都放在 row 0、递增 col；分层/分级则用 row。
- 需要非矩形的形状（数据库用圆柱、外部系统用云）？通过底层的 `Diagram.add_vertex` 传自定义
  `style=`（见 format.md）——例如数据库用 `shape=cylinder3;`，外部系统用 `shape=cloud;`。
