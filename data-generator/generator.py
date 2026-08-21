import os
import csv
import random
import argparse
from datetime import datetime, timedelta

# Constants & Synthetic Data Lists
FIRST_NAMES = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David", "Elizabeth", "José", "Renée", "Müller", "François", "Sven"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "O'Connor", "St. Cyr", "Kovács"]
CITIES = ["New York", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]
ACCOUNT_TYPES = ["CHECKING", "SAVINGS", "MONEY_MARKET", "CERTIFICATE_OF_DEPOSIT"]
TRANSACTION_TYPES = ["DEPOSIT", "WITHDRAWAL", "WIRE_TRANSFER", "ACH_DEBIT", "FEE", "INTEREST"]
CURRENCIES = ["USD", "EUR", "GBP", "CAD"]

def random_date(start_year=2020, end_year=2024):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

def format_dirty_date(dt, error_rate):
    """Applies inconsistent date formats based on error rate."""
    if random.random() < error_rate:
        fmt_choice = random.choice(["MM/DD/YYYY", "DD-MM-YYYY", "EPOCH", "INVALID"])
        if fmt_choice == "MM/DD/YYYY":
            return dt.strftime("%m/%d/%Y")
        elif fmt_choice == "DD-MM-YYYY":
            return dt.strftime("%d-%m-%Y")
        elif fmt_choice == "EPOCH":
            epoch_base = datetime(1970, 1, 1)
            return str(int((dt - epoch_base).total_seconds()))
        else:
            return "2024-13-45" # Invalid date
    return dt.strftime("%Y-%m-%d")

def format_dirty_currency(amount, error_rate):
    """Applies dirty currency formatting."""
    if random.random() < error_rate:
        style = random.choice(["SYMBOL", "TEXT", "RAW_FLOAT", "COMMAS"])
        if style == "SYMBOL":
            return f"${amount:,.2f}"
        elif style == "TEXT":
            return f"{amount:.2f} USD"
        elif style == "RAW_FLOAT":
            return f"{amount:.1f}"
        elif style == "COMMAS":
            return f"{amount:,.2f}"
    return f"{amount:.2f}"

