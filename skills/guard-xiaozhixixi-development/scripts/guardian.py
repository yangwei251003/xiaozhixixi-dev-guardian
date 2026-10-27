from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path


def project_root(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    if not (root / "SPEC.md").is_file():
        raise SystemExit(f"SPEC.md not found under {root}")
    return root


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def table_rows(markdown: str) -> list[str]:
    return [line.strip() for line in markdown.splitlines() if line.strip().startswith("|") and "---" not in line]


def research_path(root: Path, stage: int) -> Path:
    if stage == 0:
        return root / "research" / "调研报告.md"
    return root / "research" / f"stage-{stage}-research.md"


def preflight(args: argparse.Namespace) -> int:
    root = project_root(args.project_root)
    skills_map = root / "research" / "skills-map.md"
    research = research_path(root, args.stage)
    missing = [p.relative_to(root).as_posix() for p in (skills_map, research) if not p.is_file()]
    rows = table_rows(read_text(skills_map))
    needles = {str(args.stage), f"阶段 {args.stage}", f"阶段{args.stage}"}
    needles.update(word.lower() for word in args.task.replace("/", " ").replace("-", " ").split() if len(word) > 1)
    matches = [row for row in rows if any(needle in row.lower() for needle in needles)]
    result = {
        "ok": not missing and bool(matches),
        "stage": args.stage,
        "task": args.task,
        "research": str(research),
        "missing": missing,
        "tool_matches": matches,
        "next_actions": ["Read the stage research", "Load and announce matched Skills", "Define a failing test or observable acceptance check"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def status_path(root: Path) -> Path:
    return root / "research" / "stage-status.json"


def load_status(root: Path) -> dict[str, dict[str, str]]:
    path = status_path(root)
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def record_stage(args: argparse.Namespace) -> int:
    root = project_root(args.project_root)
    data = load_status(root)
    data[str(args.stage)] = {
        "completed_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "summary": args.summary,
        "tests": args.tests,
        "next": args.next,
    }
    path = status_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded stage {args.stage} in {path}")
    return 0


def git_output(root: Path, *command: str) -> str:
    try:
        return subprocess.run(["git", *command], cwd=root, check=False, capture_output=True, text=True, encoding="utf-8").stdout.strip()
    except OSError:
        return "git unavailable"


def handoff(args: argparse.Namespace) -> int:
    root = project_root(args.project_root)
    stages = [item.strip() for item in args.completed.split(",") if item.strip()]
    data = load_status(root)
    missing = [stage for stage in stages if stage not in data]
    if missing:
        raise SystemExit(f"Missing recorded stage evidence: {', '.join(missing)}")
    completed = "\n".join(
        f"- 阶段 {stage}: {data[stage]['summary']}\n  - 验证: {data[stage]['tests']}\n  - 后续: {data[stage]['next']}"
        for stage in stages
    )
    branch = git_output(root, "branch", "--show-current") or "未建立分支"
    status = git_output(root, "status", "--short") or "clean"
    commits = git_output(root, "log", "-5", "--oneline") or "暂无提交"
    next_research_path = research_path(root, args.next_stage)
    next_research = next_research_path.relative_to(root).as_posix()
    if next_research_path.is_file():
        research_instruction = f"阅读 {next_research}"
        research_status = f"已存在，先阅读 `{next_research}`"
    else:
        research_instruction = f"先完成联网调研并创建 {next_research}"
        research_status = f"尚未创建；先完成联网调研并创建 `{next_research}`"
    prompt = (
        f"请在 {root} 继续开发小智析析。先完整阅读 SPEC.md、Progress.md 和 research/skills-map.md，"
        f"{research_instruction}，再调用 $guard-xiaozhixixi-development 对阶段 {args.next_stage} 做 preflight，"
        "确认当前 Git 状态和测试基线后再继续。不得显示 backend/.env 的值。"
    )
    body = f"""# Progress.md — 小智析析跨窗口交接

更新时间：{dt.datetime.now().astimezone().isoformat(timespec='seconds')}

## 已完成阶段

{completed}

## 关键决策

- `SPEC.md` 是唯一产品规格；`research/skills-map.md` 是每项任务前的工具入口。
- 每阶段实现前先完成联网调研并写入对应 research 文件。
- 真实失败不得由模拟业务结果掩盖；密钥只从本地 `backend/.env` 读取。

## Git 与工作区

- 分支：`{branch}`
- 最近提交：

```text
{commits}
```

- 未提交状态：

```text
{status}
```

## 下一阶段

- 阶段：{args.next_stage}
- 调研文件：{research_status}
- 开始前：运行开发守门员 preflight，加载匹配的 Skill/插件，并确认测试基线。

## 新窗口必须提供

- 仓库路径、`SPEC.md`、本文件、`research/skills-map.md`、下一阶段调研文件。
- 说明本地 `backend/.env` 已配置，但不要复制或粘贴任何密钥值。

## 新窗口提示词

```text
{prompt}
```
"""
    output = root / "Progress.md"
    output.write_text(body, encoding="utf-8")
    print(f"Wrote {output}")
    print(prompt)
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="小智析析阶段开发守门工具")
    commands = result.add_subparsers(dest="command", required=True)
    check = commands.add_parser("preflight")
    check.add_argument("--project-root", required=True)
    check.add_argument("--stage", type=int, choices=range(8), required=True)
    check.add_argument("--task", required=True)
    check.set_defaults(handler=preflight)
    record = commands.add_parser("record-stage")
    record.add_argument("--project-root", required=True)
    record.add_argument("--stage", type=int, choices=range(8), required=True)
    record.add_argument("--summary", required=True)
    record.add_argument("--tests", required=True)
    record.add_argument("--next", required=True)
    record.set_defaults(handler=record_stage)
    transfer = commands.add_parser("handoff")
    transfer.add_argument("--project-root", required=True)
    transfer.add_argument("--completed", required=True, help="Comma-separated stages, for example 0,1")
    transfer.add_argument("--next-stage", type=int, choices=range(8), required=True)
    transfer.set_defaults(handler=handoff)
    return result


if __name__ == "__main__":
    arguments = parser().parse_args()
    raise SystemExit(arguments.handler(arguments))
