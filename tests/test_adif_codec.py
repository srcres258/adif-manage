import unittest

from src.adif_manage.adif_codec import (
    missing_required_fields,
    parse_adi,
    to_adi,
    validate_core_field_formats,
)
from src.adif_manage.errors import AdifParseError


class TestAdifCodec(unittest.TestCase):
    def test_parse_and_write_roundtrip(self) -> None:
        content = "<EOH><QSO_DATE:8>20260101<TIME_ON:6>120000<CALL:5>BA1AA<MODE:3>SSB<BAND:3>20M<EOR>"
        records = parse_adi(content)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].fields["CALL"], "BA1AA")

        text = to_adi(records, adif_version="3.1.7", program_version="0.1.0")
        self.assertIn("<EOR>", text)
        self.assertIn("<CALL:5>BA1AA", text)

    def test_parse_invalid_length(self) -> None:
        content = "<EOH><CALL:10>BA1AA"
        with self.assertRaises(AdifParseError):
            parse_adi(content)

    def test_missing_required_fields(self) -> None:
        missing = missing_required_fields({"CALL": "BA1AA"})
        self.assertIn("QSO_DATE", missing)
        self.assertIn("FREQ/BAND", missing)

    def test_core_field_validation(self) -> None:
        self.assertIn("QSO_DATE", validate_core_field_formats({"QSO_DATE": "20261399"}))
        self.assertIn("TIME_ON", validate_core_field_formats({"TIME_ON": "256099"}))


if __name__ == "__main__":
    unittest.main()
