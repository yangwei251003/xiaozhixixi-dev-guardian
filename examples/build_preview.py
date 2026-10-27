"""Build a static report from the actual synthetic CLI run, never from business data."""
import argparse
import html
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    validation=json.loads((args.results/'validation.json').read_text('utf-8'))
    if validation.get('synthetic') is not True or validation.get('real_business_project_read_or_written') is not False:
        raise SystemExit('Only explicitly synthetic demo output is accepted')
    transcript=json.loads((args.results/'cli-transcript.json').read_text('utf-8'))
    progress=(args.results/'Progress.synthetic.md').read_text('utf-8')
    args.output.mkdir(parents=True,exist_ok=True)
    for name in ['validation.json','cli-transcript.json','Progress.synthetic.md','stage-status.synthetic.json']:
        source=(args.results/name).resolve(); target=(args.output/name).resolve()
        if source!=target: shutil.copyfile(source,target)
    shutil.copyfile(ROOT/'docs/workflow.svg',args.output/'workflow.svg') if (ROOT/'docs/workflow.svg').resolve()!=(args.output/'workflow.svg').resolve() else None
    e=html.escape
    rows=''.join(f'<tr><td>{e(row["label"])}</td><td><code>{row["exit_code"]}</code></td><td>{"符合预期" if row["exit_code"]==row["expected_exit_code"] else "异常"}</td></tr>' for row in transcript)
    cards=''.join(f'<details><summary>{e(row["label"])} · exit {row["exit_code"]}</summary><pre>{e("guardian.py "+" ".join(row["arguments"]))}</pre><pre>{e(row["stdout"]+row["stderr"])}</pre></details>' for row in transcript)
    content=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>小智析析开发守门员 · 合成 CLI 报告</title><link rel="icon" href="data:,"><style>
:root{{color-scheme:dark}}*{{box-sizing:border-box}}body{{margin:0;background:#081824;color:#e7f2f6;font:16px/1.7 system-ui,sans-serif}}main{{max-width:1080px;margin:auto;padding:44px 24px 70px}}.kicker{{letter-spacing:.13em;color:#6fdbc6;font-size:13px}}h1{{font-size:clamp(27px,5vw,44px);line-height:1.25;margin:12px 0}}h2{{font-size:23px;margin-top:32px}}p{{color:#bdd0dc}}.notice{{background:#153343;border:1px solid #3b7a87;padding:16px;border-radius:12px}}.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:24px 0}}.stat{{padding:20px;background:#102b3b;border:1px solid #244958;border-radius:14px}}strong{{color:#7be2c5}}.stat b{{font-size:30px;display:block}}img{{max-width:100%;height:auto;border-radius:14px}}table{{width:100%;border-collapse:collapse;table-layout:fixed}}td,th{{padding:12px;text-align:left;border-bottom:1px solid #294453;overflow-wrap:anywhere}}th{{color:#7be2c5}}pre{{background:#06121c;white-space:pre-wrap;overflow-wrap:anywhere;padding:16px;border-radius:10px;font:13px/1.7 ui-monospace,monospace}}details{{border:1px solid #284454;border-radius:10px;padding:14px;margin:12px 0}}summary{{cursor:pointer}}a{{color:#7be2c5}}footer{{margin-top:36px;color:#9fb4c2;font-size:14px}}@media(max-width:600px){{main{{padding:28px 16px}}.stats{{grid-template-columns:1fr}}td,th{{padding:9px 6px;font-size:14px}}}}
</style><main><div class="kicker">LOCAL WORKFLOW · SYNTHETIC CONTRACT</div><h1>小智析析开发守门员</h1><p>让阶段预检、人工证据记录和跨窗口交接有迹可循。</p><div class="notice"><strong>这是合成项目的真实离线 CLI 报告。</strong>未安装/调用实际宿主插件，未读取真实小智析析业务、私密配置或模型服务。记录中的“阶段完成”内容是明确虚构的演示输入，不能作为业务验收。下图是流程示意。</div><div class="stats"><div class="stat"><b>{len(transcript)}</b>实际 CLI 调用</div><div class="stat"><b>3</b>原有 pytest 另行本机通过</div><div class="stat"><b>0</b>真实业务 / 外部模型调用</div></div><img src="workflow.svg" alt="流程示意：合成 SPEC 与调研，原 CLI 预检，人工记录，Progress 交接；宿主触发未验"><h2>观测到的退出码</h2><table><thead><tr><th>合成场景</th><th>退出码</th><th>结果</th></tr></thead><tbody>{rows}</tbody></table><p>退出码 0/2/1 都包含预期分支；匹配结果不证明调研质量、测试真实性或工具已经安装。Git 元数据来自新建的隔离合成仓库，不联系远端。</p><h2>实际命令与输出</h2>{cards}<h2>生成的交接（合成）</h2><pre>{e(progress)}</pre><footer>可下载 <a href="validation.json">验证数据</a> · <a href="cli-transcript.json">真实调用记录</a> · <a href="Progress.synthetic.md">合成交接文件</a>。路径已替换为占位符；这里是只读报告，没有在线改项目功能。</footer></main></html>'''
    (args.output/'index.html').write_text(content,encoding='utf-8')
    print(json.dumps({'synthetic':True,'calls':len(transcript),'output_files':6,'external_assets':0},ensure_ascii=False))

if __name__=='__main__': main()
