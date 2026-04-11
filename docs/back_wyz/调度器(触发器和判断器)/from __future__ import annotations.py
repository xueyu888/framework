from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Protocol, Any, Set


# =========================
# 异常定义
# =========================

class SchedulerError(Exception):
    """调度器基础异常"""
    pass


class InvalidInputError(SchedulerError):
    """非法输入异常"""
    pass


class MappingConfigError(SchedulerError):
    """映射配置异常"""
    pass


# =========================
# 数据结构
# =========================

@dataclass(frozen=True)
class InputRequest:
    """
    对应:
    struct 输入请求 := <tag_in, content_in>
    """
    tag_in: str
    content_in: Any


@dataclass(frozen=True)
class OutputRequest:
    """
    对应:
    struct 输出请求 := <tag_out, content_out, module>
    """
    tag_out: str
    content_out: Any
    module: str


# =========================
# 目标模块协议
# =========================

class TargetModule(Protocol):
    """
    目标模块接口:
    调度器只负责转发，不负责业务处理
    """
    name: str

    def handle(self, request: OutputRequest) -> None:
        ...


# =========================
# 示例目标模块
# =========================

class StarGraphModule:
    name = "星型图"

    def handle(self, request: OutputRequest) -> None:
        print(f"[{self.name}] 收到请求: tag={request.tag_out}, content={request.content_out}")


class ParentTaskJudgeModule:
    name = "父任务完成状态判断器"

    def handle(self, request: OutputRequest) -> None:
        print(f"[{self.name}] 收到请求: tag={request.tag_out}, content={request.content_out}")


# =========================
# 调度器
# =========================

