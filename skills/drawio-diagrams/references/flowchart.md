# 流程图（Flowcharts）

用 `scripts/drawio.py` 里的 `Flowchart` 构建器。你描述节点以及它们之间的箭头；它按各节点的
row/col 把节点放到网格上。

## 节点词汇表

| 方法 | 形状 | 用于 |
| --- | --- | --- |
| `start(label)` | 绿色体育场形 | 入口（“开始”） |
| `end(label)` | 红色体育场形 | 出口（“结束”） |
| `process(label)` | 蓝色矩形 | 一个动作 / 步骤 |
| `decision(label)` | 橙色菱形 | 一个是/否分支（“…?”） |
| `io(label)` | 黄色平行四边形 | 输入 / 输出 |
| `subprocess(label)` | 紫色预定义流程框 | 一个具名子过程 |

`flow(src, dst, label="")` 画一条箭头；给判断框引出的分支打标签（例如 “是” / “否”，
“Yes” / “No”）。

## 布局模型

- 每个节点都有一个 **row**（自上而下）和 **column**（自左向右）。
- row 按调用顺序自动递增，所以一条直线流程根本不用定位——按顺序加节点即可。
- 对于分支，给旁路单独一列，并用 `row=` 让它的行与判断框对齐。读 `fc.current_row` 可知道
  当前到哪一行了。

## 示例——一个分支后又汇合

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

## 提示

- 标签简短；靠形状的颜色/类型传达角色。
- 判断节点默认更高（80px），免得菱形太挤。
- 要画回环箭头（例如“重试”），直接从靠后的节点 `flow()` 回靠前的节点——正交布线会自动处理
  折角。
- 更宽的框：给任意节点方法传 `w=200`。
- 多条并行分支：用列 1、2、3 … 配上对应的 row。
