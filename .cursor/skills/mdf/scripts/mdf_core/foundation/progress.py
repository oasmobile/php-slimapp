"""检查阶段的实时 stderr 输出；stdout 留给结构化结果。"""
import sys
import time
from contextlib import contextmanager
from contextvars import ContextVar
from threading import RLock
from typing import Callable, Iterator, Sequence, TypeVar

T = TypeVar("T")
_OUTPUT_LOCK = RLock()
_STAGE = ContextVar("inspection_stage", default="")
_GROUPS = ContextVar("inspection_groups", default=None)
_LOCAL_GROUPS = ContextVar("local_inspection_groups", default=None)


class ProgressGroups:
    """单次命令共享的计数组；登记顺序决定稳定编号，状态按实际完成更新。"""

    def __init__(self, labels: Sequence[str]):
        self.states = dict.fromkeys(labels, "待开始")
        self.discovery_pending = True

    def summary(self) -> str:
        counts = {state: list(self.states.values()).count(state)
                  for state in ("完成", "运行", "待开始", "中断", "跳过")}
        running = "、".join(f"组 {index}" for index, state in enumerate(self.states.values(), 1) if state == "运行")
        fields = [f"共 {len(self.states)} 组"] + [f"{state} {count}" for state, count in counts.items()]
        if running:
            fields.append(f"运行中：{running}")
        if self.discovery_pending:
            fields.append("后续分组待扫描")
        return "｜".join(fields)


def register_progress_groups(labels: Sequence[str], *, reason: str) -> None:
    groups = _GROUPS.get()
    if groups is None:
        return
    with _OUTPUT_LOCK:
        previous = len(groups.states)
        for label in labels:
            groups.states.setdefault(label, "待开始")
        groups.discovery_pending = False
        report_progress("计数组清单", f"{reason}，组数 {previous} → {len(groups.states)}；"
                        + "；".join(f"组 {index}：{label}" for index, label in enumerate(groups.states, 1)))
        report_progress("计数组汇总", groups.summary())


def report_count(label: str, completed: int, total: int, detail: str = "") -> None:
    with _OUTPUT_LOCK:
        groups = _GROUPS.get()
        if groups is not None:
            groups.states[label] = "完成" if completed == total else "运行"
            local = _LOCAL_GROUPS.get()
            if local is not None:
                local.add(label)
        report_progress(label, f"已检查 {completed}/{total}{detail}")


def skip_progress_group(label: str, reason: str) -> None:
    with _OUTPUT_LOCK:
        groups = _GROUPS.get()
        if groups is not None:
            groups.states[label] = "跳过"
        report_progress(label, f"跳过本组：{reason}")


def report_progress(label: str, message: str) -> None:
    with _OUTPUT_LOCK:
        prefix = f"[{_STAGE.get()}] " if _STAGE.get() else ""
        groups = _GROUPS.get()
        if groups is not None and label in groups.states:
            index = list(groups.states).index(label) + 1
            prefix += f"[计数组：{groups.summary()}] [组 {index}] "
        print(f"{prefix}[{label}] {message}", file=sys.stderr, flush=True)


class ProgressPlan:
    """固定阶段清单；子检查继承当前阶段，不把局部完成当作整体完成。"""

    def __init__(self, label: str, stages: Sequence[str], *, groups: Sequence[str] = ()):
        self.label = label
        self.stages = tuple(stages)
        self.groups = ProgressGroups(groups)
        roadmap = " → ".join(f"{index}. {name}" for index, name in enumerate(stages, 1))
        report_progress(label, f"全局共 {len(stages)} 个阶段：{roadmap}")
        report_progress("计数组清单", "；".join(f"组 {index}：{name}" for index, name in enumerate(groups, 1)))
        report_progress("计数组汇总", self.groups.summary())

    @contextmanager
    def stage(self, index: int):
        total = len(self.stages)
        label = f"{self.label} {index}/{total}：{self.stages[index - 1]}"
        token = _STAGE.set(f"全局 {self.label} 阶段 {index}/{total}，已完成 {index - 1}/{total}")
        group_token = _GROUPS.set(self.groups)
        try:
            with progress(label):
                yield
                report_progress("计数组汇总", self.groups.summary())
                _STAGE.set(f"全局 {self.label} 阶段 {index}/{total}，已完成 {index}/{total}")
        except BaseException:
            with _OUTPUT_LOCK:
                for name, state in self.groups.states.items():
                    if state == "运行":
                        self.groups.states[name] = "中断"
                report_progress("计数组汇总", self.groups.summary())
            raise
        finally:
            _GROUPS.reset(group_token)
            _STAGE.reset(token)


def progress_items(
    label: str, items: Sequence[T], describe: Callable[[T], str] = str,
) -> Iterator[T]:
    """处理前报告当前位置；只在调用方处理后增加已检查数。"""
    started = time.monotonic()
    total = len(items)
    for completed, item in enumerate(items):
        report_count(
            label, completed, total,
            f"，当前 {describe(item)}，"
            f"用时 {time.monotonic() - started:.1f}s",
        )
        yield item
    report_count(
        label, total, total, f"，用时 {time.monotonic() - started:.1f}s",
    )


@contextmanager
def progress(label: str):
    started = time.monotonic()
    local: set[str] = set()
    token = _LOCAL_GROUPS.set(local)
    report_progress(label, "开始")
    try:
        yield
    except BaseException:
        with _OUTPUT_LOCK:
            groups = _GROUPS.get()
            if groups is not None:
                for name in local:
                    if groups.states.get(name) == "运行":
                        groups.states[name] = "中断"
                report_progress("计数组汇总", groups.summary())
            report_progress(label, f"中断，用时 {time.monotonic() - started:.1f}s")
        raise
    else:
        report_progress(label, f"检查结束，用时 {time.monotonic() - started:.1f}s")
    finally:
        _LOCAL_GROUPS.reset(token)
