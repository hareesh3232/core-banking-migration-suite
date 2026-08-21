import os
import csv
from datetime import datetime
from database.db_engine import get_connection
from etl.cleanser import clean_record

def load_staging_data(run_id, data_dir="./data", mask_pii=False):
    """
    Reads CSV flat files, performs record cleansing, loads into Staging tables,
    and logs preliminary validation errors to Audit_Logs.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Load Customers
    cust_path = os.path.join(data_dir, "customers.csv")
    if os.path.exists(cust_path):
        with open(cust_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            seen_cust_ids = set()
            for row in reader:
                cleansed, is_valid, reason = clean_record(row, "Customer", mask_pii=mask_pii)
                if not is_valid:
                    cursor.execute("""
                    INSERT INTO Audit_Logs (RunID, EntityName, SourceRecordID, Action, Status, Reason, Payload, CreatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (run_id, "Customer", row.get("CustomerID", "UNKNOWN"), "REJECT", "REJECTED", reason, str(row), datetime.now().isoformat()))
                    continue
                
                # Check for duplicate CustomerID within same batch
                cust_id = cleansed["CustomerID"]
                if cust_id in seen_cust_ids:
                    cursor.execute("""
                    INSERT INTO Audit_Logs (RunID, EntityName, SourceRecordID, Action, Status, Reason, Payload, CreatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (run_id, "Customer", cust_id, "REJECT", "REJECTED", "Duplicate CustomerID in source batch", str(row), datetime.now().isoformat()))
                    continue
                seen_cust_ids.add(cust_id)

                cursor.execute("""
                INSERT INTO Staging_Customers (RunID, CustomerID, SSN, FirstName, LastName, DateOfBirth, Email, Phone, Address, CreatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (run_id, cleansed["CustomerID"], cleansed["SSN"], cleansed["FirstName"], cleansed["LastName"], cleansed["DateOfBirth"], cleansed["Email"], cleansed["Phone"], cleansed["Address"], cleansed["CreatedAt"]))

    # 2. Load Accounts
    acc_path = os.path.join(data_dir, "accounts.csv")
    if os.path.exists(acc_path):
        with open(acc_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cleansed, is_valid, reason = clean_record(row, "Account", mask_pii=mask_pii)
                if not is_valid:
                    cursor.execute("""
                    INSERT INTO Audit_Logs (RunID, EntityName, SourceRecordID, Action, Status, Reason, Payload, CreatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (run_id, "Account", row.get("AccountNumber", "UNKNOWN"), "REJECT", "REJECTED", reason, str(row), datetime.now().isoformat()))
                    continue

                cursor.execute("""
                INSERT INTO Staging_Accounts (RunID, AccountNumber, CustomerID, AccountType, Currency, Balance, OpenDate, Status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (run_id, cleansed["AccountNumber"], cleansed["CustomerID"], cleansed["AccountType"], cleansed["Currency"], str(cleansed["Balance"]), cleansed["OpenDate"], cleansed["Status"]))

    # 3. Load Transactions
    tx_path = os.path.join(data_dir, "transactions.csv")
    if os.path.exists(tx_path):
        with open(tx_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cleansed, is_valid, reason = clean_record(row, "Transaction", mask_pii=mask_pii)
                if not is_valid:
                    cursor.execute("""
                    INSERT INTO Audit_Logs (RunID, EntityName, SourceRecordID, Action, Status, Reason, Payload, CreatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (run_id, "Transaction", row.get("TransactionID", "UNKNOWN"), "REJECT", "REJECTED", reason, str(row), datetime.now().isoformat()))
                    continue

                cursor.execute("""
                INSERT INTO Staging_Transactions (RunID, TransactionID, AccountNumber, Amount, Currency, TransactionType, TransactionDate, Description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (run_id, cleansed["TransactionID"], cleansed["AccountNumber"], str(cleansed["Amount"]), cleansed["Currency"], cleansed["TransactionType"], cleansed["TransactionDate"], cleansed["Description"]))

    # 4. Load Beneficiaries
    ben_path = os.path.join(data_dir, "beneficiaries.csv")
    if os.path.exists(ben_path):
        with open(ben_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cleansed, is_valid, reason = clean_record(row, "Beneficiary", mask_pii=mask_pii)
                if not is_valid:
                    cursor.execute("""
                    INSERT INTO Audit_Logs (RunID, EntityName, SourceRecordID, Action, Status, Reason, Payload, CreatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (run_id, "Beneficiary", row.get("BeneficiaryID", "UNKNOWN"), "REJECT", "REJECTED", reason, str(row), datetime.now().isoformat()))
                    continue

                cursor.execute("""
                INSERT INTO Staging_Beneficiaries (RunID, BeneficiaryID, CustomerID, BeneficiaryName, AccountNumber, BankRoutingNumber, AddedDate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (run_id, cleansed["BeneficiaryID"], cleansed["CustomerID"], cleansed["BeneficiaryName"], cleansed["AccountNumber"], cleansed["BankRoutingNumber"], cleansed["AddedDate"]))

    conn.commit()
    conn.close()
    print(f"[+] Staging load completed for Run {run_id}")

def execute_transformation_procedures(run_id):
    """
    Executes transformation and load logic from Staging to Target tables.
    Emulates T-SQL stored procedures sp_LoadCustomers, sp_LoadAccounts, etc. with transactions.
    """
    conn = get_connection()
    cursor = conn.cursor()

    now_iso = datetime.now().isoformat()

    try:
        # 1. Load Target Customers (Idempotent UPSERT)
        cursor.execute("""
        INSERT OR REPLACE INTO Target_Customers (CustomerID, SSN, FirstName, LastName, DateOfBirth, Email, Phone, Address, CreatedAt, LastMigratedRunID)
        SELECT 
            CustomerID, SSN, FirstName, LastName, DateOfBirth, Email, Phone, Address, COALESCE(CreatedAt, strftime('%Y-%m-%d', 'now')), ?
        FROM Staging_Customers
        WHERE RunID = ?
        """, (run_id, run_id))

        # Log audit for inserted customers
        cursor.execute("""
        INSERT INTO Audit_Logs (RunID, EntityName, SourceRecordID, Action, Status, Reason, CreatedAt)
        SELECT ?, 'Customer', CustomerID, 'UPSERT', 'SUCCESS', 'Loaded successfully into Target_Customers', ?
        FROM Staging_Customers WHERE RunID = ?
        """, (run_id, now_iso, run_id))

        # 2. Load Target Accounts (Reject Orphaned FKs referencing missing Customers)
        cursor.execute("""
        INSERT INTO Audit_Logs (RunID, EntityName, SourceRecordID, Action, Status, Reason, Payload, CreatedAt)
        SELECT ?, 'Account', s.AccountNumber, 'REJECT', 'REJECTED', 
               'Orphaned Foreign Key: CustomerID ' || s.CustomerID || ' does not exist in Target_Customers',
               'Balance:' || s.Balance || ' | Type:' || s.AccountType, ?
        FROM Staging_Accounts s
        LEFT JOIN Target_Customers c ON s.CustomerID = c.CustomerID
        WHERE s.RunID = ? AND c.CustomerID IS NULL
        """, (run_id, now_iso, run_id))

        cursor.execute("""
        INSERT OR REPLACE INTO Target_Accounts (AccountNumber, CustomerID, AccountType, Currency, Balance, OpenDate, Status, LastMigratedRunID)
        SELECT 
            s.AccountNumber, s.CustomerID, s.AccountType, UPPER(COALESCE(s.Currency, 'USD')), CAST(s.Balance AS REAL), s.OpenDate, s.Status, ?
        FROM Staging_Accounts s
        INNER JOIN Target_Customers c ON s.CustomerID = c.CustomerID
        WHERE s.RunID = ?
        """, (run_id, run_id))

        # 3. Load Target Transactions (Reject Orphaned FKs referencing missing Accounts)
        cursor.execute("""
        INSERT INTO Audit_Logs (RunID, EntityName, SourceRecordID, Action, Status, Reason, Payload, CreatedAt)
        SELECT ?, 'Transaction', s.TransactionID, 'REJECT', 'REJECTED',
               'Orphaned Foreign Key: AccountNumber ' || s.AccountNumber || ' does not exist in Target_Accounts',
               'Amount:' || s.Amount || ' | Date:' || s.TransactionDate, ?
        FROM Staging_Transactions s
        LEFT JOIN Target_Accounts a ON s.AccountNumber = a.AccountNumber
        WHERE s.RunID = ? AND a.AccountNumber IS NULL
        """, (run_id, now_iso, run_id))

        cursor.execute("""
        INSERT OR REPLACE INTO Target_Transactions (TransactionID, AccountNumber, Amount, Currency, TransactionType, TransactionDate, Description, LastMigratedRunID)
        SELECT 
            s.TransactionID, s.AccountNumber, CAST(s.Amount AS REAL), UPPER(COALESCE(s.Currency, 'USD')), s.TransactionType, s.TransactionDate, s.Description, ?
        FROM Staging_Transactions s
        INNER JOIN Target_Accounts a ON s.AccountNumber = a.AccountNumber
        WHERE s.RunID = ?
        """, (run_id, run_id))

        # 4. Load Target Beneficiaries (Reject Orphaned FKs referencing missing Customers)
        cursor.execute("""
        INSERT INTO Audit_Logs (RunID, EntityName, SourceRecordID, Action, Status, Reason, Payload, CreatedAt)
        SELECT ?, 'Beneficiary', s.BeneficiaryID, 'REJECT', 'REJECTED',
               'Orphaned Foreign Key: CustomerID ' || s.CustomerID || ' does not exist in Target_Customers',
               'Name:' || s.BeneficiaryName, ?
        FROM Staging_Beneficiaries s
        LEFT JOIN Target_Customers c ON s.CustomerID = c.CustomerID
        WHERE s.RunID = ? AND c.CustomerID IS NULL
        """, (run_id, now_iso, run_id))

        cursor.execute("""
        INSERT OR REPLACE INTO Target_Beneficiaries (BeneficiaryID, CustomerID, BeneficiaryName, AccountNumber, BankRoutingNumber, AddedDate, LastMigratedRunID)
        SELECT 
            s.BeneficiaryID, s.CustomerID, s.BeneficiaryName, s.AccountNumber, s.BankRoutingNumber, s.AddedDate, ?
        FROM Staging_Beneficiaries s
        INNER JOIN Target_Customers c ON s.CustomerID = c.CustomerID
        WHERE s.RunID = ?
        """, (run_id, run_id))

        conn.commit()
        print(f"[+] Transformation procedures executed successfully for Run {run_id}")
    except Exception as e:
        conn.rollback()
        print(f"[!] Error during transformation execution: {e}")
        raise e
    finally:
        conn.close()