def generate_legacy_data(num_rows, error_rate, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    print(f"[*] Generating legacy banking datasets with {num_rows} base rows and {error_rate*100}% error rate...")

    # 1. Customers
    customers = []
    customer_ids = []
    
    for i in range(1, num_rows + 1):
        cust_id = f"CUST-{10000 + i}"
        
        # Duplicate customer ID anomaly
        if random.random() < (error_rate * 0.5) and i > 5:
            cust_id = random.choice(customer_ids[:5])
        else:
            customer_ids.append(cust_id)
            
        ssn = f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"
        if random.random() < (error_rate * 0.3):
            ssn = "" # Null required field
            
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        dob = format_dirty_date(random_date(1950, 2002), error_rate)
        email = f"{first_name.lower()}.{last_name.lower()}@example.com".replace("'", "").replace(" ", "")
        phone = f"+1-{random.randint(200,999)}-555-{random.randint(1000,9999)}"
        address = f"{random.randint(100, 9999)} Main St, {random.choice(CITIES)}"
        created_at = format_dirty_date(random_date(2020, 2023), error_rate)

        customers.append({
            "CustomerID": cust_id,
            "SSN": ssn,
            "FirstName": first_name,
            "LastName": last_name,
            "DateOfBirth": dob,
            "Email": email,
            "Phone": phone,
            "Address": address,
            "CreatedAt": created_at
        })

    cust_file = os.path.join(output_dir, "customers.csv")
    with open(cust_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(customers[0].keys()))
        writer.writeheader()
        writer.writerows(customers)
    print(f"[+] Saved {len(customers)} records to {cust_file}")

    # 2. Accounts
    accounts = []
    account_numbers = []
    
    for i in range(1, num_rows + 1):
        acc_num = f"ACC-{500000 + i}"
        account_numbers.append(acc_num)
        
        # Orphaned FK anomaly
        if random.random() < (error_rate * 0.8):
            cust_id = f"CUST-999999" # Non-existent customer
        else:
            cust_id = random.choice(customer_ids)
            
        acc_type = random.choice(ACCOUNT_TYPES)
        currency = random.choice(CURRENCIES)
        balance = round(random.uniform(-500.0, 250000.0), 2)
        
        balance_str = format_dirty_currency(balance, error_rate)
        open_date = format_dirty_date(random_date(2018, 2023), error_rate)
        status = random.choice(["ACTIVE", "DORMANT", "CLOSED"])

        accounts.append({
            "AccountNumber": acc_num,
            "CustomerID": cust_id,
            "AccountType": acc_type,
            "Currency": currency,
            "Balance": balance_str,
            "OpenDate": open_date,
            "Status": status
        })

    acc_file = os.path.join(output_dir, "accounts.csv")
    with open(acc_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(accounts[0].keys()))
        writer.writeheader()
        writer.writerows(accounts)
    print(f"[+] Saved {len(accounts)} records to {acc_file}")

    # 3. Transactions
    transactions = []
    tx_count = num_rows * 2
    
    for i in range(1, tx_count + 1):
        tx_id = f"TXN-{1000000 + i}"
        
        # Orphaned Account FK
        if random.random() < (error_rate * 0.5):
            acc_num = "ACC-999999"
        else:
            acc_num = random.choice(account_numbers)
            
        amount = round(random.uniform(5.0, 15000.0), 2)
        amount_str = format_dirty_currency(amount, error_rate)
        tx_type = random.choice(TRANSACTION_TYPES)
        tx_date = format_dirty_date(random_date(2023, 2024), error_rate)
        currency = random.choice(["USD", "EUR", "USD"])
        desc = f"Legacy Txn #{i} - {tx_type} transfer via Online Portal"

        transactions.append({
            "TransactionID": tx_id,
            "AccountNumber": acc_num,
            "Amount": amount_str,
            "Currency": currency,
            "TransactionType": tx_type,
            "TransactionDate": tx_date,
            "Description": desc
        })

    tx_file = os.path.join(output_dir, "transactions.csv")
    with open(tx_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(transactions[0].keys()))
        writer.writeheader()
        writer.writerows(transactions)
    print(f"[+] Saved {len(transactions)} records to {tx_file}")

    # 4. Beneficiaries
    beneficiaries = []
    ben_count = int(num_rows * 0.6)
    
    for i in range(1, ben_count + 1):
        ben_id = f"BEN-{20000 + i}"
        cust_id = random.choice(customer_ids)
        ben_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        acc_num = f"{random.randint(10000000, 99999999)}"
        routing = f"{random.randint(100000000, 999999999)}"
        added_date = format_dirty_date(random_date(2021, 2024), error_rate)

        beneficiaries.append({
            "BeneficiaryID": ben_id,
            "CustomerID": cust_id,
            "BeneficiaryName": ben_name,
            "AccountNumber": acc_num,
            "BankRoutingNumber": routing,
            "AddedDate": added_date
        })

    ben_file = os.path.join(output_dir, "beneficiaries.csv")
    with open(ben_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(beneficiaries[0].keys()))
        writer.writeheader()
        writer.writerows(beneficiaries)
    print(f"[+] Saved {len(beneficiaries)} records to {ben_file}")

    print("[OK] Legacy data generation complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Legacy Core Banking Synthetic Data Generator")
    parser.add_argument("--rows", type=int, default=1000, help="Number of primary records to generate")
    parser.add_argument("--error-rate", type=float, default=0.05, help="Proportion of records with intentional dirty anomalies (0.0 - 1.0)")
    parser.add_argument("--output-dir", type=str, default="./data", help="Output directory for generated CSV files")
    
    args = parser.parse_args()
    generate_legacy_data(args.rows, args.error_rate, args.output_dir)
