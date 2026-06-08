# Block / architecture diagrams (框图 / 架构图)

Use the `BlockDiagram` builder in `scripts/drawio.py` for boxes-and-arrows:
system architecture, module decomposition, data flow, component relationships.

## Model

- `block(label, col, row, color=...)` places a labelled box on a grid and
  returns its id.
- `connect(src, dst, label="", directed=True, dashed=False)` links two blocks.
  `directed=False` gives a plain line (e.g. a bus / bidirectional link).
- `group(label, members)` draws a dashed labelled container *behind* a set of
  blocks to show a boundary (a service, a tier, a subsystem).

Colours: `blue green orange yellow purple red gray` (draw.io's native palette).
Use colour to encode role — e.g. blue=app, green=gateway, gray=datastore.

## Layout

Grid coordinates: `col` is the column (x), `row` is the row (y). Spacing is
handled for you. For irregular layouts pass explicit `x=`/`y=` instead.

## Example

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

## Tips

- Call `group()` **after** placing its member blocks — it computes the boundary
  from their positions.
- Keep one concept per box; push detail into the label's second line
  (`"订单服务\n(Go, 8081)"`).
- For a strict left-to-right pipeline, keep everything in row 0 and increment
  col; for layers/tiers, use rows.
- Need a shape that isn't a rectangle (cylinder for a DB, cloud for external)?
  Pass a custom `style=` via the low-level `Diagram.add_vertex` (see
  format.md) — e.g. `shape=cylinder3;` for a database, `shape=cloud;` for an
  external system.
