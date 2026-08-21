import re
from datetime import datetime

def parse_date(date_str):
    """
    Cleanses and standardizes inconsistent legacy date inputs.
    Supported inputs: YYYY-MM-DD, MM/DD/YYYY, DD-MM-YYYY, epoch timestamps.
    Returns ISO date string YYYY-MM-DD or None if invalid.
    """
    if not date_str or not isinstance(date_str, str):
        return None
        
    date_str = date_str.strip()
    if not date_str:
        return None

    # Check numeric epoch timestamp
    if date_str.isdigit():
        try:
            ts = int(date_str)
            dt = datetime.fromtimestamp(ts)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # Try standard formats
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%b %d, %Y"
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None # Invalid date format

def parse_currency(currency_str):
    """
    Normalizes dirty currency string formats ($1,250.50, 1250.5, 1250.50 USD) to clean float.
    Returns float or None if invalid.
    """
    if currency_str is None:
        return None
        
    if isinstance(currency_str, (int, float)):
        return float(currency_str)

    s = str(currency_str).strip()
    if not s:
        return None

    # Remove currency symbols, text labels, commas
    cleaned = re.sub(r"[^\d.-]", "", s)
    try:
        val = float(cleaned)
        return round(val, 2)
    except ValueError:
        return None

def mask_ssn(ssn):
    """Masks SSN for non-prod compliance (XXX-XX-1234)."""
    if not ssn or not isinstance(ssn, str):
        return ssn
    parts = ssn.strip().split("-")
    if len(parts) == 3:
        return f"XXX-XX-{parts[2]}"
    elif len(ssn) >= 4:
        return f"XXX-XX-{ssn[-4:]}"
    return "XXX-XX-XXXX"

def mask_account_number(acc_num):
    """Masks Account Number (****5678)."""
    if not acc_num or not isinstance(acc_num, str):
        return acc_num
    acc = acc_num.strip()
    if len(acc) > 4:
        return f"****{acc[-4:]}"
    return "****"

def clean_record(record, entity_type, mask_pii=False):
    """
    Applies preliminary record-level cleansing and PII masking.
    Returns tuple: (cleansed_record_dict, is_valid, rejection_reason)
    """
    cleansed = record.copy()

    if entity_type == "Customer":
        cust_id = record.get("CustomerID", "").strip()
        ssn = record.get("SSN", "").strip()
        
        if not cust_id:
            return (None, False, "Missing CustomerID")
        if not ssn:
            return (None, False, "Missing required SSN")

        dob = parse_date(record.get("DateOfBirth", ""))
        created_at = parse_date(record.get("CreatedAt", "")) or datetime.now().strftime("%Y-%m-%d")

        cleansed["CustomerID"] = cust_id
        cleansed["SSN"] = mask_ssn(ssn) if mask_pii else ssn
        cleansed["FirstName"] = record.get("FirstName", "").strip()
        cleansed["LastName"] = record.get("LastName", "").strip()
        cleansed["DateOfBirth"] = dob
        cleansed["Email"] = record.get("Email", "").strip()
        cleansed["Phone"] = record.get("Phone", "").strip()
        cleansed["Address"] = record.get("Address", "").strip()
        cleansed["CreatedAt"] = created_at
        return (cleansed, True, None)

    elif entity_type == "Account":
        acc_num = record.get("AccountNumber", "").strip()
        cust_id = record.get("CustomerID", "").strip()
        
        if not acc_num:
            return (None, False, "Missing AccountNumber")
        if not cust_id:
            return (None, False, "Missing CustomerID")

        balance = parse_currency(record.get("Balance"))
        open_date = parse_date(record.get("OpenDate", ""))

        cleansed["AccountNumber"] = mask_account_number(acc_num) if mask_pii else acc_num
        cleansed["CustomerID"] = cust_id
        cleansed["AccountType"] = record.get("AccountType", "CHECKING").strip().upper()
        cleansed["Currency"] = record.get("Currency", "USD").strip().upper()[:3]
        cleansed["Balance"] = balance if balance is not None else 0.0
        cleansed["OpenDate"] = open_date
        cleansed["Status"] = record.get("Status", "ACTIVE").strip().upper()
        return (cleansed, True, None)

    elif entity_type == "Transaction":
        tx_id = record.get("TransactionID", "").strip()
        acc_num = record.get("AccountNumber", "").strip()
        
        if not tx_id:
            return (None, False, "Missing TransactionID")
        if not acc_num:
            return (None, False, "Missing AccountNumber")

        amount = parse_currency(record.get("Amount"))
        tx_date = parse_date(record.get("TransactionDate", "")) or datetime.now().strftime("%Y-%m-%d")

        cleansed["TransactionID"] = tx_id
        cleansed["AccountNumber"] = mask_account_number(acc_num) if mask_pii else acc_num
        cleansed["Amount"] = amount if amount is not None else 0.0
        cleansed["Currency"] = record.get("Currency", "USD").strip().upper()[:3]
        cleansed["TransactionType"] = record.get("TransactionType", "TRANSFER").strip().upper()
        cleansed["TransactionDate"] = tx_date
        cleansed["Description"] = record.get("Description", "").strip()
        return (cleansed, True, None)

    elif entity_type == "Beneficiary":
        ben_id = record.get("BeneficiaryID", "").strip()
        cust_id = record.get("CustomerID", "").strip()
        
        if not ben_id:
            return (None, False, "Missing BeneficiaryID")
        if not cust_id:
            return (None, False, "Missing CustomerID")

        added_date = parse_date(record.get("AddedDate", ""))

        cleansed["BeneficiaryID"] = ben_id
        cleansed["CustomerID"] = cust_id
        cleansed["BeneficiaryName"] = record.get("BeneficiaryName", "").strip()
        cleansed["AccountNumber"] = record.get("AccountNumber", "").strip()
        cleansed["BankRoutingNumber"] = record.get("BankRoutingNumber", "").strip()
        cleansed["AddedDate"] = added_date
        return (cleansed, True, None)

    return (record, True, None)
