
import sys
import os
import pandas as pd
from utils import extract_from_pdf

def test_bob2_extraction():
    filepath = 'BOB-2.pdf'
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    print(f"Testing extraction for {filepath}...")
    df, bank_name = extract_from_pdf(filepath)
    
    print(f"Detected Bank: {bank_name}")
    print(f"Extracted Rows: {len(df)}")
    
    if df.empty:
        print("FAIL: No rows extracted.")
        return

    print("\n--- Extracted Data (First 5 rows) ---")
    print(df.head())
    
    print("\n--- Extracted Data (Last 5 rows) ---")
    print(df.tail())
    
    # Validation
    # Check for expected columns
    expected_cols = ['Date', 'Description', 'Debit', 'Credit', 'Balance']
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        print(f"FAIL: Missing columns: {missing_cols}")
    else:
        print("PASS: valid columns validation.")

    # Check for specific known transaction
    # 14-12-2024 ... 112.00 ... 4,068.37Cr
    # We determined 112.00 is a Credit (based on logic).
    mask = df['Amount'].astype(str).str.contains('112.00') if 'Amount' in df.columns else (df['Credit'].astype(str).str.contains('112.00') | df['Debit'].astype(str).str.contains('112.00'))
    
    if mask.any():
        print("PASS: Found transaction with amount 112.00")
        row = df[mask].iloc[0]
        print("Sample Row:")
        print(row)
    else:
        print("FAIL: Could not find transaction with amount 112.00")

if __name__ == "__main__":
    test_bob2_extraction()
