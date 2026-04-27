import unittest

from src.adif_manage.record_flow import REQUIRED_FIELD_SEQUENCE, run_record_interaction

_REQUIRED_FIELDS_ORDER = [field_name for _, field_name, _, _ in REQUIRED_FIELD_SEQUENCE]
_REQUIRED_FIELD_COUNT = len(REQUIRED_FIELD_SEQUENCE)


class TestRecordFlow(unittest.TestCase):
    def _run(self, inputs, last_fields=None):
        output = []
        iterator = iter(inputs)

        def read_line():
            return next(iterator)

        def write_out(text):
            output.append(text)

        result = run_record_interaction(read_line, write_out, last_fields)
        return result, "".join(output)

    def _fill_required_inputs(self, overrides=None):
        defaults: dict[str, str] = {
            "QSO_DATE": "20260101",
            "TIME_ON": "120000",
            "CALL": "BA1AA",
            "FREQ": "14.250",
            "MODE": "SSB",
            "RST_SENT": "",
            "RST_RCVD": "",
            "TX_PWR": "",
            "RX_PWR": "",
            "QTH": "",
            "RIG": "",
            "MY_ANTENNA": "",
            "APP_ADIFMANAGE_WX": "",
        }
        if overrides:
            defaults.update(overrides)
        return [f"{defaults[field]}\n" for field in _REQUIRED_FIELDS_ORDER]

    def test_record_minimal_required(self):
        result, _ = self._run(self._fill_required_inputs() + ["0\n"])
        self.assertIsNotNone(result)
        fields, snapshot = result
        self.assertEqual(fields["CALL"], "BA1AA")
        self.assertEqual(fields["QSO_DATE"], "20260101")
        self.assertNotIn("RST_SENT", fields)

    def test_record_with_optional_fields(self):
        inputs = self._fill_required_inputs({
            "RST_SENT": "599",
            "RST_RCVD": "599",
            "QTH": "Beijing",
        }) + ["0\n"]
        result, _ = self._run(inputs)
        self.assertIsNotNone(result)
        fields, _ = result
        self.assertEqual(fields["RST_SENT"], "599")
        self.assertEqual(fields["RST_RCVD"], "599")
        self.assertEqual(fields["QTH"], "Beijing")
        self.assertNotIn("TX_PWR", fields)

    def test_record_required_field_cannot_skip_with_empty(self):
        inputs = ["\n"] + self._fill_required_inputs() + ["0\n"]
        result, output = self._run(inputs)
        self.assertIsNotNone(result)
        self.assertIn("此字段为必填，不能跳过", output)

    def test_record_required_field_cannot_skip_with_dash(self):
        inputs = ["-\n"] + self._fill_required_inputs() + ["0\n"]
        result, output = self._run(inputs)
        self.assertIsNotNone(result)
        self.assertIn("此字段为必填，不能跳过", output)

    def test_record_optional_field_skip_with_dash(self):
        inputs = self._fill_required_inputs({
            "RST_SENT": "-",
            "RST_RCVD": "-",
        }) + ["0\n"]
        result, _ = self._run(inputs)
        self.assertIsNotNone(result)
        fields, _ = result
        self.assertNotIn("RST_SENT", fields)
        self.assertNotIn("RST_RCVD", fields)

    def test_record_qf_completes(self):
        inputs = self._fill_required_inputs() + ["qf\n"]
        result, _ = self._run(inputs)
        self.assertIsNotNone(result)
        fields, _ = result
        self.assertEqual(fields["CALL"], "BA1AA")

    def test_record_memory_reuse_last_value(self):
        last = {"CALL": "BA1AA", "QSO_DATE": "20260101", "QTH": "Beijing"}
        inputs = self._fill_required_inputs({
            "QSO_DATE": "",
            "CALL": "",
            "QTH": "",
        }) + ["0\n"]
        result, _ = self._run(inputs, last_fields=last)
        self.assertIsNotNone(result)
        fields, _ = result
        self.assertEqual(fields["QSO_DATE"], "20260101")
        self.assertEqual(fields["CALL"], "BA1AA")
        self.assertEqual(fields["QTH"], "Beijing")

    def test_record_snapshot_merges_last_and_new(self):
        last = {"QSO_DATE": "20260101", "RST_SENT": "599", "RIG": "IC-7300"}
        inputs = self._fill_required_inputs({
            "QSO_DATE": "20260115",
            "RST_SENT": "-",
        }) + ["0\n"]
        result, _ = self._run(inputs, last_fields=last)
        self.assertIsNotNone(result)
        fields, snapshot = result
        self.assertEqual(fields["QSO_DATE"], "20260115")
        self.assertNotIn("RST_SENT", fields)
        self.assertEqual(snapshot["QSO_DATE"], "20260115")
        self.assertEqual(snapshot["RST_SENT"], "599")
        self.assertEqual(snapshot["RIG"], "IC-7300")

    def test_record_snapshot_includes_new_optional(self):
        last: dict[str, str] = {}
        inputs = self._fill_required_inputs({"RST_SENT": "599"}) + ["0\n"]
        result, _ = self._run(inputs, last_fields=last)
        self.assertIsNotNone(result)
        fields, snapshot = result
        self.assertEqual(snapshot["RST_SENT"], "599")
        self.assertEqual(snapshot["CALL"], "BA1AA")

    def test_record_invalid_date_blocked_inline(self):
        result, output = self._run([
            "20261301\n", "20260101\n",
            "120000\n",
            "BA1AA\n",
            "14.250\n",
            "SSB\n",
            "\n", "\n", "\n", "\n", "\n", "\n", "\n", "\n",
            "0\n",
        ])
        self.assertIsNotNone(result)
        fields, _ = result
        self.assertEqual(fields["QSO_DATE"], "20260101")
        self.assertIn("日期无效", output)

    def test_record_invalid_date_format_inline(self):
        result, output = self._run([
            "notadate\n", "20260101\n",
            "120000\n",
            "BA1AA\n",
            "14.250\n",
            "SSB\n",
            "\n", "\n", "\n", "\n", "\n", "\n", "\n", "\n",
            "0\n",
        ])
        self.assertIsNotNone(result)
        fields, _ = result
        self.assertEqual(fields["QSO_DATE"], "20260101")
        self.assertIn("日期格式错误", output)

    def test_record_phase2_invalid_choice(self):
        inputs = self._fill_required_inputs() + ["999\n", "abc\n", "0\n"]
        result, output = self._run(inputs)
        self.assertIsNotNone(result)
        self.assertIn("编号超出范围", output)
        self.assertIn("输入无效", output)


if __name__ == "__main__":
    unittest.main()
