# 框图 / 架构图（Block / architecture diagrams）

用 `scripts/drawio.py` 里的 `BlockDiagram` 构建器画“方框 + 箭头”：系统架构、模块拆解、
数据流、组件关系。

## 模型

- `block(label, col, row, color=..., subtitle=None)` 在网格上放一个带标签的方框，返回它的 id。
  高度会按 `label` 的行数**自动计算**（每行 ~20px + 16px 留白），文字不会溢出方框；
  超长的单行文字（尤其是英文标识符）请显式传 `w=` 留够宽度。
  `subtitle="…"` 会在主名下面渲染一行**小灰字副标题**（9px / `#666`，自动不带括号）——
  用来补一句职责/出处/格式，而不是把它塞进 `label` 的括号里。`label` 保持单行短名；副标题
  里若出现「A + B + C」这种并列，改用 `child_block` 框中框。
- `child_block(parent_id, label, rel_x, rel_y, w, h, color=...)` 在父方框内部、相对
  父方框左上角偏移 `(rel_x, rel_y)` 处放一个小方框——用来表示“父方框包含多个同类元素”
  （框中框）。父方框建议传 `title_top=True`，让父方框的标题显示在顶部而不是居中，
  给子方框留出空间。
- `connect(src, dst, label="", directed=True, dashed=False, waypoints=None)` 连接两个
  方框。`directed=False` 画成普通直线（例如总线 / 双向连接）。`waypoints=[(x,y), ...]`
  让连线在这些中间点处转折，画成折线而不是直线——见下方“折线箭头”。
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

## 框中框（同类元素分组展示）

当一个方框概念上包含多个并列的子项（例如“配置文件目录”下有好几个子目录/文件类型），
不要把它们全塞进一行标签里——用 `child_block()` 画成框中框：

```python
container = bd.block("配置文件", x=60, y=60, w=520, h=115,
                      color="blue", title_top=True)   # 标题置顶，给子框留空间
bd.child_block(container, "flag_declarations/", rel_x=8,   rel_y=38, w=130, h=34, color="blue")
bd.child_block(container, "flag_values/",       rel_x=146, rel_y=38, w=110, h=34, color="blue")
bd.child_block(container, "release_configs/",   rel_x=264, rel_y=38, w=130, h=34, color="blue")
```

`child_block` 用绝对坐标定位（父框左上角 + `rel_x/rel_y`），子框宽度之和 + 间距需要小于
父框宽度，否则会溢出父框边界——和普通 `block()` 一样需要自己核对尺寸。

## 副标题（角色/出处提示，别用括号）

补一句职责/出处/格式时，用 `subtitle=` 而不是在标签里写 `名字（说明）`：

```python
bd.block("release_config.mk",        x=40,  y=40, w=240, color="yellow",
         subtitle="合并 map 列表 → maps_list")
bd.block("PRODUCT_RELEASE_CONFIG_MAPS", x=340, y=40, w=240, color="blue",
         subtitle="env var / soong_ui 输出")
```

主名保持单行短名，副标题是更小的灰字、自动不带括号。`title_top=True` 的容器框也能带
`subtitle`（标题加粗、副标题紧随其下）。副标题里若要并列多个子项，改用 `child_block`。

## 折线箭头（避免连线重叠）

默认 `connect()` 画直线（border-to-border）。当两个方框之间隔着别的方框、或多条连线会
挤在一起时，传 `waypoints=[(x,y), ...]` 让连线绕路：

```python
# A 在左上，B 在右下，中间隔着 C：让连线绕到左侧再往下
bd.connect(A, B, "读取", waypoints=[(30, 200), (30, 450)])
```

要点：
- waypoint 本身要落在**两个方框之外**（否则边框交点计算会出问题）。
- 多条连线如果都往同一侧绕路，给它们分配**不同的 x/y 通道**（例如一条走 x=30，另一条走
  x=100），避免折线段彼此重叠。
- 连线标签会画在折线的中间一段上，留意标签背景矩形（左右各 30px）不要超出画布——
  通道离画布边缘太近时把 x 往里收一点。

## 提示

- 放好成员方框**之后**再调用 `group()`——它根据成员位置计算边界。
- 一个方框一个概念；细节放到标签第二行（`"订单服务\n(Go, 8081)"`）。
- 严格的从左到右流水线：所有节点都放在 row 0、递增 col；分层/分级则用 row。
- 需要非矩形的形状（数据库用圆柱、外部系统用云）？通过底层的 `Diagram.add_vertex` 传自定义
  `style=`（见 format.md）——例如数据库用 `shape=cylinder3;`，外部系统用 `shape=cloud;`。
- 生成 SVG 后用 `rsvg-convert -w 1200 x.svg -o /tmp/preview.png`（或类似工具）渲染成图片
  自查一遍：文字是否溢出方框、折线是否仍有重叠、标签是否被裁切。
