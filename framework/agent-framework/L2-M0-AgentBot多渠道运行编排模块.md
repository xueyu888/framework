# Agent Bot 多渠道运行编排模块:AgentBotMultiChannelRuntimeOrchestration

@framework

本模块收敛 agent bot 的多渠道运行编排结构。它只负责 6 件事：消息怎么进入并定位会话、渠道事件怎么和消息总线解耦、提示上下文怎么由身份文件/技能/记忆/历史装配、模型与工具调用怎么循环直到产出结果、会话与长期记忆怎么持久化和整理、后台任务怎么被触发并回投；不负责具体渠道 SDK 选型、业务工具语义、界面文案、桥接服务实现和具体供应商名单。

## 1. 能力声明（Capability Statement）

- `C1` 会话入口定位能力：把渠道标识、聊天标识、发送者标识与会话键收敛为稳定对话入口。
- `C2` 渠道适配与事件收发能力：把平台消息、入站事件、出站结果与渠道发送动作收敛为稳定渠道收发线。
- `C3` 提示上下文装配能力：把身份说明、引导文件、长期记忆、技能摘要、运行时元数据与会话历史收敛为稳定提示上下文。
- `C4` 模型与工具循环能力：把 provider 选择、模型调用、tool call 解析、工具执行与结果回填收敛为稳定 agent 主循环。
- `C5` 会话持久化与记忆整理能力：把 JSONL 会话、长期记忆、历史记录与整理游标收敛为稳定记忆延续线。
- `C6` 后台任务延续能力：把子代理、定时任务、心跳检查与结果回投收敛为稳定后台延续线。
- `C7` 非能力项：不负责具体渠道 SDK 细节、供应商商业策略、业务插件语义、桥接实现和界面交互文案。

## 2. 边界定义（Boundary / 参数）

- `SESSIONKEY` 会话键边界：同一入站消息必须稳定映射到一个会话键；未显式覆盖时，会话键必须由 `channel:chat_id` 唯一确定。来源：`C1 + C5`。
- `CHANNELSET` 渠道集合边界：只有已启用并完成初始化的渠道才能接收入站事件和发送出站消息。来源：`C1 + C2 + C6`。
- `WORKROOT` 工作区边界：身份文件、引导文件、技能目录、记忆目录与会话目录只能来自声明过的 workspace 根目录。来源：`C3 + C5 + C6`。
- `CTXSET` 上下文装配边界：system prompt 与调用消息只能由身份说明、引导文件、长期记忆、技能索引、运行时元数据与会话历史组成。来源：`C3 + C4`。
- `PROVIDERSET` 模型提供商边界：可调用模型与 provider 只能来自注册表或显式配置过的 provider 集合。来源：`C4`。
- `ITERMAX` 工具迭代边界：一次 agent 处理允许的 tool call 轮数上限必须显式声明；超过上限必须稳定终止。来源：`C4`。
- `MEMWINDOW` 记忆窗口边界：会话保留窗口、整理触发条件与 `last_consolidated` 推进规则必须显式声明。来源：`C5`。
- `TASKSET` 后台任务边界：允许的后台延续类型只能来自子代理、cron 与 heartbeat 三类触发集合，且回投目标必须显式可路由。来源：`C6`。

## 3. 最小可行基（Minimum Viable Bases）