class Scheduler:
    """
    MODULE 调度器: Scheduler

    Goal:
        接收任务请求, 并按照预定义的任务请求表,
        把该请求一对一调度到对应的目标模块。
        调度器只负责识别请求并转发内容, 不负责具体业务处理。
    """

    # -------------------------
    # Boundary / Param
    # -------------------------

    INPUT_TAGS: Set[str] = {
        "子任务状态更新",
        "子任务状态更新完成",
        "父任务查找完成",
        "输出星型图",
        "父任务状态更新",
    }

    OUTPUT_TAGS: Set[str] = {
        "子任务状态更新",
        "父任务查找",
        "星型图查找",
        "父任务判断",
        "父任务状态更新",
    }

    TARGET_MODULES: Set[str] = {
        "星型图",
        "父任务完成状态判断器",
    }

    # relation[1:1] 事件映射
    EVENT_MAPPING: Dict[str, str] = {
        "子任务状态更新": "子任务状态更新",
        "子任务状态更新完成": "父任务查找",
        "父任务查找完成": "星型图查找",
        "输出星型图": "父任务判断",
        "父任务状态更新": "父任务状态更新",
    }

    # relation[|输出触发事件Tag集合|:|调用对象集合|] 触发事件-调用对象映射
    EVENT_TO_MODULE_MAPPING: Dict[str, str] = {
        "子任务状态更新": "星型图",
        "父任务查找": "星型图",
        "星型图查找": "星型图",
        "父任务判断": "父任务完成状态判断器",
        "父任务状态更新": "星型图",
    }

    def __init__(self, module_registry: Dict[str, TargetModule]):
        """
        module_registry:
            运行时模块注册表，key 必须与 TARGET_MODULES 中定义一致
        """
        self.module_registry = module_registry
        self._validate_configuration()

    # -------------------------
    # Principles 校验
    # -------------------------

    def _validate_configuration(self) -> None:
        """
        校验以下约束:
        1. 映射表完备性前提
        2. 调用对象映射完备性前提
        3. 注册模块完备性
        """

        # 1) 对任意 tag_in ∈ 输入请求Tag集合，存在且仅存在一个 tag_out
        if set(self.EVENT_MAPPING.keys()) != self.INPUT_TAGS:
            missing = self.INPUT_TAGS - set(self.EVENT_MAPPING.keys())
            extra = set(self.EVENT_MAPPING.keys()) - self.INPUT_TAGS
            raise MappingConfigError(
                f"事件映射配置不完备或存在非法键. missing={missing}, extra={extra}"
            )

        for tag_in, tag_out in self.EVENT_MAPPING.items():
            if tag_out not in self.OUTPUT_TAGS:
                raise MappingConfigError(
                    f"事件映射中存在非法输出标签: {tag_in} -> {tag_out}"
                )

        # 2) 对任意 tag_out ∈ 输出触发事件Tag集合，存在且仅存在一个 module
        if set(self.EVENT_TO_MODULE_MAPPING.keys()) != self.OUTPUT_TAGS:
            missing = self.OUTPUT_TAGS - set(self.EVENT_TO_MODULE_MAPPING.keys())
            extra = set(self.EVENT_TO_MODULE_MAPPING.keys()) - self.OUTPUT_TAGS
            raise MappingConfigError(
                f"触发事件-调用对象映射不完备或存在非法键. missing={missing}, extra={extra}"
            )

        for tag_out, module_name in self.EVENT_TO_MODULE_MAPPING.items():
            if module_name not in self.TARGET_MODULES:
                raise MappingConfigError(
                    f"触发事件-调用对象映射中存在非法模块: {tag_out} -> {module_name}"
                )

        # 3) 注册模块完备性
        missing_modules = self.TARGET_MODULES - set(self.module_registry.keys())
        if missing_modules:
            raise MappingConfigError(
                f"缺少目标模块注册: {missing_modules}"
            )

    # -------------------------
    # Spaces
    # -------------------------

    def is_legal_dispatch(self, input_request: InputRequest, output_request: OutputRequest) -> bool:
        """
        对应:
        合法调度空间 :=
        { <i, o> |
            i = <tag_in, content_in> ∈ Base.输入请求,
            o = <tag_out, content_out, module> ∈ Base.输出请求,
            <tag_in, tag_out> ∈ Base.事件映射,
            <tag_out, module> ∈ Base.触发事件-调用对象映射,
            content_out = content_in
        }
        """
        expected_tag_out = self.EVENT_MAPPING.get(input_request.tag_in)
        expected_module = self.EVENT_TO_MODULE_MAPPING.get(output_request.tag_out)

        return (
            input_request.tag_in in self.INPUT_TAGS
            and output_request.tag_out in self.OUTPUT_TAGS
            and expected_tag_out == output_request.tag_out
            and expected_module == output_request.module
            and input_request.content_in == output_request.content_out
        )

    # -------------------------
    # Core Behavior
    # -------------------------

    def schedule(self, request: InputRequest) -> OutputRequest:
        """
        只做识别与转发信息构造，不处理业务。

        对应:
        - 事件映射约束
        - 调用对象约束
        - 内容透传约束
        - 非法输入处理约束
        """
        # 非法输入处理约束
        if request.tag_in not in self.INPUT_TAGS:
            raise InvalidInputError(f"非法输入错误: 未知输入标签 '{request.tag_in}'")

        # 事件映射约束
        tag_out = self.EVENT_MAPPING[request.tag_in]

        # 调用对象约束
        module_name = self.EVENT_TO_MODULE_MAPPING[tag_out]

        # 内容透传约束
        return OutputRequest(
            tag_out=tag_out,
            content_out=request.content_in,
            module=module_name,
        )

    def dispatch(self, request: InputRequest) -> OutputRequest:
        """
        调度并转发到目标模块
        """
        output_request = self.schedule(request)
        target_module = self.module_registry[output_request.module]
        target_module.handle(output_request)
        return output_request


# =========================
# 示例运行
# =========================

if __name__ == "__main__":
    registry = {
        "星型图": StarGraphModule(),
        "父任务完成状态判断器": ParentTaskJudgeModule(),
    }

    scheduler = Scheduler(module_registry=registry)

    test_requests = [
        InputRequest("子任务状态更新", {"task_id": 1, "status": "running"}),
        InputRequest("子任务状态更新完成", {"task_id": 1, "status": "done"}),
        InputRequest("父任务查找完成", {"parent_task_id": 1001}),
        InputRequest("输出星型图", {"graph_id": "G-01"}),
        InputRequest("父任务状态更新", {"parent_task_id": 1001, "status": "done"}),
    ]

    for req in test_requests:
        result = scheduler.dispatch(req)
        print("调度结果:", result)
        print("-" * 60)

    # 非法输入示例
    try:
        scheduler.dispatch(InputRequest("未知事件", {"x": 1}))
    except InvalidInputError as e:
        print("捕获异常:", e)