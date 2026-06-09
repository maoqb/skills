# 时序图 / 序列图（Sequence diagrams）

用 `scripts/drawio.py` 里的 `Sequence` 构建器。时序图是最难手写的，因为每条消息都要在竖直的
生命线之间对齐——这套几何由构建器负责，你只需按顺序说明谁对谁说话即可。

## 模型

1. 用 `participant(label)` 从左到右声明参与者；每次返回一个索引，供你引用它。
2. 用 `message(src, dst, label, kind)` 从上到下添加消息。它们按调用顺序、以等间距的行绘制；
   生命线会自动延伸覆盖所有消息。

构建器还会自动画**执行/激活条**（activation bars）：对某参与者的 `call`/`async` 会在接收方开启
一条激活条，从某参与者发出的 `return` 结束它的激活条，再次进入则延长已有的激活条（因此连续打到
同一参与者的一串调用会显示为一条连续的激活条）。结尾仍开着的激活条会在最后一行下方收掉，所以
即使你省略 `return`，激活条也合理。消息箭头吸附在激活条边缘。这些你都不用管——按顺序加消息就行。

## 消息类型（Message kinds）

| kind | 箭头 | 含义 |
| --- | --- | --- |
| `"call"`（默认） | 实线、实心箭头 | 同步调用 / 请求 |
| `"async"` | 实线、空心箭头 | 异步消息 / 信号 |
| `"return"` | 虚线、空心箭头 | 回复 / 返回值 |
| `"self"` | 小自环 | 参与者作用于自身 |

约定：每个 `call` 配一个稍后反方向的 `return`。`return` 可选——纯属噪音时就省略。

## 示例

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

## 提示

- 顺序决定一切——消息按你添加的顺序渲染。把场景从上到下读一遍，照着誊写。
- 参与者越多图越宽、消息越多图越长，所以不用操心页面尺寸。
- 参与者名字保持简短（它们待在固定宽度的表头框里，约 140px）。
- 把方法签名或负载放进消息标签，例如 `"login(account, pwd)"` 或 `"查询用户 {id}"`。
- 想要 alt/loop 框（可选、进阶用法）时，构建器不画框；如需要，用底层的 `Diagram.add_vertex`
  在相关消息行外手动加一个带标签的虚线矩形（见 format.md）。
