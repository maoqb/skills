# Flowcharts (流程图)

Use the `Flowchart` builder in `scripts/drawio.py`. You describe nodes and the
arrows between them; it places nodes on a grid from their row/col.

## Node vocabulary

| Method | Shape | Use for |
| --- | --- | --- |
| `start(label)` | green stadium | entry point ("开始") |
| `end(label)` | red stadium | exit point ("结束") |
| `process(label)` | blue rectangle | an action / step |
| `decision(label)` | orange diamond | a yes/no branch ("...?") |
| `io(label)` | yellow parallelogram | input / output |
| `subprocess(label)` | purple predefined-process | a named sub-routine |

`flow(src, dst, label="")` draws an arrow; label the branches out of a decision
(e.g. "是" / "否", "Yes" / "No").

## Layout model

- Every node has a **row** (top→bottom) and **column** (left→right).
- Rows auto-increment in call order, so a straight-line flow needs no
  positioning at all — just add nodes in order.
- For a branch, give the side path its own column and align its row with the
  decision using `row=`. Read `fc.current_row` to know where you are.

## Example — a branch that rejoins

```python
import sys; sys.path.insert(0, "<skill>/scripts")
from drawio import Flowchart

fc = Flowchart("登录流程")
a = fc.start("开始")
b = fc.io("输入账号密码")
c = fc.decision("验证通过?")
dec_row = fc.current_row - 1            # remember the decision's row
ok  = fc.process("生成会话")
no  = fc.process("提示错误", col=1, row=dec_row + 1)   # side branch
z   = fc.end("结束")

fc.flow(a, b)
fc.flow(b, c)
fc.flow(c, ok, "是")
fc.flow(c, no, "否")
fc.flow(ok, z)
fc.flow(no, z)
fc.save("login_flow.drawio")
```

## Tips

- Keep labels short; rely on shape colour/type to convey role.
- Decision nodes are taller (80px) by default so the diamond isn't cramped.
- For a loop-back arrow (e.g. "重试"), just `flow()` from a later node to an
  earlier one — orthogonal routing handles the elbow.
- Wider boxes: pass `w=200` to any node method.
- Multiple parallel branches: use columns 1, 2, 3 … and matching rows.
