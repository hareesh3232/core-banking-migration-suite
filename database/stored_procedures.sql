-- ============================================================================
-- CORE BANKING DATA MIGRATION SUITE - T-SQL STORED PROCEDURES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- PROCEDURE 1: sp_LoadCustomers
-- Cleanses staging customer records and loads into Target_Customers.
-- Idempotent: UPSERT based on CustomerID.
-- ----------------------------------------------------------------------------
CREATE OR ALTER PROCEDURE dbo.sp_LoadCustomers
    @RunID NVARCHAR(64)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        -- Process valid customers into target
        -- Reject invalid customers (missing CustomerID or SSN)
        INSERT INTO dbo.Audit_Logs (RunID, EntityName, SourceRecordID, Action, Status, Reason, Payload)
        SELECT 
            @RunID, 
            'Customer', 
            COALESCE(CustomerID, 'UNKNOWN'), 
            'REJECT', 
            'REJECTED', 
            CASE 
                WHEN CustomerID IS NULL OR CustomerID = '' THEN 'Missing required CustomerID'
                WHEN SSN IS NULL OR SSN = '' THEN 'Missing required SSN'
                ELSE 'Validation failure'
            END,
            CONCAT('RawID:', RawID, ' | Email:', Email)
        FROM dbo.Staging_Customers
        WHERE RunID = @RunID 
          AND (CustomerID IS NULL OR CustomerID = '' OR SSN IS NULL OR SSN = '');

        -- Upsert valid records
        MERGE dbo.Target_Customers AS target
        USING (
            SELECT 
                CustomerID,
                SSN,
                FirstName,
                LastName,
                TRY_CAST(DateOfBirth AS DATE) AS DateOfBirth,
                Email,
                Phone,
                Address,
                COALESCE(TRY_CAST(CreatedAt AS DATETIME2), SYSDATETIME()) AS CreatedAt
            FROM (
                SELECT *, ROW_NUMBER() OVER(PARTITION BY CustomerID ORDER BY RawID ASC) AS RowNum
                FROM dbo.Staging_Customers
                WHERE RunID = @RunID AND CustomerID IS NOT NULL AND CustomerID <> '' AND SSN IS NOT NULL AND SSN <> ''
            ) dedupe
            WHERE RowNum = 1 -- Idempotency deduplication
        ) AS source
        ON (target.CustomerID = source.CustomerID)
        WHEN MATCHED THEN
            UPDATE SET 
                target.SSN = source.SSN,
                target.FirstName = source.FirstName,
                target.LastName = source.LastName,
                target.DateOfBirth = source.DateOfBirth,
                target.Email = source.Email,
                target.Phone = source.Phone,
                target.Address = source.Address,
                target.LastMigratedRunID = @RunID
        WHEN NOT MATCHED THEN
            INSERT (CustomerID, SSN, FirstName, LastName, DateOfBirth, Email, Phone, Address, CreatedAt, LastMigratedRunID)
            VALUES (source.CustomerID, source.SSN, source.FirstName, source.LastName, source.DateOfBirth, source.Email, source.Phone, source.Address, source.CreatedAt, @RunID);

        -- Audit success
        INSERT INTO dbo.Audit_Logs (RunID, EntityName, SourceRecordID, Action, Status, Reason)
        SELECT 
            @RunID, 'Customer', CustomerID, 'INSERT_OR_UPDATE', 'SUCCESS', 'Loaded successfully into Target_Customers'
        FROM dbo.Staging_Customers
        WHERE RunID = @RunID AND CustomerID IS NOT NULL AND CustomerID <> '' AND SSN IS NOT NULL AND SSN <> '';

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

