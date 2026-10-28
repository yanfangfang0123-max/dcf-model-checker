import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dcf_check import rebuild, review  # noqa: E402

INPUTS = json.loads((ROOT / "data" / "model_inputs.json").read_text())
REPORTED = json.loads((ROOT / "data" / "colleague_model_outputs.json").read_text())


class TestDCFCheck(unittest.TestCase):
    def test_correct_model_reconciles(self):
        d = rebuild(INPUTS)
        clean = {
            "fcff": d.fcff, "wacc": d.wacc, "sum_pv_fcff": sum(d.pv_fcff),
            "terminal_value": d.terminal_value, "pv_terminal_value": d.pv_terminal_value,
            "enterprise_value": d.enterprise_value, "equity_value": d.equity_value,
            "value_per_share": d.value_per_share,
        }
        text = "\n".join(review(INPUTS, clean))
        self.assertIn("All lines reconcile", text)

    def test_three_planted_errors_are_diagnosed(self):
        text = "\n".join(review(INPUTS, REPORTED))
        self.assertIn("3 issue(s) found", text)
        self.assertIn("working capital ADDED", text)
        self.assertIn("PRE-tax", text)
        self.assertIn("6 periods instead of 5", text)

    def test_hand_check_of_wacc(self):
        # 10.25% x 210/270 + 6.5% x (1 - 25%) x 60/270 = 9.0556%
        self.assertAlmostEqual(rebuild(INPUTS).wacc, 0.090556, places=5)


if __name__ == "__main__":
    unittest.main()
