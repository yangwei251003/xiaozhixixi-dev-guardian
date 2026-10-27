from __future__ import annotations

import importlib.util
import json
from argparse import Namespace
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "guardian.py"
SPEC = importlib.util.spec_from_file_location("guardian", MODULE_PATH)
guardian = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(guardian)


def make_project(tmp_path: Path) -> Path:
    (tmp_path / "SPEC.md").write_text("# spec\n", encoding="utf-8")
    research = tmp_path / "research"
    research.mkdir()
    (research / "skills-map.md").write_text(
        "| 任务 | 工具 | 调用时机 | 理由 |\n|---|---|---|---|\n| 阶段0 GitHub 调研 | GitHub | 阶段 0 | 核验仓库 |\n",
        encoding="utf-8",
    )
    (research / "调研报告.md").write_text("# report\n", encoding="utf-8")
    return tmp_path


def test_preflight_passes_with_research_and_tool_mapping(tmp_path: Path, capsys) -> None:
    root = make_project(tmp_path)
    result = guardian.preflight(Namespace(project_root=str(root), stage=0, task="GitHub 调研"))
    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload["ok"] is True
    assert payload["tool_matches"]


def test_preflight_fails_when_stage_research_is_missing(tmp_path: Path, capsys) -> None:
    root = make_project(tmp_path)
    result = guardian.preflight(Namespace(project_root=str(root), stage=1, task="后端骨架"))
    payload = json.loads(capsys.readouterr().out)
    assert result == 2
    assert "research/stage-1-research.md" in payload["missing"]


def test_record_and_handoff_create_reusable_progress(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    for stage in (0, 1):
        guardian.record_stage(
            Namespace(
                project_root=str(root),
                stage=stage,
                summary=f"stage {stage} complete",
                tests="pytest passed",
                next="continue",
            )
        )
    result = guardian.handoff(Namespace(project_root=str(root), completed="0,1", next_stage=2))
    progress = (root / "Progress.md").read_text(encoding="utf-8")
    assert result == 0
    assert "阶段 0: stage 0 complete" in progress
    assert "阶段 1: stage 1 complete" in progress
    assert "guard-xiaozhixixi-development" in progress
    assert "先完成联网调研并创建 research/stage-2-research.md" in progress