- `B1` 入出站消息总线：L1.M0[R1,R3]：接收入站事件、排队出站事件，能根据渠道发布和 agent 回写输出下一条待处理入站事件或待发送出站事件。来源：`C1 + C2 + SESSIONKEY + CHANNELSET`。
- `B2` 渠道适配管理器：L1.M0[R1,R3]：负责已启用渠道的初始化、启动、停止与发送路由，能根据渠道名把出站结果投递到唯一渠道。来源：`C1 + C2 + CHANNELSET`。
- `B3` 会话记录存取器：L1.M0[R2]：维护会话键、JSONL 消息历史、会话元数据与整理游标，能根据 `SESSIONKEY` 读取和持久化当前会话记录。来源：`C1 + C5 + SESSIONKEY + MEMWINDOW`。
- `B4` 提示上下文装配器：L1.M1[R1]：加载身份说明、引导文件、长期记忆、技能摘要与运行时元数据，能根据当前会话历史输出稳定 system prompt 和调用消息列表。来源：`C3 + WORKROOT + CTXSET`。
- `B5` Provider 注册表与选择器：L1.M1[R2]：登记 provider 注册元数据、模型前缀规则与 API 入口绑定，能根据 model 或 provider 配置定位唯一 LLM 调用入口。来源：`C4 + PROVIDERSET`。
- `B6` 工具注册表与执行器：L1.M1[R3]：登记可用工具 schema、工具名与执行入口，能根据 tool call 名称和参数校验并执行工具，输出工具结果文本。来源：`C4 + ITERMAX + WORKROOT`。
- `B7` Agent 主循环调度器：L1.M1[R4]：驱动当前消息序列、迭代状态与工具回填结果的推进，能根据模型响应输出下一轮调用或最终回复文本。来源：`C2 + C4 + ITERMAX`。
- `B8` 记忆与历史记录器：L1.M2[R1]：写入 `MEMORY.md`、`HISTORY.md` 与整理结果，能根据 `MEMWINDOW` 和旧消息输出更新后的长期记忆与历史记录。来源：`C5 + WORKROOT + MEMWINDOW`。
- `B9` 后台任务调度器：L1.M2[R2]：维护子代理任务、cron 任务、heartbeat 决策与回投目标，能根据 `TASKSET` 触发新的 agent 处理并在可路由时投递结果。来源：`C6 + CHANNELSET + TASKSET`。

## 4. 基组合原则（Base Combination Principles）

- `R1` 会话入口成立
  - `R1.1` 参与基：`B1 + B2 + B3`。
  - `R1.2` 组合方式：先由渠道适配管理器接收平台消息并转成入站事件，再由入出站消息总线发布入站事件，最后由会话记录存取器按 `SESSIONKEY` 建立或读取唯一会话。
  - `R1.3` 输出能力：`C1 + C2`。
  - `R1.4` 边界绑定：`SESSIONKEY/CHANNELSET`。
- `R2` 上下文成立
  - `R2.1` 参与基：`B3 + B4 + B8`。
  - `R2.2` 组合方式：先由会话记录存取器给出当前未整理历史，再由记忆与历史记录器给出长期记忆，最后由提示上下文装配器按 `CTXSET` 生成 system prompt 和调用消息列表。
  - `R2.3` 输出能力：`C3 + C5`。
  - `R2.4` 边界绑定：`WORKROOT/CTXSET/MEMWINDOW`。
- `R3` 模型调用成立
  - `R3.1` 参与基：`B4 + B5 + B7`。
  - `R3.2` 组合方式：由提示上下文装配器输出规范消息，由 Provider 注册表与选择器定位唯一模型入口，再由 Agent 主循环调度器完成一次模型调用。
  - `R3.3` 输出能力：`C3 + C4`。
  - `R3.4` 边界绑定：`CTXSET/PROVIDERSET/ITERMAX`。
- `R4` 工具循环成立
  - `R4.1` 参与基：`B6 + B7`。
  - `R4.2` 组合方式：当模型返回 tool call 时，由 Agent 主循环调度器交给工具注册表与执行器执行，并把结果回填到消息序列后继续迭代，直到返回最终文本或达到 `ITERMAX`。
  - `R4.3` 输出能力：`C4`。
  - `R4.4` 边界绑定：`WORKROOT/ITERMAX`。
- `R5` 回复投递成立
  - `R5.1` 参与基：`B1 + B2 + B7`。
  - `R5.2` 组合方式：由 Agent 主循环调度器把最终文本写入出站事件，再由入出站消息总线发布出站事件，最后由渠道适配管理器路由到目标渠道发送。
  - `R5.3` 输出能力：`C2 + C4`。
  - `R5.4` 边界绑定：`CHANNELSET/SESSIONKEY`。