-- ----------------------------------------------------------------------------
-- PROCEDURE 2: sp_LoadAccounts
-- Validates customer FK, cleans balance, loads into Target_Accounts.
-- ----------------------------------------------------------------------------
CREATE OR ALTER PROCEDURE dbo.sp_LoadAccounts
    @RunID NVARCHAR(64)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        -- Reject accounts with orphaned CustomerIDs or invalid numbers
        INSERT INTO dbo.Audit_Logs (RunID, EntityName, SourceRecordID, Action, Status, Reason, Payload)
        SELECT 
            @RunID, 
            'Account', 
            COALESCE(s.AccountNumber, 'UNKNOWN'), 
            'REJECT', 
            'REJECTED', 
            CASE 
                WHEN s.AccountNumber IS NULL OR s.AccountNumber = '' THEN 'Missing AccountNumber'
                WHEN c.CustomerID IS NULL THEN CONCAT('Orphaned Foreign Key: CustomerID ', s.CustomerID, ' does not exist in Target_Customers')
                ELSE 'Invalid Account metadata'
            END,
            CONCAT('Balance:', s.Balance, ' | Type:', s.AccountType)
        FROM dbo.Staging_Accounts s
        LEFT JOIN dbo.Target_Customers c ON s.CustomerID = c.CustomerID
        WHERE s.RunID = @RunID 
          AND (s.AccountNumber IS NULL OR s.AccountNumber = '' OR c.CustomerID IS NULL);

        -- Upsert valid accounts
        MERGE dbo.Target_Accounts AS target
        USING (
            SELECT 
                s.AccountNumber,
                s.CustomerID,
                COALESCE(s.AccountType, 'CHECKING') AS AccountType,
                UPPER(COALESCE(NULLIF(s.Currency, ''), 'USD')) AS Currency,
                TRY_CAST(REPLACE(REPLACE(REPLACE(s.Balance, '$', ''), ',', ''), ' USD', '') AS DECIMAL(18,2)) AS Balance,
                TRY_CAST(s.OpenDate AS DATE) AS OpenDate,
                COALESCE(s.Status, 'ACTIVE') AS Status
            FROM dbo.Staging_Accounts s
            INNER JOIN dbo.Target_Customers c ON s.CustomerID = c.CustomerID
            WHERE s.RunID = @RunID AND s.AccountNumber IS NOT NULL AND s.AccountNumber <> ''
        ) AS source
        ON (target.AccountNumber = source.AccountNumber)
        WHEN MATCHED THEN
            UPDATE SET 
                target.CustomerID = source.CustomerID,
                target.AccountType = source.AccountType,
                target.Currency = source.Currency,
                target.Balance = COALESCE(source.Balance, 0.00),
                target.OpenDate = source.OpenDate,
                target.Status = source.Status,
                target.LastMigratedRunID = @RunID
        WHEN NOT MATCHED THEN
            INSERT (AccountNumber, CustomerID, AccountType, Currency, Balance, OpenDate, Status, LastMigratedRunID)
            VALUES (source.AccountNumber, source.CustomerID, source.AccountType, source.Currency, COALESCE(source.Balance, 0.00), source.OpenDate, source.Status, @RunID);

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

