# Sequence diagrams (时序图 / 序列图)

Use the `Sequence` builder in `scripts/drawio.py`. Sequence diagrams are the
fiddliest to hand-write because every message must line up across vertical
lifelines — the builder owns that geometry so you only state who talks to whom,
in order.

## Model

1. Declare participants left→right with `participant(label)`; each returns an
   index you use to refer to it.
2. Add messages top→bottom with `message(src, dst, label, kind)`. They are
   drawn in call order at evenly spaced rows; lifelines auto-extend to cover
   them all.

## Message kinds

| kind | arrow | meaning |
| --- | --- | --- |
| `"call"` (default) | solid, filled head | synchronous call / request |
| `"async"` | solid, open head | asynchronous message / signal |
| `"return"` | dashed, open head | reply / return value |
| `"self"` | small loop | a participant acting on itself |

Convention: pair each `call` with a later `return` going the other way. Returns
are optional — omit them when they'd just be noise.

## Example

```python
import sys; sys.path.insert(0, "<skill>/scripts")
from drawio import Sequence

sq = Sequence("下单时序")
user = sq.participant("用户")
web  = sq.participant("Web 前端")
api  = sq.participant("订单服务")
pay  = sq.participant("支付网关")

sq.message(user, web, "点击下单")
sq.message(web,  api, "POST /orders")
sq.message(api,  api, "校验库存", kind="self")
sq.message(api,  pay, "发起支付", kind="async")
sq.message(pay,  api, "支付结果", kind="return")
sq.message(api,  web, "201 Created", kind="return")
sq.message(web,  user, "显示成功页", kind="return")
sq.save("order_seq.drawio")
```

## Tips

- Order is everything — messages render in the order you add them. Read the
  scenario top to bottom and transcribe it.
- The diagram widens automatically with more participants and lengthens with
  more messages, so don't worry about page size.
- Keep participant names short (they sit in a fixed-width header box, ~140px).
- Put method signatures or payloads in the message label, e.g.
  `"login(account, pwd)"` or `"查询用户 {id}"`.
- For an alt/loop frame (optional, advanced), the builder doesn't draw boxes;
  if you need them, add a labelled dashed rectangle by hand around the relevant
  message rows using the low-level `Diagram.add_vertex` (see format.md).
