-- ============================================================================
-- CORE BANKING DATA MIGRATION SUITE - TARGET DATABASE SCHEMA (T-SQL)
-- ============================================================================

-- Drop tables if they exist (for clean setup)
IF OBJECT_ID('dbo.Target_Transactions', 'U') IS NOT NULL DROP TABLE dbo.Target_Transactions;
IF OBJECT_ID('dbo.Target_Beneficiaries', 'U') IS NOT NULL DROP TABLE dbo.Target_Beneficiaries;
IF OBJECT_ID('dbo.Target_Accounts', 'U') IS NOT NULL DROP TABLE dbo.Target_Accounts;
IF OBJECT_ID('dbo.Target_Customers', 'U') IS NOT NULL DROP TABLE dbo.Target_Customers;

IF OBJECT_ID('dbo.Staging_Transactions', 'U') IS NOT NULL DROP TABLE dbo.Staging_Transactions;
IF OBJECT_ID('dbo.Staging_Beneficiaries', 'U') IS NOT NULL DROP TABLE dbo.Staging_Beneficiaries;
IF OBJECT_ID('dbo.Staging_Accounts', 'U') IS NOT NULL DROP TABLE dbo.Staging_Accounts;
IF OBJECT_ID('dbo.Staging_Customers', 'U') IS NOT NULL DROP TABLE dbo.Staging_Customers;

IF OBJECT_ID('dbo.Audit_Logs', 'U') IS NOT NULL DROP TABLE dbo.Audit_Logs;
IF OBJECT_ID('dbo.Reconciliation_Reports', 'U') IS NOT NULL DROP TABLE dbo.Reconciliation_Reports;
IF OBJECT_ID('dbo.Migration_Runs', 'U') IS NOT NULL DROP TABLE dbo.Migration_Runs;

-- ----------------------------------------------------------------------------
-- MIGRATION METADATA & AUDIT TABLES
-- ----------------------------------------------------------------------------

CREATE TABLE dbo.Migration_Runs (
    RunID NVARCHAR(64) NOT NULL PRIMARY KEY,
    Status NVARCHAR(32) NOT NULL DEFAULT 'PENDING', -- PENDING, RUNNING, SUCCESS, PARTIAL_SUCCESS, FAILED
    StartTime DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    EndTime DATETIME2 NULL,
    TotalSourceRecords INT NOT NULL DEFAULT 0,
    TotalMigratedRecords INT NOT NULL DEFAULT 0,
    TotalRejectedRecords INT NOT NULL DEFAULT 0,
    MaskPII BIT NOT NULL DEFAULT 0,
    TriggeredBy NVARCHAR(128) NOT NULL DEFAULT 'SYSTEM_SCHEDULER',
    ErrorMessage NVARCHAR(MAX) NULL
);

CREATE TABLE dbo.Audit_Logs (
    LogID INT IDENTITY(1,1) PRIMARY KEY,
    RunID NVARCHAR(64) NOT NULL,
    EntityName NVARCHAR(64) NOT NULL, -- Customer, Account, Transaction, Beneficiary
    SourceRecordID NVARCHAR(128) NULL,
    Action NVARCHAR(32) NOT NULL, -- INSERT, UPDATE, REJECT, VALIDATION_FAILURE
    Status NVARCHAR(32) NOT NULL, -- SUCCESS, REJECTED, WARNING
    Reason NVARCHAR(512) NULL,
    Payload NVARCHAR(MAX) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT FK_Audit_MigrationRun FOREIGN KEY (RunID) REFERENCES dbo.Migration_Runs(RunID) ON DELETE CASCADE
);

