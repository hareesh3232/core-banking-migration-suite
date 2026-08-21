import os
import sqlite3
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "migration_suite.db")

def get_connection():
    """Returns a SQLite database connection with row factory enabled."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite database schema mirroring T-SQL specifications."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create Migration Metadata Tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Migration_Runs (
        RunID TEXT PRIMARY KEY,
        Status TEXT NOT NULL DEFAULT 'PENDING',
        StartTime TEXT NOT NULL,
        EndTime TEXT,
        TotalSourceRecords INTEGER NOT NULL DEFAULT 0,
        TotalMigratedRecords INTEGER NOT NULL DEFAULT 0,
        TotalRejectedRecords INTEGER NOT NULL DEFAULT 0,
        MaskPII INTEGER NOT NULL DEFAULT 0,
        TriggeredBy TEXT NOT NULL DEFAULT 'SYSTEM_SCHEDULER',
        ErrorMessage TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Audit_Logs (
        LogID INTEGER PRIMARY KEY AUTOINCREMENT,
        RunID TEXT NOT NULL,
        EntityName TEXT NOT NULL,
        SourceRecordID TEXT,
        Action TEXT NOT NULL,
        Status TEXT NOT NULL,
        Reason TEXT,
        Payload TEXT,
        CreatedAt TEXT NOT NULL,
        FOREIGN KEY(RunID) REFERENCES Migration_Runs(RunID)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Reconciliation_Reports (
        ReportID INTEGER PRIMARY KEY AUTOINCREMENT,
        RunID TEXT NOT NULL,
        EntityName TEXT NOT NULL,
        SourceCount INTEGER NOT NULL DEFAULT 0,
        TargetCount INTEGER NOT NULL DEFAULT 0,
        RejectedCount INTEGER NOT NULL DEFAULT 0,
        SourceChecksum REAL DEFAULT 0.0,
        TargetChecksum REAL DEFAULT 0.0,
        MatchStatus TEXT NOT NULL,
        GeneratedAt TEXT NOT NULL,
        FOREIGN KEY(RunID) REFERENCES Migration_Runs(RunID)
    );
    """)

    # Create Staging Tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Staging_Customers (
        RawID INTEGER PRIMARY KEY AUTOINCREMENT,
        RunID TEXT NOT NULL,
        CustomerID TEXT,
        SSN TEXT,
        FirstName TEXT,
        LastName TEXT,
        DateOfBirth TEXT,
        Email TEXT,
        Phone TEXT,
        Address TEXT,
        CreatedAt TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Staging_Accounts (
        RawID INTEGER PRIMARY KEY AUTOINCREMENT,
        RunID TEXT NOT NULL,
        AccountNumber TEXT,
        CustomerID TEXT,
        AccountType TEXT,
        Currency TEXT,
        Balance TEXT,
        OpenDate TEXT,
        Status TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Staging_Transactions (
        RawID INTEGER PRIMARY KEY AUTOINCREMENT,
        RunID TEXT NOT NULL,
        TransactionID TEXT,
        AccountNumber TEXT,
        Amount TEXT,
        Currency TEXT,
        TransactionType TEXT,
        TransactionDate TEXT,
        Description TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Staging_Beneficiaries (
        RawID INTEGER PRIMARY KEY AUTOINCREMENT,
        RunID TEXT NOT NULL,
        BeneficiaryID TEXT,
        CustomerID TEXT,
        BeneficiaryName TEXT,
        AccountNumber TEXT,
        BankRoutingNumber TEXT,
        AddedDate TEXT
    );
    """)

    # Create Target Tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Target_Customers (
        CustomerID TEXT PRIMARY KEY,
        SSN TEXT,
        FirstName TEXT NOT NULL,
        LastName TEXT NOT NULL,
        DateOfBirth TEXT,
        Email TEXT,
        Phone TEXT,
        Address TEXT,
        CreatedAt TEXT NOT NULL,
        LastMigratedRunID TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Target_Accounts (
        AccountNumber TEXT PRIMARY KEY,
        CustomerID TEXT NOT NULL,
        AccountType TEXT NOT NULL,
        Currency TEXT NOT NULL DEFAULT 'USD',
        Balance REAL NOT NULL DEFAULT 0.0,
        OpenDate TEXT,
        Status TEXT NOT NULL DEFAULT 'ACTIVE',
        LastMigratedRunID TEXT NOT NULL,
        FOREIGN KEY(CustomerID) REFERENCES Target_Customers(CustomerID)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Target_Transactions (
        TransactionID TEXT PRIMARY KEY,
        AccountNumber TEXT NOT NULL,
        Amount REAL NOT NULL,
        Currency TEXT NOT NULL DEFAULT 'USD',
        TransactionType TEXT NOT NULL,
        TransactionDate TEXT NOT NULL,
        Description TEXT,
        LastMigratedRunID TEXT NOT NULL,
        FOREIGN KEY(AccountNumber) REFERENCES Target_Accounts(AccountNumber)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Target_Beneficiaries (
        BeneficiaryID TEXT PRIMARY KEY,
        CustomerID TEXT NOT NULL,
        BeneficiaryName TEXT NOT NULL,
        AccountNumber TEXT NOT NULL,
        BankRoutingNumber TEXT NOT NULL,
        AddedDate TEXT,
        LastMigratedRunID TEXT NOT NULL,
        FOREIGN KEY(CustomerID) REFERENCES Target_Customers(CustomerID)
    );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("[+] Database initialized successfully!")
