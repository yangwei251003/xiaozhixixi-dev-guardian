"""Run the unmodified guardian CLI on an explicitly marked fictional project."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

REPOSITORY = Path(__file__).resolve().parents[1]
CLI = REPOSITORY / 'skills/guard-xiaozhixixi-development/scripts/guardian.py'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True, help='New, empty synthetic-only workspace')
    args = parser.parse_args()
    workspace = args.workspace.expanduser().resolve()
    if workspace.exists() and any(workspace.iterdir()):
        raise SystemExit('Use a new empty workspace; this demo never replaces existing content.')
    workspace.mkdir(parents=True, exist_ok=True)
    marker = workspace / '.guardian-synthetic-demo.json'
    marker.write_text(json.dumps({'synthetic': True, 'purpose': 'offline guardian demo'}), encoding='utf-8')
    project = workspace / 'project'
    shutil.copytree(REPOSITORY / 'examples/contract', project)
    results = workspace / 'results'
    results.mkdir()
    empty = workspace / 'empty-git-template'
    empty.mkdir()
    env = dict(os.environ)
    env.update({
        'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONUTF8': '1',
        'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
        'GIT_CONFIG_COUNT': '2', 'GIT_CONFIG_KEY_0': 'core.fsmonitor', 'GIT_CONFIG_VALUE_0': 'false',
        'GIT_CONFIG_KEY_1': 'core.hooksPath', 'GIT_CONFIG_VALUE_1': str(empty),
        'GIT_CEILING_DIRECTORIES': str(workspace),
    })
    git_available = shutil.which('git') is not None
    if git_available:
        initialized = subprocess.run(['git', 'init', '--initial-branch=synthetic-demo', '--template', str(empty), str(project)], cwd=workspace, env=env, capture_output=True, text=True, encoding='utf-8')
        if initialized.returncode != 0:
            raise SystemExit('Synthetic Git init failed; no fallback success is reported.')
    calls = []

    def sanitize(text: str) -> str:
        for old, new in [(str(project), '<SYNTHETIC_PROJECT>'), (str(CLI), '<GUARDIAN_CLI>'), (str(REPOSITORY), '<PLUGIN_REPOSITORY>'), (str(workspace), '<SYNTHETIC_WORKSPACE>')]:
            text = text.replace(old, new).replace(old.replace('\\', '/'), new)
            text = text.replace(old.replace('\\', '\\\\'), new)
        return text

    def call(label: str, arguments: list[str], expected: int) -> subprocess.CompletedProcess[str]:
        output = subprocess.run([sys.executable, str(CLI), *arguments], cwd=workspace, env=env, capture_output=True, text=True, encoding='utf-8')
        calls.append({'label': label, 'arguments': [sanitize(x) for x in arguments], 'exit_code': output.returncode, 'expected_exit_code': expected, 'stdout': sanitize(output.stdout), 'stderr': sanitize(output.stderr)})
        if output.returncode != expected:
            raise RuntimeError(f'{label}: exit {output.returncode}, expected {expected}')
        return output

    before = {p.relative_to(project).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in project.rglob('*') if p.is_file() and '.git' not in p.parts}
    p0 = call('stage-0 preflight with synthetic contract', ['preflight', '--project-root', str(project), '--stage', '0', '--task', '合成契约检查'], 0)
    payload = json.loads(p0.stdout)
    if not payload['ok'] or not payload['tool_matches']:
        raise RuntimeError('Preflight did not produce actual matching output')
    p1 = call('missing stage-1 research is rejected', ['preflight', '--project-root', str(project), '--stage', '1', '--task', '合成阶段记录'], 2)
    if 'research/stage-1-research.md' not in json.loads(p1.stdout)['missing']:
        raise RuntimeError('Missing research not reported')
    (project/'research/stage-1-research.md').write_text('# 合成阶段 1 占位\n\n只验证文件分支，不代表真实研究、测试或业务完成。\n', encoding='utf-8')
    call('stage-1 preflight after explicit synthetic fixture addition', ['preflight', '--project-root', str(project), '--stage', '1', '--task', '合成阶段记录'], 0)
    for stage in (0, 1):
        call(f'record fictional stage {stage}', ['record-stage', '--project-root', str(project), '--stage', str(stage), '--summary', f'合成阶段 {stage} 记录（非业务完成）', '--tests', '仅演示写入；此文本不证明业务测试通过', '--next', '补充真实项目证据后再决定后续'], 0)
    status_before = (project/'research/stage-status.json').read_bytes()
    call('handoff rejects unrecorded stage 2', ['handoff', '--project-root', str(project), '--completed', '0,2', '--next-stage', '3'], 1)
    rejected_no_write = not (project/'Progress.md').exists() and (project/'research/stage-status.json').read_bytes() == status_before
    if not rejected_no_write:
        raise RuntimeError('Rejected handoff changed state')
    call('handoff for recorded stages 0 and 1', ['handoff', '--project-root', str(project), '--completed', '0,1', '--next-stage', '2'], 0)
    call('missing required project-root argument', ['preflight', '--stage', '0', '--task', '合成'], 2)
    call('out-of-range stage', ['preflight', '--project-root', str(project), '--stage', '8', '--task', '合成'], 2)
    no_spec = workspace/'no-spec-project'
    no_spec.mkdir()
    call('project without SPEC is rejected', ['preflight', '--project-root', str(no_spec), '--stage', '0', '--task', '合成'], 1)
    originals_unchanged = all(hashlib.sha256((project/rel).read_bytes()).hexdigest() == checksum for rel, checksum in before.items())
    progress = (project/'Progress.md').read_text('utf-8')
    actual_status = json.loads((project/'research/stage-status.json').read_text('utf-8'))
    if not originals_unchanged or set(actual_status) != {'0', '1'} or '先完成联网调研并创建 research/stage-2-research.md' not in progress:
        raise RuntimeError('Unexpected synthetic output')
    if git_available and ('synthetic-demo' not in progress or '?? SPEC.md' not in progress):
        raise RuntimeError('Expected actual synthetic Git metadata not found')
    validation = {
        'synthetic': True, 'source_cli_unmodified': True,
        'cli_invocations': len(calls), 'all_expected_exit_codes_observed': True,
        'recorded_stages': sorted(actual_status), 'initial_contract_files_unchanged': originals_unchanged,
        'missing_research_exit': 2, 'missing_recorded_stage_exit': 1,
        'rejected_handoff_wrote_nothing': rejected_no_write,
        'missing_root_argument_exit': 2, 'out_of_range_stage_exit': 2, 'missing_SPEC_exit': 1,
        'git_available': git_available, 'isolated_git_repository_initialized': git_available,
        'actual_git_metadata_observed': git_available,
        'host_plugin_installed_or_invoked': False, 'real_business_project_read_or_written': False,
        'external_service_or_model_called': False, 'private_configuration_read': False,
        'stage_claims_are_fictional_not_business_acceptance': True,
    }
    (results/'validation.json').write_text(json.dumps(validation, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (results/'cli-transcript.json').write_text(json.dumps(calls, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (results/'Progress.synthetic.md').write_text(sanitize(progress), encoding='utf-8')
    (results/'stage-status.synthetic.json').write_text(json.dumps(actual_status, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(validation, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
