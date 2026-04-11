from dataclasses import dataclass
from typing import Dict, Literal, TypedDict


TaskStatus = Literal["unfinish", "finish"]
ErrorCode = Literal["None", "任务不存在", "任务原状态为已完成"]


class Output(TypedDict):
    err_code: ErrorCode
    task_status_updated: int
    task_collection_status_updated: int
    updated_task_set: Dict[str, TaskStatus]


@dataclass
class TaskCompletionStatusJudgeModule:
    """
    任务集合完成状态判断模块

    Goal:
        传入任务集合, 并传入某一任务ID,
        判断该任务状态是否更新, 以及任务集合状态是否更新。
        最终返回更新后的任务集合状态。
        若中间出现非法情况则返回错误。
    """

    @staticmethod
    def judge(task_set: Dict[str, TaskStatus], task_id: str) -> Output:
        """
        参数:
            task_set: 任务状态集合, 例如:
                {
                    "task1": "unfinish",
                    "task2": "finish"
                }
            task_id: 目标任务ID

        返回:
            {
                "err_code": 错误码,
                "task_status_updated": 是否更新目标任务状态(0/1),
                "task_collection_status_updated": 是否更新任务集合状态(0/1),
                "updated_task_set": 更新后的任务集合
            }
        """

        # 拷贝，避免直接修改输入
        updated_task_set = dict(task_set)

        # ---------------------------
        # E1: 任务存在判断
        # E1 = 1[b ∈ Children(A)]
        # ---------------------------
        E1 = int(task_id in updated_task_set)

        # ---------------------------
        # E2: 任务原状态判断
        # E2 = 1[status(b) != finish] || ~E1
        # 解释:
        #   1 = 任务不存在 或 任务存在但未完成
        #   0 = 任务存在且已完成
        # ---------------------------
        if E1 == 1:
            E2 = int(updated_task_set[task_id] != "finish")
        else:
            E2 = 1

        # ---------------------------
        # E3: 任务原状态为已完成判断
        # E3 = E1 & ~E2
        # ---------------------------
        E3 = int(E1 == 1 and E2 == 0)

        # ---------------------------
        # E4: 任务状态更新判断
        # E4 = E1 & E2
        # 即: 任务存在且原状态不是finish时，可以更新
        # ---------------------------
        E4 = int(E1 == 1 and E2 == 1)

        # 若可更新，则将目标任务更新为 finish
        if E4 == 1:
            updated_task_set[task_id] = "finish"

        # ---------------------------
        # E5: 任务集合状态更新判断
        # E5 = 1[∀ c ∈ Children(A) \ {目标任务}, status(c) = finish] & (E3 || E4)
        #    = 1[∀ c ∈ Children(A) \ {目标任务}, status(c) = finish] & E1
        #
        # 解释:
        #   只要目标任务存在，并且除目标任务外其他任务都已完成，
        #   则任务集合状态更新为已完成。
        # ---------------------------
        if E1 == 1:
            other_tasks_all_finished = all(
                status == "finish"
                for tid, status in updated_task_set.items()
                if tid != task_id
            )
            E5 = int(other_tasks_all_finished)
        else:
            E5 = 0

        # ---------------------------
        # 错误码计算
        # ERR_1 | default -> "None"
        # ERR_2 | ~E1     -> "任务不存在"
        # ERR_3 | E3      -> "任务原状态为已完成"
        # ---------------------------
        if E1 == 0:
            err_code: ErrorCode = "任务不存在"
        elif E3 == 1:
            err_code = "任务原状态为已完成"
        else:
            err_code = "None"

        return {
            "err_code": err_code,
            "task_status_updated": E4,
            "task_collection_status_updated": E5,
            "updated_task_set": updated_task_set,
        }
    

if __name__ == "__main__":
    
    task_set = {
        "任务1": "finish",
        "任务2": "unfinish",
        "任务3": "finish"
    }

    result = TaskCompletionStatusJudgeModule.judge(task_set, "任务2")
    print(result)