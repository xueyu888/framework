from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from framework_ir.parser import parse_framework_module
from project_runtime.correspondence_contracts import boundary_field_name
from project_runtime.framework_layer import _boundary_name_to_section


FRAMEWORK_TEXT = """# 测试参数模块:DemoParameterModule

@framework

## 1. 能力声明（Capability Statement）

- `C1` 查询承接能力：支持承接查询输入。

## 2. 边界定义（Boundary / Parameter 参数）

- `query_in` 查询输入参数：用于约束查询入口。来源：`C1`。
- `Result_OUT` 结果输出参数：用于约束结果出口。来源：`C1`。

## 3. 最小结构基（Minimal Structural Bases）

- `B1` 查询结构基：由查询文本与结果出口约束组成。来源：`C1 + query_in + Result_OUT`。

## 4. 基组合原则（Base Combination Principles）

- `R1` 查询闭合规则
  - `R1.1` 参与基：`B1`。
  - `R1.2` 组合方式：查询入口与结果出口同时约束同一个查询实例。
  - `R1.3` 输出能力：`C1`。
  - `R1.4` 参数绑定：`query_in + Result_OUT`。

## 5. 验证（Verification）

- `V1` 闭环验证：查询输入与结果输出约束必须能稳定导出查询承接能力。
"""


class FrameworkIrParserTest(unittest.TestCase):
    def test_parser_accepts_snake_case_and_mixed_case_boundary_ids(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp_dir:
            framework_file = Path(tmp_dir) / "L9-M9-测试参数模块.md"
            framework_file.write_text(FRAMEWORK_TEXT, encoding="utf-8")

            module = parse_framework_module(framework_file)

        self.assertEqual(tuple(item.boundary_id for item in module.boundaries), ("query_in", "Result_OUT"))
        self.assertEqual(module.boundaries[0].source_ref.anchor, "boundary:query_in")
        self.assertEqual(module.boundaries[1].source_ref.anchor, "boundary:result_out")
        self.assertEqual(module.rules[0].boundary_bindings, ("query_in", "Result_OUT"))

    def test_boundary_projection_names_normalize_to_lowercase(self) -> None:
        self.assertEqual(_boundary_name_to_section("query_in"), "query_in")
        self.assertEqual(_boundary_name_to_section("Result_OUT"), "result_out")
        self.assertEqual(boundary_field_name("Result_OUT"), "result_out")


if __name__ == "__main__":
    unittest.main()
