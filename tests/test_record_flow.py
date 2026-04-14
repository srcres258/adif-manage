import unittest

from src.adif_manage.record_flow import ALL_QSO_FIELDS, run_record_interaction


class TestRecordFlow(unittest.TestCase):
    def _run(self, inputs: list[str]):
        output: list[str] = []
        iterator = iter(inputs)

        def read_line() -> str:
            return next(iterator)

        def write_out(text: str) -> None:
            output.append(text)

        result = run_record_interaction(read_line, write_out)
        return result, "".join(output)

    def _index(self, field_name: str) -> str:
        return str(ALL_QSO_FIELDS.index(field_name) + 1)

    def test_record_successful_completion(self) -> None:
        result, _ = self._run([
            f"{self._index('CALL')}\n", "BA1AA\n",
            f"{self._index('QSO_DATE')}\n", "20260101\n",
            f"{self._index('TIME_ON')}\n", "120000\n",
            f"{self._index('MODE')}\n", "SSB\n",
            f"{self._index('BAND')}\n", "20M\n",
            "q\n",
        ])
        if result is None:
            self.fail("record result should not be None")
        self.assertEqual(result["CALL"], "BA1AA")

    def test_record_qf_failure(self) -> None:
        result, output = self._run(["qf\n"])
        self.assertIsNone(result)
        self.assertIn("您未录入所有必填字段，QSO 记录失败", output)


if __name__ == "__main__":
    unittest.main()
