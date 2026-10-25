"""证据链核验：故意失败已留证（png + source.html），通过用例零附件。"""
import glob
import os

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
pngs = glob.glob(os.path.join(out, "FAIL_*.png"))
sources = glob.glob(os.path.join(out, "FAIL_*.source.html"))
assert pngs and sources, f"证据缺失：png={pngs} source={sources}"
assert len(pngs) == len(sources) == 1, f"应恰好 1 组证据，实得 {len(pngs)}/{len(sources)}"
assert all(os.path.getsize(p) > 10_000 for p in pngs), "截图小得可疑（<10KB）"
pass_evidence = [p for p in os.listdir(out) if p.startswith("test_pass")]
assert not pass_evidence, f"通过用例不该留证据：{pass_evidence}"
print(f"✅ 证据链核验通过：{os.path.basename(pngs[0])} + {os.path.basename(sources[0])}；通过用例零附件")