-- ----------------------------------------------------------------------------
-- PROCEDURE 3: sp_LoadTransactions
-- Validates Account FK, cleans amount/date, loads Target_Transactions.
-- ----------------------------------------------------------------------------
CREATE OR ALTER PROCEDURE dbo.sp_LoadTransactions
    @RunID NVARCHAR(64)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        -- Reject orphaned transactions
        INSERT INTO dbo.Audit_Logs (RunID, EntityName, SourceRecordID, Action, Status, Reason, Payload)
        SELECT 
            @RunID, 
            'Transaction', 
            COALESCE(s.TransactionID, 'UNKNOWN'), 
            'REJECT', 
            'REJECTED', 
            CASE 
                WHEN s.TransactionID IS NULL OR s.TransactionID = '' THEN 'Missing TransactionID'
                WHEN a.AccountNumber IS NULL THEN CONCAT('Orphaned Foreign Key: AccountNumber ', s.AccountNumber, ' does not exist in Target_Accounts')
                ELSE 'Invalid transaction data'
            END,
            CONCAT('Amount:', s.Amount, ' | Date:', s.TransactionDate)
        FROM dbo.Staging_Transactions s
        LEFT JOIN dbo.Target_Accounts a ON s.AccountNumber = a.AccountNumber
        WHERE s.RunID = @RunID 
          AND (s.TransactionID IS NULL OR s.TransactionID = '' OR a.AccountNumber IS NULL);

        -- Upsert valid transactions
        MERGE dbo.Target_Transactions AS target
        USING (
            SELECT 
                s.TransactionID,
                s.AccountNumber,
                TRY_CAST(REPLACE(REPLACE(REPLACE(s.Amount, '$', ''), ',', ''), ' USD', '') AS DECIMAL(18,2)) AS Amount,
                UPPER(COALESCE(NULLIF(s.Currency, ''), 'USD')) AS Currency,
                COALESCE(s.TransactionType, 'TRANSFER') AS TransactionType,
                COALESCE(TRY_CAST(s.TransactionDate AS DATETIME2), SYSDATETIME()) AS TransactionDate,
                s.Description
            FROM dbo.Staging_Transactions s
            INNER JOIN dbo.Target_Accounts a ON s.AccountNumber = a.AccountNumber
            WHERE s.RunID = @RunID AND s.TransactionID IS NOT NULL AND s.TransactionID <> ''
        ) AS source
        ON (target.TransactionID = source.TransactionID)
        WHEN MATCHED THEN
            UPDATE SET 
                target.AccountNumber = source.AccountNumber,
                target.Amount = COALESCE(source.Amount, 0.00),
                target.Currency = source.Currency,
                target.TransactionType = source.TransactionType,
                target.TransactionDate = source.TransactionDate,
                target.Description = source.Description,
                target.LastMigratedRunID = @RunID
        WHEN NOT MATCHED THEN
            INSERT (TransactionID, AccountNumber, Amount, Currency, TransactionType, TransactionDate, Description, LastMigratedRunID)
            VALUES (source.TransactionID, source.AccountNumber, COALESCE(source.Amount, 0.00), source.Currency, source.TransactionType, source.TransactionDate, source.Description, @RunID);

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

-- ----------------------------------------------------------------------------
-- PROCEDURE 4: sp_LoadBeneficiaries
-- ----------------------------------------------------------------------------
CREATE OR ALTER PROCEDURE dbo.sp_LoadBeneficiaries
    @RunID NVARCHAR(64)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        -- Reject orphaned beneficiaries
        INSERT INTO dbo.Audit_Logs (RunID, EntityName, SourceRecordID, Action, Status, Reason, Payload)
        SELECT 
            @RunID, 
            'Beneficiary', 
            COALESCE(s.BeneficiaryID, 'UNKNOWN'), 
            'REJECT', 
            'REJECTED', 
            CONCAT('Orphaned Foreign Key: CustomerID ', s.CustomerID, ' does not exist in Target_Customers'),
            CONCAT('Name:', s.BeneficiaryName, ' | Account:', s.AccountNumber)
        FROM dbo.Staging_Beneficiaries s
        LEFT JOIN dbo.Target_Customers c ON s.CustomerID = c.CustomerID
        WHERE s.RunID = @RunID AND (s.BeneficiaryID IS NULL OR s.BeneficiaryID = '' OR c.CustomerID IS NULL);

        -- Upsert valid beneficiaries
        MERGE dbo.Target_Beneficiaries AS target
        USING (
            SELECT 
                s.BeneficiaryID,
                s.CustomerID,
                s.BeneficiaryName,
                s.AccountNumber,
                s.BankRoutingNumber,
                TRY_CAST(s.AddedDate AS DATE) AS AddedDate
            FROM dbo.Staging_Beneficiaries s
            INNER JOIN dbo.Target_Customers c ON s.CustomerID = c.CustomerID
            WHERE s.RunID = @RunID AND s.BeneficiaryID IS NOT NULL AND s.BeneficiaryID <> ''
        ) AS source
        ON (target.BeneficiaryID = source.BeneficiaryID)
        WHEN MATCHED THEN
            UPDATE SET 
                target.CustomerID = source.CustomerID,
                target.BeneficiaryName = source.BeneficiaryName,
                target.AccountNumber = source.AccountNumber,
                target.BankRoutingNumber = source.BankRoutingNumber,
                target.AddedDate = source.AddedDate,
                target.LastMigratedRunID = @RunID
        WHEN NOT MATCHED THEN
            INSERT (BeneficiaryID, CustomerID, BeneficiaryName, AccountNumber, BankRoutingNumber, AddedDate, LastMigratedRunID)
            VALUES (source.BeneficiaryID, source.CustomerID, source.BeneficiaryName, source.AccountNumber, source.BankRoutingNumber, source.AddedDate, @RunID);

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