- `R6` 记忆整理成立
  - `R6.1` 参与基：`B3 + B7 + B8`。
  - `R6.2` 组合方式：当会话达到整理条件时，由 Agent 主循环调度器触发记忆与历史记录器把旧消息写入 `HISTORY.md`、更新 `MEMORY.md`，并推进会话整理游标。
  - `R6.3` 输出能力：`C5`。
  - `R6.4` 边界绑定：`WORKROOT/MEMWINDOW`。
- `R7` 后台延续成立
  - `R7.1` 参与基：`B1 + B7 + B9`。
  - `R7.2` 组合方式：由后台任务调度器根据 cron、heartbeat 或子代理完成事件触发新的 agent 处理，并在目标渠道可路由时把结果回投到消息总线。
  - `R7.3` 输出能力：`C6`。
  - `R7.4` 边界绑定：`CHANNELSET/TASKSET/SESSIONKEY`。
- `R8` Agent Bot 运行闭环成立
  - `R8.1` 参与基：`B1 + B2 + B3 + B4 + B5 + B6 + B7 + B8 + B9`。
  - `R8.2` 组合方式：把会话入口、上下文装配、模型调用、工具循环、回复投递、记忆整理和后台延续接成一条完整 agent bot 运行闭环。
  - `R8.3` 输出能力：`C1 + C2 + C3 + C4 + C5 + C6`。
  - `R8.4` 边界绑定：`SESSIONKEY/CHANNELSET/WORKROOT/CTXSET/PROVIDERSET/ITERMAX/MEMWINDOW/TASKSET`。
- `R9` 禁止组合
  - `R9.1` 参与基：`B1 + B2 + B3 + B4 + B5 + B6 + B7 + B8 + B9`。
  - `R9.2` 组合方式：会话键不稳定、未启用渠道仍可发送、上下文读取 workspace 外内容、未注册 provider 仍被调用、工具结果未回填就继续下一轮、记忆整理不推进游标或后台任务没有可路由目标的组合无效。
  - `R9.3` 输出能力：`C7`。
  - `R9.4` 边界绑定：`SESSIONKEY/CHANNELSET/WORKROOT/CTXSET/PROVIDERSET/ITERMAX/MEMWINDOW/TASKSET`。

## 5. 验证（Verification）

- `V1` 会话唯一性：同一入站消息必须稳定映射到一个 `SESSIONKEY`；未显式覆盖时，相同 `channel + chat_id` 必须进入同一会话。
- `V2` 渠道路由有效性：只有 `CHANNELSET` 内渠道可以接收和发送；未知或未启用渠道不得通过 `R1/R5`。
- `V3` 上下文装配有效性：通过 `R2` 生成的上下文必须只包含 `CTXSET` 允许的组成块，且文件来源不得越出 `WORKROOT`。
- `V4` 模型与工具循环有效性：通过 `R3/R4` 的一次处理必须在 `ITERMAX` 内得到最终文本或稳定终止；每次 tool call 后必须先写入 tool result 再进入下一轮。
- `V5` Provider 选择有效性：通过 `R3` 的模型调用必须只能落到 `PROVIDERSET` 内一个明确 provider 入口。
- `V6` 记忆整理有效性：达到 `MEMWINDOW` 条件后，旧消息必须被写入 `HISTORY.md` 或整合到 `MEMORY.md`，且 `last_consolidated` 必须推进。
- `V7` 后台任务延续有效性：通过 `R7` 触发的 cron、heartbeat 和子代理结果必须能再次进入 agent 处理链，并在目标可路由时完成回投。
- `V8` 最小必要性：移除任一 `B*` 后，`V2~V7` 至少一项失败。
- `V9` 结论表达：逐条输出 `R* -> C* / 边界` 的通过或失败结论。