CREATE TABLE dbo.Reconciliation_Reports (
    ReportID INT IDENTITY(1,1) PRIMARY KEY,
    RunID NVARCHAR(64) NOT NULL,
    EntityName NVARCHAR(64) NOT NULL,
    SourceCount INT NOT NULL DEFAULT 0,
    TargetCount INT NOT NULL DEFAULT 0,
    RejectedCount INT NOT NULL DEFAULT 0,
    SourceChecksum DECIMAL(18,4) NULL,
    TargetChecksum DECIMAL(18,4) NULL,
    MatchStatus NVARCHAR(32) NOT NULL, -- MATCH, MISMATCH
    GeneratedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT FK_Reconcile_MigrationRun FOREIGN KEY (RunID) REFERENCES dbo.Migration_Runs(RunID) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- STAGING TABLES (Raw imported data before stored proc transformation)
-- ----------------------------------------------------------------------------

CREATE TABLE dbo.Staging_Customers (
    RawID INT IDENTITY(1,1) PRIMARY KEY,
    RunID NVARCHAR(64) NOT NULL,
    CustomerID NVARCHAR(64) NULL,
    SSN NVARCHAR(64) NULL,
    FirstName NVARCHAR(128) NULL,
    LastName NVARCHAR(128) NULL,
    DateOfBirth NVARCHAR(64) NULL,
    Email NVARCHAR(256) NULL,
    Phone NVARCHAR(64) NULL,
    Address NVARCHAR(512) NULL,
    CreatedAt NVARCHAR(64) NULL
);

CREATE TABLE dbo.Staging_Accounts (
    RawID INT IDENTITY(1,1) PRIMARY KEY,
    RunID NVARCHAR(64) NOT NULL,
    AccountNumber NVARCHAR(64) NULL,
    CustomerID NVARCHAR(64) NULL,
    AccountType NVARCHAR(64) NULL,
    Currency NVARCHAR(32) NULL,
    Balance NVARCHAR(64) NULL,
    OpenDate NVARCHAR(64) NULL,
    Status NVARCHAR(64) NULL
);

CREATE TABLE dbo.Staging_Transactions (
    RawID INT IDENTITY(1,1) PRIMARY KEY,
    RunID NVARCHAR(64) NOT NULL,
    TransactionID NVARCHAR(64) NULL,
    AccountNumber NVARCHAR(64) NULL,
    Amount NVARCHAR(64) NULL,
    Currency NVARCHAR(32) NULL,
    TransactionType NVARCHAR(64) NULL,
    TransactionDate NVARCHAR(64) NULL,
    Description NVARCHAR(512) NULL
);

CREATE TABLE dbo.Staging_Beneficiaries (
    RawID INT IDENTITY(1,1) PRIMARY KEY,
    RunID NVARCHAR(64) NOT NULL,
    BeneficiaryID NVARCHAR(64) NULL,
    CustomerID NVARCHAR(64) NULL,
    BeneficiaryName NVARCHAR(256) NULL,
    AccountNumber NVARCHAR(64) NULL,
    BankRoutingNumber NVARCHAR(64) NULL,
    AddedDate NVARCHAR(64) NULL
);

-- ----------------------------------------------------------------------------
-- TARGET NORMALIZED CORE BANKING TABLES
-- ----------------------------------------------------------------------------

CREATE TABLE dbo.Target_Customers (
    CustomerID NVARCHAR(64) NOT NULL PRIMARY KEY,
    SSN NVARCHAR(64) NULL, -- Masked if PII masking enabled
    FirstName NVARCHAR(128) NOT NULL,
    LastName NVARCHAR(128) NOT NULL,
    DateOfBirth DATE NULL,
    Email NVARCHAR(256) NULL,
    Phone NVARCHAR(64) NULL,
    Address NVARCHAR(512) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    LastMigratedRunID NVARCHAR(64) NOT NULL
);

CREATE TABLE dbo.Target_Accounts (
    AccountNumber NVARCHAR(64) NOT NULL PRIMARY KEY,
    CustomerID NVARCHAR(64) NOT NULL,
    AccountType NVARCHAR(32) NOT NULL, -- CHECKING, SAVINGS, etc.
    Currency CHAR(3) NOT NULL DEFAULT 'USD',
    Balance DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    OpenDate DATE NULL,
    Status NVARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    LastMigratedRunID NVARCHAR(64) NOT NULL,
    CONSTRAINT FK_Account_Customer FOREIGN KEY (CustomerID) REFERENCES dbo.Target_Customers(CustomerID)
);

CREATE TABLE dbo.Target_Transactions (
    TransactionID NVARCHAR(64) NOT NULL PRIMARY KEY,
    AccountNumber NVARCHAR(64) NOT NULL,
    Amount DECIMAL(18,2) NOT NULL,
    Currency CHAR(3) NOT NULL DEFAULT 'USD',
    TransactionType NVARCHAR(32) NOT NULL,
    TransactionDate DATETIME2 NOT NULL,
    Description NVARCHAR(512) NULL,
    LastMigratedRunID NVARCHAR(64) NOT NULL,
    CONSTRAINT FK_Transaction_Account FOREIGN KEY (AccountNumber) REFERENCES dbo.Target_Accounts(AccountNumber)
);

CREATE TABLE dbo.Target_Beneficiaries (
    BeneficiaryID NVARCHAR(64) NOT NULL PRIMARY KEY,
    CustomerID NVARCHAR(64) NOT NULL,
    BeneficiaryName NVARCHAR(256) NOT NULL,
    AccountNumber NVARCHAR(64) NOT NULL,
    BankRoutingNumber NVARCHAR(64) NOT NULL,
    AddedDate DATE NULL,
    LastMigratedRunID NVARCHAR(64) NOT NULL,
    CONSTRAINT FK_Beneficiary_Customer FOREIGN KEY (CustomerID) REFERENCES dbo.Target_Customers(CustomerID)
);

-- Indexes for performance
CREATE INDEX IX_TargetAccounts_CustomerID ON dbo.Target_Accounts(CustomerID);
CREATE INDEX IX_TargetTransactions_AccountNumber ON dbo.Target_Transactions(AccountNumber);
CREATE INDEX IX_AuditLogs_RunID ON dbo.Audit_Logs(RunID);
CREATE INDEX IX_AuditLogs_EntityName ON dbo.Audit_Logs(EntityName);
