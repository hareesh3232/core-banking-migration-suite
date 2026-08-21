import unittest
from etl.cleanser import parse_date, parse_currency, mask_ssn, mask_account_number, clean_record

class TestCleanser(unittest.TestCase):

    def test_parse_date_formats(self):
        self.assertEqual(parse_date("2024-05-15"), "2024-05-15")
        self.assertEqual(parse_date("05/15/2024"), "2024-05-15")
        self.assertEqual(parse_date("15-05-2024"), "2024-05-15")
        self.assertIsNone(parse_date("2024-13-45"))
        self.assertIsNone(parse_date(""))

    def test_parse_currency(self):
        self.assertEqual(parse_currency("$1,250.50"), 1250.50)
        self.assertEqual(parse_currency("1250.5 USD"), 1250.50)
        self.assertEqual(parse_currency("1250.5"), 1250.50)
        self.assertEqual(parse_currency(500), 500.0)
        self.assertIsNone(parse_currency(None))

    def test_mask_ssn(self):
        self.assertEqual(mask_ssn("123-45-6789"), "XXX-XX-6789")
        self.assertEqual(mask_ssn(""), "")

    def test_mask_account(self):
        self.assertEqual(mask_account_number("ACC-500001"), "****0001")
        self.assertEqual(mask_account_number("12345678"), "****5678")

    def test_clean_record_customer_validation(self):
        # Missing CustomerID
        record = {"SSN": "123-45-6789", "FirstName": "John"}
        _, is_valid, reason = clean_record(record, "Customer")
        self.assertFalse(is_valid)
        self.assertIn("Missing CustomerID", reason)

        # Valid Customer
        record2 = {"CustomerID": "CUST-101", "SSN": "123-45-6789", "FirstName": "Jane", "LastName": "Doe", "DateOfBirth": "1990-01-01"}
        cleansed, is_valid, reason = clean_record(record2, "Customer", mask_pii=True)
        self.assertTrue(is_valid)
        self.assertEqual(cleansed["SSN"], "XXX-XX-6789")

if __name__ == "__main__":
    unittest.main()
