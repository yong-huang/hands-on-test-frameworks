"""核验：4 条负向按预期绿 + 1 条注入失败红 + Teardown 截图存在。"""
import glob
import os
from xml.etree import ElementTree as ET

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
r = ET.parse(os.path.join(out, "output.xml")).getroot()
tests = {t.attrib["name"]: t.find("status").attrib["status"] for t in r.iter("test")}
expected_green = [n for n in tests if n.startswith("负向")]
assert len(expected_green) == 4 and all(tests[n] == "PASS" for n in expected_green), tests
fails = [n for n, st in tests.items() if st == "FAIL"]
assert len(fails) == 1, f"应恰好 1 条注入失败：{fails}"
shots = glob.glob(os.path.join(out, "*.png")) + glob.glob(os.path.join(out, "selenium-screenshot-*.png"))
assert shots, f"Teardown 截图缺失（reports/ 下无 png）：{sorted(os.listdir(out))}"
print(f"✅ 负向 4 条全绿；注入失败 1 条已留证：{os.path.basename(shots[0])}")