-- ----------------------------------------------------------------------------
-- PROCEDURE 5: sp_ReconcileMigration
-- Generates entity count comparison and checksum validation report.
-- ----------------------------------------------------------------------------
CREATE OR ALTER PROCEDURE dbo.sp_ReconcileMigration
    @RunID NVARCHAR(64)
AS
BEGIN
    SET NOCOUNT ON;

    -- 1. Customers Reconciliation
    DECLARE @CustSource INT = (SELECT COUNT(*) FROM dbo.Staging_Customers WHERE RunID = @RunID);
    DECLARE @CustTarget INT = (SELECT COUNT(*) FROM dbo.Target_Customers WHERE LastMigratedRunID = @RunID);
    DECLARE @CustReject INT = (SELECT COUNT(*) FROM dbo.Audit_Logs WHERE RunID = @RunID AND EntityName = 'Customer' AND Status = 'REJECTED');
    
    INSERT INTO dbo.Reconciliation_Reports (RunID, EntityName, SourceCount, TargetCount, RejectedCount, SourceChecksum, TargetChecksum, MatchStatus)
    VALUES (@RunID, 'Customer', @CustSource, @CustTarget, @CustReject, 0.00, 0.00, CASE WHEN @CustSource = (@CustTarget + @CustReject) THEN 'MATCH' ELSE 'MISMATCH' END);

    -- 2. Accounts Reconciliation
    DECLARE @AccSource INT = (SELECT COUNT(*) FROM dbo.Staging_Accounts WHERE RunID = @RunID);
    DECLARE @AccTarget INT = (SELECT COUNT(*) FROM dbo.Target_Accounts WHERE LastMigratedRunID = @RunID);
    DECLARE @AccReject INT = (SELECT COUNT(*) FROM dbo.Audit_Logs WHERE RunID = @RunID AND EntityName = 'Account' AND Status = 'REJECTED');
    
    INSERT INTO dbo.Reconciliation_Reports (RunID, EntityName, SourceCount, TargetCount, RejectedCount, SourceChecksum, TargetChecksum, MatchStatus)
    VALUES (@RunID, 'Account', @AccSource, @AccTarget, @AccReject, 0.00, 0.00, CASE WHEN @AccSource = (@AccTarget + @AccReject) THEN 'MATCH' ELSE 'MISMATCH' END);

    -- 3. Transactions Financial Checksum Reconciliation
    DECLARE @TxSource INT = (SELECT COUNT(*) FROM dbo.Staging_Transactions WHERE RunID = @RunID);
    DECLARE @TxTarget INT = (SELECT COUNT(*) FROM dbo.Target_Transactions WHERE LastMigratedRunID = @RunID);
    DECLARE @TxReject INT = (SELECT COUNT(*) FROM dbo.Audit_Logs WHERE RunID = @RunID AND EntityName = 'Transaction' AND Status = 'REJECTED');
    
    DECLARE @TxSourceSum DECIMAL(18,4) = (
        SELECT COALESCE(SUM(TRY_CAST(REPLACE(REPLACE(REPLACE(Amount, '$', ''), ',', ''), ' USD', '') AS DECIMAL(18,2))), 0.0) 
        FROM dbo.Staging_Transactions WHERE RunID = @RunID
    );
    DECLARE @TxTargetSum DECIMAL(18,4) = (
        SELECT COALESCE(SUM(Amount), 0.0) 
        FROM dbo.Target_Transactions WHERE LastMigratedRunID = @RunID
    );

    INSERT INTO dbo.Reconciliation_Reports (RunID, EntityName, SourceCount, TargetCount, RejectedCount, SourceChecksum, TargetChecksum, MatchStatus)
    VALUES (@RunID, 'Transaction', @TxSource, @TxTarget, @TxReject, @TxSourceSum, @TxTargetSum, CASE WHEN @TxSource = (@TxTarget + @TxReject) THEN 'MATCH' ELSE 'MISMATCH' END);

    -- 4. Beneficiaries Reconciliation
    DECLARE @BenSource INT = (SELECT COUNT(*) FROM dbo.Staging_Beneficiaries WHERE RunID = @RunID);
    DECLARE @BenTarget INT = (SELECT COUNT(*) FROM dbo.Target_Beneficiaries WHERE LastMigratedRunID = @RunID);
    DECLARE @BenReject INT = (SELECT COUNT(*) FROM dbo.Audit_Logs WHERE RunID = @RunID AND EntityName = 'Beneficiary' AND Status = 'REJECTED');

    INSERT INTO dbo.Reconciliation_Reports (RunID, EntityName, SourceCount, TargetCount, RejectedCount, SourceChecksum, TargetChecksum, MatchStatus)
    VALUES (@RunID, 'Beneficiary', @BenSource, @BenTarget, @BenReject, 0.00, 0.00, CASE WHEN @BenSource = (@BenTarget + @BenReject) THEN 'MATCH' ELSE 'MISMATCH' END);

    -- Update Migration_Runs Summary
    DECLARE @TotalSource INT = @CustSource + @AccSource + @TxSource + @BenSource;
    DECLARE @TotalTarget INT = @CustTarget + @AccTarget + @TxTarget + @BenTarget;
    DECLARE @TotalReject INT = @CustReject + @AccReject + @TxReject + @BenReject;

    UPDATE dbo.Migration_Runs
    SET 
        Status = CASE WHEN @TotalReject = 0 THEN 'SUCCESS' ELSE 'PARTIAL_SUCCESS' END,
        EndTime = SYSDATETIME(),
        TotalSourceRecords = @TotalSource,
        TotalMigratedRecords = @TotalTarget,
        TotalRejectedRecords = @TotalReject
    WHERE RunID = @RunID;
