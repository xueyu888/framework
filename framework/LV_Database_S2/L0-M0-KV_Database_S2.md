# 中文模块名:EnglishName

@framework

这个模块是KV数据库+WAL+Checkpoint的模块。

## 1. 能力声明（Capability Statement）

- `C1` 数据承载能力：能承载KEY和VALUE。
- `C2` 数据关系映射能力：能映射KEY和VALUE之间的关系，每个KEY有些仅有一个映射的VALUE，且这个映射是单向的。
- `C3` "put"能力：能添加新的KEY和映射的VALUE。
- `C4` "get"能力：能根据KEY查询其映射的VALUE。
- `C5` "delete"能力：能删除KEY和其映射的VALUE。
- `C6` 日志记录能力：在执行添加和删除之前记录对应的操作、KEY、VALUE。
- `C7` 快照记录能力：能记录当前数据库状态，并落盘成快照文件。
- `C8` 数据恢复能力：能根据日志和快照恢复程序上次结束运行时的状态。-

### 非职责声明（Non-Responsibility Statement）

- `N1` 非职责声明：不负责具并发处理、高效查询、范围查询。

## 2. 边界定义（Boundary / Parameter 参数）

- `COUNT` 数量边界：可承载的KEY/VALUE的数量存在上限限制。来源：`C1`。
- `OPERATION` 操作边界：对数据的操作只能是"put"，"get"，"delete"。来源：`C3 + C4 + C5`。
- `KEY` KEY边界：每次操作必须输入一个KEY，且是str类型。来源：`C2 + C3 + C4 + C5`。
- `VALUE` VALUE边界："put"操作必须输入一个VALUE，不限数据类型。来源：`C2 + C3 + C4 + C5`。
- `LOGPATH` 日志路径边界：日志存放的路径，和日志文件名必须明确。来源：`C6`。
- `LOG` 日志内容格式边界：日志以"操作"，"KEY"，"VALUE"的格式进行排列。来源：`C6`。
- `SNAPSHOTPATH` 快照路径边界：快照存放的路径，及快照文件并必须明确。来源：`C7`。
- `SNAPSHOT` 快照内容格式边界：快照以"{"KEY":"VALUE"}"的格式按行排列。来源：`C7`。
- `RECORDTIMING` 快照记录时机边界：需要明确进行快照记录的时机。来源：`C7`。
- `RECOVER` 恢复依据边界：数据只能根据日志和快照进行恢复。来源：`C8`，.

## 3. 最小结构基（Minimal Structural Bases）

- `B1` KEY-VALUE容器：将KEY-VALUE以一对一的形式存放数据的容器。来源：`C1 + C2 + C3 + C4 + C5 + COUNT + OPERATION + KEY + VALUE`。
- `B2` 日志：记录执行的操作。来源：`C6 + C8 + LOGPATH + LOG + RECOVER`。
- `B3` 快照：记录当前状态。来源：`C7 + C8 + SNAPSHOTPATH + SNAPSHOT + RECORDTIMING + RECOVER`。

## 4. 基组合原则（Base Combination Principles）

- `R1` 日志记录组合
  - `R1.1` 参与基：`B1 + B2`。
  - `R1.2` 组合方式：在进行"put"，"delete"之前，先将操作和对应的KEY-VALUE记录到日志，然后在落实到容器。
  - `R1.3` 输出能力：`C1 + C2 + C3 + C4 + C5 + C6`。
  - `R1.4` 边界绑定：`COUNT + OPERATION + KEY + VALUE + LOGPATH + LOG`。
- `R2` 快照记录组合
  - `R2.1` 参与基：`B1 + B3`。
  - `R2.2` 组合方式：到达`RECORDTIMING`时机时，将当前数据库状态记录为一次快照。
  - `R2.3` 输出能力：`C1 + C2 + C3 + C4 + C5 + C7`。
  - `R2.4` 边界绑定：`SNAPSHOTPATH + SNAPSHOT + RECORDTIMING`。
- `R3` 数据恢复组合
  - `R3.1` 参与基：`B1 + B2 + B3`。
  - `R3.2` 组合方式：程序启动时，根据当前工作区内的快照和日志，将数据库状态恢复至上次程序结束时的状态。
  - `R3.3` 输出能力：`C8`。
  - `R3.4` 边界绑定：`LOGPATH + LOG + SNAPSHOTPATH + SNAPSHOT + RECOVER`。
- `R4` 完整功能组合
  - `R4.1` 参与基：`B1 + B2 + B3`
  - `R4.2` 组合方式：程序启动时，根据当前工作区内的快照和日志，将数据库状态恢复至上次程序结束时的状态。在进行"put"，"delete"之前，先将操作和对应的KEY-VALUE记录到日志，然后在落实到容器。到达`RECORDTIMING`时机时，将当前数据库状态记录为一次快照，并且清空WAL。
  - `R4.3` 输出能力：`C1 + C2 + C3 + C4 + C5 + C6 + C7 + C8`
  - `R4.4` 边界绑定：`COUNT + OPERATION + KEY + VALUE + LOGPATH + LOG + SNAPSHOTPATH + SNAPSHOT + RECORDTIMING + RECOVER`

## 5. 验证（Verification）

- `V1` 操作正确性：数据库内容变化，必须与执行的操作、输入的KEY和VALUE一致，
- `V2` 操作、日志、快照一致性：内存中维护的数据库必须与通过日志、快照恢复的数据库一致。
- `V3` 日志先行性：每次进行操作时必须先落实日志，再对数据库进行修改。
- `V4` 快照完整性：快照必须包含记录时数据库的所有数据。
- `V5` 结构闭环性：`R1~R4` 输出能力并集必须覆盖 `C1~C8`。
- `V6` 边界符合性：所有有效组合必须满足绑定的参数边界。
- `V7` 最小必要性：移除任一 `B*` 后，`V3` 或 `V4` 至少一项失败。
- `V8` 结论表达：逐条输出 `R* -> C* + 边界绑定` 或 `R* -> N* + 边界绑定` 的通过或失败结论。