import unittest
import os
from database.db_engine import init_db, get_connection
from etl.loader import load_staging_data, execute_transformation_procedures
from etl.reconciler import generate_reconciliation_report

class TestDatabasePipeline(unittest.TestCase):

    def setUp(self):
        init_db()

    def test_end_to_end_migration(self):
        run_id = "TEST-RUN-001"
        conn = get_connection()
        cursor = conn.cursor()

        # Insert test migration run
        cursor.execute("INSERT OR REPLACE INTO Migration_Runs (RunID, Status, StartTime) VALUES (?, 'RUNNING', '2026-08-21T12:00:00')", (run_id,))
        conn.commit()

        # Insert staging data
        cursor.execute("INSERT INTO Staging_Customers (RunID, CustomerID, SSN, FirstName, LastName, DateOfBirth) VALUES (?, 'CUST-T1', '123-45-6789', 'Test', 'User', '1990-01-01')", (run_id,))
        cursor.execute("INSERT INTO Staging_Accounts (RunID, AccountNumber, CustomerID, AccountType, Balance) VALUES (?, 'ACC-T1', 'CUST-T1', 'CHECKING', '1000.00')", (run_id,))
        cursor.execute("INSERT INTO Staging_Transactions (RunID, TransactionID, AccountNumber, Amount, TransactionType) VALUES (?, 'TXN-T1', 'ACC-T1', '250.00', 'DEPOSIT')", (run_id,))
        conn.commit()
        conn.close()

        # Execute procedure transformation
        execute_transformation_procedures(run_id)

        # Verify Target tables loaded
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT FirstName FROM Target_Customers WHERE CustomerID = 'CUST-T1'")
        cust = cursor.fetchone()
        self.assertIsNotNone(cust)
        self.assertEqual(cust[0], 'Test')

        cursor.execute("SELECT Balance FROM Target_Accounts WHERE AccountNumber = 'ACC-T1'")
        acc = cursor.fetchone()
        self.assertIsNotNone(acc)
        self.assertEqual(acc[0], 1000.00)

        cursor.execute("SELECT Amount FROM Target_Transactions WHERE TransactionID = 'TXN-T1'")
        tx = cursor.fetchone()
        self.assertIsNotNone(tx)
        self.assertEqual(tx[0], 250.00)

        conn.close()

        # Generate Reconciliation
        summary = generate_reconciliation_report(run_id)
        self.assertEqual(summary["run_id"], run_id)
        self.assertEqual(summary["status"], "SUCCESS")

if __name__ == "__main__":
    unittest.main()