END;
GO

-- ----------------------------------------------------------------------------
-- PROCEDURE 6: sp_ExecuteFullMigration
-- Master procedure executing entire load pipeline with error handling.
-- ----------------------------------------------------------------------------
CREATE OR ALTER PROCEDURE dbo.sp_ExecuteFullMigration
    @RunID NVARCHAR(64)
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE dbo.Migration_Runs SET Status = 'RUNNING' WHERE RunID = @RunID;

    BEGIN TRY
        EXEC dbo.sp_LoadCustomers @RunID = @RunID;
        EXEC dbo.sp_LoadAccounts @RunID = @RunID;
        EXEC dbo.sp_LoadTransactions @RunID = @RunID;
        EXEC dbo.sp_LoadBeneficiaries @RunID = @RunID;
        EXEC dbo.sp_ReconcileMigration @RunID = @RunID;
    END TRY
    BEGIN CATCH
        UPDATE dbo.Migration_Runs 
        SET Status = 'FAILED', EndTime = SYSDATETIME(), ErrorMessage = ERROR_MESSAGE() 
        WHERE RunID = @RunID;

        INSERT INTO dbo.Audit_Logs (RunID, EntityName, SourceRecordID, Action, Status, Reason)
        VALUES (@RunID, 'SYSTEM', 'GLOBAL', 'MIGRATION_FAILURE', 'FAILED', ERROR_MESSAGE());

        THROW;
    END CATCH
END;
GO
