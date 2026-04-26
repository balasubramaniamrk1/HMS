import pandas as pd
import pdfplumber
import re

def detect_bank(text):
    """
    Detects the bank name from the text content of the PDF.
    """
    # Only check the first 1000 characters (header area) to avoid false positives 
    # from transaction descriptions (e.g. "Transfer to IOB")
    text = text[:1000].lower().replace('\n', ' ').replace('  ', ' ')
    
    # Helper for strict word match
    def has_word(word, text):
        return re.search(r'\b' + re.escape(word) + r'\b', text) is not None

    # 1. Check for Specific Unique Markers (High confidence - Issuer details)
    # These are usually in the header (IFSC, CRN, etc.) and are less likely to be in transaction descriptions
    
    # Priority Check: City Union Bank (CUB) - Check first to avoid IOB false positives from 'IOBA' in descriptions
    if 'ciub' in text or 'city union bank' in text:
        return 'City Union Bank'

    # Priority Check: Indian Bank name (to avoid IOBA false positive match for IOB)
    if 'indian bank' in text:
        return 'Indian Bank'
    
    # ICICI (Generic Statement Format) - Check this first as it's a strong signature
    if 'detailed statement' in text and 'transaction type all transactions list' in text:
        return 'ICICI Bank'
    
    # HDFC: "hdfcbank" (no space) or "hdfc" substring
    if 'hdfcbank' in text or 'hdfc' in text:
        return 'HDFC Bank'
    
    # Kotak: CRN (Customer Relationship Number) or KKBK (IFSC)
    if 'crn' in text or 'kkbk' in text:
        return 'Kotak Mahindra Bank'
    # YES Bank: IFSC starts with YESB
    if 'yesb' in text:
        return 'YES Bank'
    # BOB: IFSC starts with BARB
    if 'barb' in text: 
        return 'Bank of Baroda'
    # TMB: IFSC starts with TMBL
    if 'tmbl' in text:
        return 'Tamilnad Mercantile Bank'
    # Union Bank: IFSC starts with UBIN
    if 'ubin' in text:
        return 'Union Bank of India'
    # IOB: IFSC starts with IOBA
    if 'ioba' in text:
        return 'Indian Overseas Bank'
    # Indian Bank: IFSC starts with IDIB
    if 'idib' in text:
        return 'Indian Bank'
    # Canara: IFSC starts with CNRB
    if 'cnrb' in text:
        return 'Canara Bank'
    # SBI: IFSC starts with SBIN
    if 'sbin' in text:
        return 'State Bank of India'
    # ICICI: IFSC starts with ICIC
    if 'icic' in text:
        return 'ICICI Bank'

    # City Union Bank: IFSC starts with CIUB or Name match
    if 'ciub' in text or 'city union bank' in text:
        return 'City Union Bank'

    # 2. Check for Full Bank Names (Reliable but can be in transaction descriptions)
    if 'tamilnad mercantile bank' in text:
        return 'Tamilnad Mercantile Bank'
    elif 'state bank of india' in text:
        return 'State Bank of India'
    elif 'union bank of india' in text:
        return 'Union Bank of India'
    elif 'kotak mahindra bank' in text:
        return 'Kotak Mahindra Bank'
    elif 'indian overseas bank' in text:
        return 'Indian Overseas Bank'
    elif 'bank of baroda' in text:
        return 'Bank of Baroda'
    elif 'canara bank' in text:
        return 'Canara Bank'
    elif 'indian bank' in text:
        return 'Indian Bank'
    elif 'idbi bank' in text:
        return 'IDBI Bank'
    elif 'axis bank' in text:
        return 'Axis Bank'
    elif 'hdfc bank' in text:
        return 'HDFC Bank'
    elif 'icici bank' in text:
        return 'ICICI Bank'
    elif 'yes bank' in text:
        return 'YES Bank'
    elif 'dbs bank' in text:
        return 'DBS Bank'
    elif 'city union bank' in text:
        return 'City Union Bank'

    # 3. Check for Abbreviations (Strict word boundary check)
    if has_word('sbi', text):
        return 'State Bank of India'
    elif has_word('kotak', text):
        return 'Kotak Mahindra Bank'
    elif has_word('iob', text):
        return 'Indian Overseas Bank'
    elif has_word('bob', text):
        return 'Bank of Baroda'
    elif has_word('tmb', text):
        return 'Tamilnad Mercantile Bank'
    elif has_word('canara', text):
        return 'Canara Bank'
    elif has_word('axis', text):
        return 'Axis Bank'
    elif has_word('idbi', text):
        return 'IDBI Bank'
    elif has_word('hdfc', text):
        return 'HDFC Bank'
    elif has_word('icici', text):
        return 'ICICI Bank'
    elif has_word('yes', text) and 'bank' in text: # "YES" is common, check context
        return 'YES Bank'
    elif has_word('dbs', text):
        return 'DBS Bank'
        
    return 'Unknown Bank'

def extract_from_pdf(filepath):
    """
    Extracts tables from a PDF bank statement.
    Returns: (DataFrame, bank_name)
    """
    all_rows = []
    bank_name = "Unknown Bank"
    
    with pdfplumber.open(filepath) as pdf:
        # Detect bank from first page text
        if len(pdf.pages) > 0:
            first_page_text = pdf.pages[0].extract_text() or ""
            bank_name = detect_bank(first_page_text)
    
        running_balance = None
            
        for page in pdf.pages:
            tables = page.extract_tables()
            
            # For City Union Bank, force text parsing as table extraction is unreliable (merges columns)
            if bank_name == 'City Union Bank':
                tables = []
            
            page_has_messy_tables = False
            extracted_rows_from_tables_on_this_page = [] # Collect rows from tables for this page

            # Strategy 1: Standard Table Extraction
            if tables:
                for table in tables:
                    # Check if it's a valid transaction table
                    # Heuristic: Skip tables that look like Account Summary or Legends
                    if not table or not table[0]:
                        continue
                        
                    headers = [str(cell).lower() for cell in table[0] if cell]
                    header_str = " ".join(headers)
                    
                    # Skip Account Summary tables
                    if 'account no' in header_str and 'currency' in header_str:
                        continue
                    # Skip Legend tables (check headers and first data row)
                    if 'ib trf' in header_str or 'term deposit' in header_str:
                        continue
                    # Also check first data row for legend content
                    if len(table) > 1 and table[1]:
                        first_row_str = " ".join([str(cell).lower() for cell in table[1] if cell])
                        if ('point of sales' in first_row_str or 'term deposit' in first_row_str or 
                            'immediate payment' in first_row_str):
                            continue
                    
                    # Check for "messy" tables (merged rows)
                    # Only check for messiness if this looks like a TRANSACTION table
                    # (has headers like date, amount, balance, withdrawal, deposit, etc.)
                    # This avoids flagging non-transaction tables (like customer details) as messy
                    looks_like_transaction_table = any(keyword in header_str for keyword in 
                        ['date', 'amount', 'balance', 'withdrawal', 'deposit', 'debit', 'credit', 
                         'particulars', 'narration', 'description', 'transaction'])
                    
                    is_messy_table = False
                    if looks_like_transaction_table:
                        # Heuristic: If the FIRST column has multiple newlines (>5), it's likely a merged row table (like HDFC)
                        # If only a few newlines (1-3), it's just wrapped text and is fine.
                        for row in table:
                            # Check first cell (Date) for many newlines
                            if row and row[0] and str(row[0]).count('\n') > 5:
                                is_messy_table = True
                                page_has_messy_tables = True
                                break
                            # Also check if *many* cells have newlines (e.g. > 50% of cells in a row)
                            # This handles cases where Date might be clean but everything else is merged
                            newline_cells = sum(1 for cell in row if cell and str(cell).count('\n') > 5)
                            if len(row) > 0 and newline_cells / len(row) > 0.5:
                                 is_messy_table = True
                                 page_has_messy_tables = True
                                 break
                            if is_messy_table:
                                break
                    
                    if is_messy_table:
                        # If a table is messy, we skip it and rely on text parsing for the whole page.
                        # We don't want to mix potentially bad table data with good text data.
                        continue 
                    else:
                        for row in table:
                            # Clean row
                            cleaned_row = [cell.strip() if cell else '' for cell in row]
                            # Check if it's a "merged" row (1 column containing everything)
                            if len(cleaned_row) == 1 and cleaned_row[0]:
                                # Strategy 2: Regex Parsing for Merged Rows
                                # Pattern: Date ... Amount ... Balance (or Balance ... Amount due to wrapping)
                                text = cleaned_row[0].replace('\n', ' ')
                                
                                # 1. Extract Date
                                date_match = re.search(r'^(\d{2}[/-]\d{2}[/-]\d{2,4})', text)
                                if date_match:
                                    date = date_match.group(1)
                                    
                                    # 2. Extract all potential money values (e.g. 10,000.00 or 10,000.00Cr)
                                    # Regex: digits, commas, dot, 2 digits, optional Cr/Dr/suffix
                                    money_matches = list(re.finditer(r'([\d,]+\.\d{2})([A-Za-z]*)', text))
                                    
                                    if len(money_matches) >= 2:
                                        # We take the last two matches as Amount and Balance
                                        # But we need to decide which is which.
                                        val1_full = money_matches[-2].group(0)
                                        val1_num = money_matches[-2].group(1)
                                        val1_suffix = money_matches[-2].group(2).lower()
                                        
                                        val2_full = money_matches[-1].group(0)
                                        val2_num = money_matches[-1].group(1)
                                        val2_suffix = money_matches[-1].group(2).lower()
                                        
                                        # Assume last is Balance, second to last is Amount
                                        balance = val2_full
                                        amount = val1_full
                                        
                                        # Description is everything between Date and Amount
                                        # Find end of date
                                        date_end = date_match.end()
                                        # Find start of amount
                                        amount_start = money_matches[-2].start()
                                        
                                        description = text[date_end:amount_start].strip()
                                        
                                        extracted_rows_from_tables_on_this_page.append([date, description, amount, balance])
                            else:
                                extracted_rows_from_tables_on_this_page.append(cleaned_row)
            
            # Strategy 3: Text-based Parsing (Fallback/Supplement)
            # If we found messy tables, OR if no tables were found at all, try text parsing
            if page_has_messy_tables or not tables:
                text = page.extract_text()
                if text:
                    lines = text.split('\n')
                    current_row = []
                    
                    for line in lines:
                        # Regex for Date (DD/MM/YY or DD-MM-YYYY or DD-MMM-YYYY)
                        # Also handle newlines in date if possible (though text extraction usually puts them on one line)
                        date_match = re.match(r'^(\d{2}[/-]\w{3}[/-]\d{2,4}|\d{2}[/-]\d{2}[/-]\d{2,4})', line)
                        
                        # IOB-2 Specific Format: DD-MM-YYYY TranID/RefNum Particulars Debit Credit Balance
                        # e.g. 02-04-2024 2024040286828851 BY TRANSFER-UPI/409346654766/Mr. 10.00 12,028.00Cr
                        iob2_match = re.match(r'^(\d{2}-\d{2}-\d{4})\s+(\S+)\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})([A-Za-z]*)', line)
                        

                        if iob2_match:
                             # IOB-2 match found!
                             date = iob2_match.group(1)
                             ref = iob2_match.group(2)
                             desc = iob2_match.group(3) + " " + ref
                             # Amount logic: determine debit/credit from position or context?
                             # In IOB-2, it seems to be Debit Credit Balance.
                             # But wait, the regex above captures 2 amounts.
                             # Let's assume the last amount is Balance if it has Cr/Dr.
                             # Actually, let's look at the line structure again.
                             # The regex captures: Date, Ref, Desc, Amt1, Amt2+Suffix.
                             # This assumes 2 amounts on the line.
                             # If there are 3 amounts (Debit, Credit, Balance), we need a better regex.
                             
                             # Let's stick to the generic date match for now, but refine it.
                             pass
                        
                        # City Union Bank (CUB) Specific Format
                        # Format: DATE DESCRIPTION CHEQUE NO DEBIT CREDIT BALANCE
                        # Example: 30/09/2023 TO PROCESSING CHAGRE:00032 30,000.00 -30,000.00
                        # Example: 01/04/2024 BY ONL UPI/CR/... 3,000.00 3,378.48
                        # Regex to capture: Date, Description, Amount, Balance
                        # Note: Amount column is tricky because it could be Debit or Credit.
                        # We capture the last two numbers.
                        cub_match = re.search(r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2}|-[\d,]+\.\d{2})\s*$', line)
                        
                        if cub_match:
                            date = cub_match.group(1)
                            description = cub_match.group(2).strip()
                            amount_val = cub_match.group(3)
                            balance_val = cub_match.group(4)
                            
                            # Determine Debit/Credit based on description or context
                            # Heuristic: "TO " usually implies Debit, "BY " usually implies Credit
                            # Also, usually Debit is before Credit in columns. But we only have one amount here between Desc and Balance?
                            # Wait, the example: "30,000.00 -30,000.00". That is Amount, Balance.
                            # Is the Amount Debit or Credit?
                            # CUB Table Headers: DATE, DESCRIPTION, CHEQUE NO, DEBIT, CREDIT, BALANCE
                            # So if there is only one amount, it's either in Debit or Credit column.
                            # The regex captures 2 numbers at the end.
                            # If the description starts with "TO", treat as Debit.
                            # If the description starts with "BY", treat as Credit.
                            
                            debit = ''
                            credit = ''
                            
                            if description.startswith('TO '):
                                debit = amount_val
                            elif description.startswith('BY '):
                                credit = amount_val
                            else:
                                # Fallback: assume Debit if no "BY" (safest?) or put in Amount and let cleaner handle?
                                # Let's assume Debit for now if unsure, or maybe search specifically.
                                # Actually, CUB seems to consistently use TO/BY.
                                debit = amount_val # Default to Debit
                                
                            current_row = [date, description, debit, credit, balance_val]
                            all_rows.append(current_row)
                            continue


                        if date_match:
                            # Start of a new transaction row
                            if current_row:
                                all_rows.append(current_row)
                            
                            # Split line into parts
                            parts = line.split()
                            # Basic heuristic: Date is first, amounts are at the end
                            date = parts[0]
                            
                            # Find amounts at the end
                            # Look for numbers with decimals
                            amounts = []
                            desc_parts = []
                            for part in reversed(parts[1:]):
                                if re.match(r'[\d,]+\.\d{2}', part):
                                    amounts.insert(0, part)
                                else:
                                    desc_parts.insert(0, part)
                                    # Once we hit non-numbers from the end, the rest (to the left) is description
                                    # But wait, description can contain numbers.
                                    # We assume amounts are strictly at the end.
                                    # If we have collected enough amounts (e.g. 3 for Dr/Cr/Bal, or 2 for Amt/Bal), stop?
                                    # Let's just collect all trailing amounts.
                                    if len(amounts) >= 3: # Max 3 amounts usually
                                        break
                            
                            # Reconstruct description
                            # The description is everything from parts[1] up to the start of amounts
                            # We need to be careful about where we stopped in the reversed loop.
                            # Actually, simpler:
                            # Date is parts[0]
                            # Amounts are the last N parts that look like amounts
                            # Description is everything in between
                            
                            amount_indices = [i for i, part in enumerate(parts) if re.match(r'[\d,]+\.\d{2}', part)]
                            
                            if len(amount_indices) >= 1:
                                first_amount_idx = amount_indices[-1] # Start with last
                                # Try to find the contiguous block of amounts at the end
                                for idx in reversed(amount_indices):
                                    if idx == len(parts) - 1:
                                        first_amount_idx = idx
                                    elif idx == first_amount_idx - 1:
                                        first_amount_idx = idx
                                    else:
                                        break
                                
                                # If the block is at the end
                                if first_amount_idx > 0:
                                    description = " ".join(parts[1:first_amount_idx])
                                    row_amounts = parts[first_amount_idx:]
                                    
                                    # Pad with empty strings if needed to match 4 columns (Date, Desc, Amt, Bal)
                                    # or 5 columns (Date, Desc, Dr, Cr, Bal)
                                    current_row = [date, description] + row_amounts
                                else:
                                    current_row = list(match.groups())
                            else:
                                current_row = list(match.groups())
                        elif current_row:
                            # If no date match, but we have a current row, append text to description
                            # Check if line looks like a footer, page header, or junk content to avoid
                            line_lower = line.lower().strip()
                            
                            # Skip common page elements
                            if any(skip in line_lower for skip in [
                                'page', 'confidential', 'statement of account',
                                # IOB-specific page headers/footers
                                'rep27', 'register', 'report for the period',
                                'brought forward', '----', 'date tran ref',
                                'particulars', 'debit amt', 'credit amt', 'balance amt',
                                'contra', 'indian overseas bank', 'transaction details',
                                'account number', 'service outlet',
                                # IOB URL footers
                                'https://', 'http://', 'iob.in', 'finbranch', 
                                'tran_rpt.jsp', 'arjspmorph',
                                # IOB summary/footer lines
                                'total', 'otal(', 'curr. inr', 'manager', 'chief manager',
                                'date :'  # Footer date stamp
                            ]):
                                continue
                            
                            # Skip empty or very short lines
                            if len(line.strip()) < 3:
                                continue
                            
                            # Skip lines that look like "Id Date" (column header continuation)
                            if line.strip() in ['Id', 'Date', 'Id Date']:
                                continue
                            
                            # Skip lines that look like standalone dates (footer timestamps)
                            # e.g., "11/09/2025" or "11-09-2025"
                            if re.match(r'^\d{2}[/-]\d{2}[/-]\d{4}$', line.strip()):
                                continue
                            
                            # Append to description (Group 2 in regex, which is index 1 in list)
                            current_row[1] += " " + line.strip()
                    
                    # Append the last row
                    if current_row:
                        all_rows.append(current_row)
            else:
                # If tables were found and none were messy, add the extracted rows from tables
                all_rows.extend(extracted_rows_from_tables_on_this_page)
    
    # For text-parsed data (Strategy 3), rows will have exactly 4 elements
    # For table data, rows may have varying lengths
    # Filter rows: if most have exactly 4 elements, keep only those (text-parsed)
    # Otherwise, keep all rows (table-extracted)
    if len(all_rows) > 0:
        row_lengths = [len([x for x in row if x is not None]) for row in all_rows]
        four_col_count = sum(1 for length in row_lengths if length == 4)
        
        # If >80% of rows have exactly 4 non-null elements, filter to 4-column rows (text-parsed)
        if four_col_count / len(all_rows) > 0.8:
            # Text-parsed data - keep only rows with 4 elements
            filtered_rows = [row[:4] if isinstance(row, list) else list(row)[:4] for row in all_rows if len([x for x in row if x is not None]) >= 4]
            df = pd.DataFrame(filtered_rows)
            if len(df.columns) == 4:
                df.columns = ['Date', 'Description', 'Amount', 'Balance']
        else:
            # Table-extracted data - keep all rows as-is
            df = pd.DataFrame(all_rows)
    else:
        df = pd.DataFrame(all_rows)
    
    # Fallback to OCR if no data extracted
    if df.empty:
        print("Standard extraction failed. Attempting OCR...")
        df, bank_name_ocr = extract_from_pdf_ocr(filepath)
        if bank_name == "Unknown Bank":
            bank_name = bank_name_ocr
        
    return df, bank_name

def extract_from_csv(filepath):
    return pd.read_csv(filepath)

def extract_from_excel(filepath):
    return pd.read_excel(filepath)

def extract_from_pdf_ocr(filepath):
    """
    Extracts text from scanned/image-based PDFs using OCR (Tesseract).
    Fallback for PDFs where pdfplumber cannot extract tables or text.
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError:
        print("OCR packages not installed. Install with: pip install pytesseract pdf2image")
        return pd.DataFrame()
    
    # Convert PDF pages to images
    images = convert_from_path(filepath, dpi=200)
    
    all_rows = []
    bank_name = "Unknown Bank (OCR)"
    
    for i, img in enumerate(images):
        # OCR the page with PSM 6 (Assume a single uniform block of text)
        text = pytesseract.image_to_string(img, config='--psm 6')
        
        # Detect bank from first page
        if i == 0:
            bank_name = detect_bank(text)
            
        lines = text.split('\n')
        
        current_row = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # TMB format: DD-MM-YYYY Description [ChqNo] [Withdrawal] [Deposit] [Balance]
            # Match transaction lines starting with date
            date_match = re.match(r'^(\d{2}-\d{2}-\d{4})\s+(.+)', line)
            
            if date_match:
                # Save previous row
                if current_row:
                    all_rows.append(current_row)
                
                date = date_match.group(1)
                rest = date_match.group(2)
                
                # Look for amount patterns at the end: numbers with commas and decimals
                # Pattern: amounts like 1,234.56 or 0 or 0.00
                # We look for the last 3 numbers which likely represent Withdrawal, Deposit, Balance
                # But sometimes ChqNo is there too.
                
                # Strategy: Find all numbers at the end of the string
                # Regex to find numbers (including 0) at the end
                # This is tricky because description can contain numbers.
                # We assume amounts are separated by spaces at the end.
                
                parts = rest.split()
                amounts = []
                description_parts = []
                
                # Iterate backwards to find amounts
                for part in reversed(parts):
                    # Check if part is a number (allow commas and decimals)
                    if re.match(r'^[\d,]+\.?\d*$', part):
                        amounts.insert(0, part)
                    else:
                        # Stop when we hit something that's not a number
                        # But wait, description can end with numbers.
                        # We assume we need at least Balance, and likely Deposit/Withdrawal.
                        # TMB usually has 3 columns at end: Withdrawal, Deposit, Balance
                        if len(amounts) >= 3:
                            break
                        description_parts.insert(0, part)
                
                # Reconstruct description from the remaining parts (and any parts we didn't consume)
                # Actually, a better way:
                # If we found >= 3 amounts, take the last 3 as W, D, B
                # If we found 2 amounts, maybe D, B or W, B?
                # TMB OCR sample: "0.89 0 6,263.11" -> 3 amounts
                
                if len(amounts) >= 3:
                    balance = amounts[-1]
                    deposit = amounts[-2]
                    withdrawal = amounts[-3]
                    # Description is everything before these
                    # We need to be careful not to include ChqNo in amounts if it looks like a number
                    # But if we take last 3, ChqNo should be in description or ignored
                    
                    # Re-find the position of these amounts in 'rest' to split correctly
                    # This is safer than splitting by space
                    
                    # Construct suffix to search for
                    suffix = f"{withdrawal} {deposit} {balance}"
                    idx = rest.rfind(suffix)
                    if idx != -1:
                        description = rest[:idx].strip()
                    else:
                        # Fallback
                        description = " ".join(parts[:-3])
                        
                    current_row = [date, description, withdrawal, deposit, balance]
                    
                elif len(amounts) == 2:
                    # Maybe Withdrawal/Deposit and Balance?
                    # Hard to say. Let's assume Amount and Balance
                    balance = amounts[-1]
                    amount = amounts[-2]
                    current_row = [date, rest.replace(f"{amount} {balance}", "").strip(), amount, '', balance]
                else:
                    # Just date and description, amounts might be on next line (though PSM 6 usually puts them on same line)
                    current_row = [date, rest, '', '', '']
            
            elif current_row:
                # Continuation line - append to description
                # Skip junk lines
                line_lower = line.lower()
                if any(skip in line_lower for skip in [
                    'page', 'statement', 'account', 'balance', 'date', 'particulars',
                    'withdrawal', 'deposit', 'branch', 'customer', 'address', 'mobile',
                    'e-mail', 'tamilnad', 'mercantile', 'be a step'
                ]):
                    continue
                # Check if it's just numbers/amounts (continuation of previous line's amounts)
                if re.match(r'^[\d,\.\s]+$', line):
                    continue
                # Append to description
                current_row[1] += ' ' + line
        
        # Don't forget the last row
        if current_row:
            all_rows.append(current_row)
    
    if all_rows:
        df = pd.DataFrame(all_rows, columns=['Date', 'Description', 'Debit', 'Credit', 'Balance'])
        return df, bank_name
    
    return pd.DataFrame(), bank_name



def clean_data(df):
    
    # 0. Identify Header Row (Restored)
    # Check if current columns already contain keywords
    current_cols_str = " ".join([str(x).lower() for x in df.columns])
    header_keywords = ['date', 'particulars', 'description', 'narration', 'debit', 'withdrawal', 'credit', 'deposit', 'balance']
    
    # Count how many keywords are in the current columns
    keyword_matches = sum(1 for keyword in header_keywords if keyword in current_cols_str)
    
    # If we have enough matches (e.g., 2 or more), assume current headers are correct
    if keyword_matches < 2:
        header_idx = -1
        for i, row in df.iterrows():
            # Convert row to string and check for multiple keywords to be safer
            # Normalize newlines to spaces for proper keyword matching
            row_values = [str(x).lower().replace('\n', ' ') for x in row.values]
            row_str = " ".join(row_values)
            
            # Check for specific combinations that strongly suggest a header
            # e.g. "date" AND ("description" OR "narration" OR "particulars")
            has_date = 'date' in row_str
            has_desc = any(x in row_str for x in ['description', 'narration', 'particulars'])
            has_amount = any(x in row_str for x in ['debit', 'credit', 'withdrawal', 'deposit', 'amount', 'balance'])
            
            # We need at least Date AND (Description OR Amount) to be confident it's a header
            if has_date and (has_desc or has_amount):
                header_idx = i
                break
        
        if header_idx != -1:
            df.columns = df.iloc[header_idx]
            df = df.iloc[header_idx+1:].reset_index(drop=True)

    # 1. Column Mapping
    col_mapping = {
        'txn date': 'Date',  # SBI
        'transaction date': 'Date',  # YES Bank
        'tran date': 'Date', # Axis Bank
        'post date': 'Date',  # SBI-2
        'value date': 'Date',  # SBI-1, ICICI-2, HDFC
        'date': 'Date',  # Union Bank
        'narration': 'Description', # HDFC
        'naration': 'Description', # IOB-1 typo
        'remarks': 'Description',  # Union Bank
        'transaction remarks': 'Description', # ICICI-2
        'description': 'Description', # SBI
        'particulars': 'Description', # IOB
        'transaction details': 'Description',  # Kotak specific
        'debit': 'Debit',
        'withdrawals': 'Debit',  # Union/YES Bank
        'withdrawal': 'Debit',
        'withdraws': 'Debit',
        'withdrawal(dr)': 'Debit',  # BOB specific
        'withdrawal (dr)': 'Debit',  # ICICI-2 specific (with space)
        'withdra wal (dr)': 'Debit',  # ICICI-2 broken newline
        'withdrawalamt.': 'Debit',  # HDFC specific
        'withdrawal amount (inr )': 'Debit', # ICICI-1 specific
        'debit amount': 'Debit',  # IndianBank specific
        'debit(₹)': 'Debit',  # Kotak specific
        'dr': 'Debit',
        'credit': 'Credit',
        'deposit': 'Credit',
        'deposits': 'Credit',  # Union Bank
        'deposit(cr)': 'Credit',  # BOB specific
        'deposit (cr)': 'Credit',  # ICICI-2 specific (with space)
        'depositamt.': 'Credit',  # HDFC specific
        'deposit amount (inr )': 'Credit', # ICICI-1 specific
        'credit amount': 'Credit',  # IndianBank specific
        'credit(₹)': 'Credit',  # Kotak specific
        'cr': 'Credit',
        'balance': 'Balance',
        'balance(inr)': 'Balance',  # BOB specific
        'balance (inr)': 'Balance',  # ICICI-2 specific (with space)
        'balance (inr )': 'Balance', # ICICI-1 specific
        'closing balance': 'Balance',  # IndianBank specific
        'closingbalance': 'Balance',  # HDFC specific
        'balance(₹)': 'Balance',  # Kotak specific
        'running balance': 'Balance',  # YES Bank
        'bal': 'Balance',
        'amount': 'Amount',
        'chq / ref no.': 'Reference',  # Kotak specific
        'chq no': 'Reference', # Axis Bank
        'chq / ref no': 'Reference', # ICICI-2
        'ref no./cheque no.': 'Reference',  # SBI
        'cheque no/reference': 'Reference',  # SBI-2
        'cheque no/ reference no': 'Reference',  # YES Bank
        'chq\nno': 'Reference', # IOB-1
        'cheque no': 'Reference', # CUB
        'chq./ref.no.': 'Reference',  # HDFC
        'tran id-1': 'Reference',  # Union Bank
        'utr number': 'UTR',  # Union Bank
        'instr. id': 'Instrument',  # Union Bank
        'valuedt': 'Value Date',  # HDFC
    }
    new_columns = []
    for col in df.columns:
        clean_col = str(col).replace('\n', ' ').strip().lower()
        mapped_col = col_mapping.get(clean_col, col)
        new_columns.append(mapped_col)
    df.columns = new_columns
    
    # Remove duplicate columns (keep first)
    df = df.loc[:, ~df.columns.duplicated()]
    
    # Ensure required columns exist
    required_cols = ['Date', 'Description', 'Debit', 'Credit', 'Balance']
    for col in required_cols:
        if col not in df.columns:
            if col in ['Debit', 'Credit'] and 'Amount' in df.columns:
                continue
            df[col] = ''
            
    # Drop rows where Date is empty
    df = df[df['Date'].astype(str).str.strip() != '']
    
    # Filter out account header rows (BOB specific - contains "Account" or "XXXXXXXX")
    df = df[~df['Date'].astype(str).str.contains('Account', case=False, na=False)]
    df = df[~df['Date'].astype(str).str.contains('XXXX', na=False)]
    
    # Clean Description column - remove footer junk from various banks
    if 'Description' in df.columns:
        # Common footer patterns to remove from descriptions
        junk_patterns = [
            # HDFC footer patterns
            r'HDFCBANKLIMITED.*',  # Footer text starting with HDFC BANK LIMITED
            r'\*Closingbalanceincludesfunds.*',  # Footer note
            r'Contentsofthisstatementwillbe.*',  # Footer note
            r'STATEMENTSUMMARY.*',  # Summary section
            r'OpeningBalanceDrCountCrCount.*',  # Summary header
            r'GeneratedOn:.*',  # Generated timestamp
            r'GeneratedBy:.*',  # Generated by
            r'RequestingBranchCode:.*',  # Branch code
            r'Thisisacomputergenerated.*',  # Footer note
            r'StateaccountbranchGSTN:.*',  # GSTN footer
            # TMB footer patterns
            r'LIST OF ABBREVATION:.*',  # TMB abbreviation list
            r'#Terms and Conditions Apply.*',  # Terms note
            r'Unless the constituent notifies.*',  # Disclaimer
            r'TR -Transfer.*',  # Abbreviation definitions
        ]
        for pattern in junk_patterns:
            df['Description'] = df['Description'].astype(str).str.replace(pattern, '', regex=True, flags=re.IGNORECASE)
        # Clean up extra spaces
        df['Description'] = df['Description'].str.strip()

    # Fix for YES Bank Misaligned "Credit Interest Capitalised" Row
    # Issue: Description appears in Reference, Amount in Description, Balance in Debit
    if 'Reference' in df.columns and 'Description' in df.columns and 'Debit' in df.columns:
        # Identify rows where Reference contains "Credit Interest Capitalised"
        mask = df['Reference'].astype(str).str.contains('Credit Interest Capitalised', case=False, na=False)
        
        if mask.any():
            # For these rows:
            # New Description = Old Reference
            # New Credit = Old Description (Amount)
            # New Balance = Old Debit (Balance)
            # New Debit = 0
            
            # We need to be careful with types. Convert to appropriate types later.
            # Temporarily store values
            refs = df.loc[mask, 'Reference']
            debits = df.loc[mask, 'Debit']   # Contains Amount (3022)
            credits = df.loc[mask, 'Credit'] # Contains Balance (13388)
            
            df.loc[mask, 'Description'] = refs
            df.loc[mask, 'Credit'] = debits # This will be cleaned by clean_currency later
            df.loc[mask, 'Balance'] = credits # This will be cleaned by clean_currency later
            df.loc[mask, 'Debit'] = 0
            df.loc[mask, 'Reference'] = ''
    
    # 3. Clean Data
    def clean_currency(x):
        if isinstance(x, str):
            # Remove newlines, spaces, commas
            x = x.replace('\n', '').replace(',', '').replace(' ', '').strip()
            
            # Handle empty strings
            if not x or x == '':
                return 0.0
            
            # Handle Cr/Dr suffix
            if x.lower().endswith('cr'):
                return float(x[:-2])
            elif x.lower().endswith('dr'):
                return -float(x[:-2])
            # Handle negative sign at end (sometimes happens)
            if x.endswith('-'):
                x_clean = x[:-1].strip()
                return -float(x_clean) if x_clean else 0.0
            # Handle negative sign at start
            if x.startswith('-'):
                x_clean = x[1:].strip()
                return -float(x_clean) if x_clean else 0.0
            try:
                return float(x)
            except ValueError:
                return 0.0
        elif pd.isna(x) or x is None:
            return 0.0
        return x

    for col in ['Debit', 'Credit', 'Balance', 'Amount']:
        if col in df.columns:
            df[col] = df[col].apply(clean_currency)
            
    # 3. Date Parsing
    # Handle newlines in date (e.g. 12\nApr\n2023 -> 12 Apr 2023)
    # Aggressively remove all newlines and carriage returns
    df['Date'] = df['Date'].astype(str).str.replace('\n', ' ').str.replace('\r', '').str.replace('  ', ' ').str.strip()
    # Remove spaces after / or - (e.g. 10/ 07/ 2023 -> 10/07/2023)
    df['Date'] = df['Date'].str.replace(r'/\s+', '/', regex=True).str.replace(r'-\s+', '-', regex=True)
    # Fix split years (e.g. 20 24 -> 2024, 2 024 -> 2024)
    df['Date'] = df['Date'].str.replace(r'(\d{1,2})\s+(\d{2,4})$', r'\1\2', regex=True)
    # Remove time components
    df['Date'] = df['Date'].str.replace(r'\s+\d{2}:\d{2}:\d{2}.*$', '', regex=True)
    
    df['DateObj'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    
    # Fallback for DD-MMM-YY format if standard parsing fails
    mask = df['DateObj'].isna()
    if mask.any():
        try:
            df.loc[mask, 'DateObj'] = pd.to_datetime(df.loc[mask, 'Date'], format='%d-%b-%Y', errors='coerce')
        except:
            pass
            
    # Fallback for DD-MMM-YYYY format
    mask = df['DateObj'].isna()
    if mask.any():
        try:
            df.loc[mask, 'DateObj'] = pd.to_datetime(df.loc[mask, 'Date'], format='%d-%b-%y', errors='coerce')
        except:
            pass
            
    # Drop rows where Date is invalid
    df = df.dropna(subset=['DateObj'])
    
    # Sort by date
    df = df.sort_values('DateObj')
    
    # Format Date
    df['Date'] = df['DateObj'].dt.strftime('%d-%m-%Y')
    
    # 4. Infer Debit/Credit if only Amount exists
    if 'Debit' not in df.columns and 'Amount' in df.columns:
        # Check if Amount has negative values (indicating debit)
        amount_values = df['Amount'].fillna(0)
        has_negative = (amount_values < 0).any()
        has_positive = (amount_values > 0).any()
        
        if has_negative and has_positive:
            # Signed amount format - directly split based on sign
            df['Debit'] = df['Amount'].apply(lambda x: abs(x) if x < 0 else 0.0)
            df['Credit'] = df['Amount'].apply(lambda x: x if x > 0 else 0.0)
        elif 'Balance' in df.columns:
            # Create temporary numeric columns
            df['AmountNum'] = df['Amount']
            df['BalanceNum'] = df['Balance']
            
            # Detect order
            is_ascending = False
            try:
                is_ascending = df['DateObj'].is_monotonic_increasing
                if is_ascending:
                    df = df.iloc[::-1].reset_index(drop=True)
            except:
                pass
            
            # Initialize
            df['Debit'] = 0.0
            df['Credit'] = 0.0
            
            df['PrevBalance'] = df['BalanceNum'].shift(-1)
            df['Diff'] = df['BalanceNum'] - df['PrevBalance']
            
            for i, row in df.iterrows():
                if pd.isna(row['PrevBalance']):
                    desc = str(row['Description']).lower()
                    if 'credit' in desc or 'deposit' in desc:
                        df.at[i, 'Credit'] = row['AmountNum']
                    else:
                        df.at[i, 'Debit'] = row['AmountNum']
                    continue
                
                diff = row['Diff']
                amount = row['AmountNum']
                
                if abs(diff - amount) < 1.0:
                    df.at[i, 'Credit'] = amount
                elif abs(diff + amount) < 1.0:
                    df.at[i, 'Debit'] = amount
                else:
                    if diff < 0:
                        df.at[i, 'Debit'] = amount
                    else:
                        df.at[i, 'Credit'] = amount
            
            if is_ascending:
                df = df.iloc[::-1].reset_index(drop=True)
                
    # Fill NaN with 0
    if 'Debit' in df.columns:
        df['Debit'] = df['Debit'].fillna(0.0)
    if 'Credit' in df.columns:
        df['Credit'] = df['Credit'].fillna(0.0)
        
    
    if 'Description' in df.columns:
        df['Description'] = df['Description'].astype(str).str.replace('\n', ' ').str.replace(r'\s+', ' ', regex=True).str.strip()
        
    return df[['Date', 'Description', 'Debit', 'Credit', 'Balance']]


def extract_from_pdf(filepath):
    """
    Extracts tables from a PDF bank statement.
    Returns: (DataFrame, bank_name)
    """
    all_rows = []
    bank_name = "Unknown Bank"
    
    with pdfplumber.open(filepath) as pdf:
        # Detect bank from first page text
        if len(pdf.pages) > 0:
            first_page_text = pdf.pages[0].extract_text() or ""
            bank_name = detect_bank(first_page_text)
            
        for page in pdf.pages:
            tables = page.extract_tables()
            
            page_has_messy_tables = False
            extracted_rows_from_tables_on_this_page = [] # Collect rows from tables for this page

            # Strategy 1: Standard Table Extraction
            if tables:
                for table in tables:
                    # Check if it's a valid transaction table
                    # Heuristic: Skip tables that look like Account Summary or Legends
                    if not table or not table[0]:
                        continue
                        
                    headers = [str(cell).lower() for cell in table[0] if cell]
                    header_str = " ".join(headers)
                    
                    # Skip Account Summary tables
                    if 'account no' in header_str and 'currency' in header_str:
                        continue
                    # Skip Legend tables (check headers and first data row)
                    if 'ib trf' in header_str or 'term deposit' in header_str:
                        continue
                    # Also check first data row for legend content
                    if len(table) > 1 and table[1]:
                        first_row_str = " ".join([str(cell).lower() for cell in table[1] if cell])
                        if ('point of sales' in first_row_str or 'term deposit' in first_row_str or 
                            'immediate payment' in first_row_str):
                            continue
                    
                    # Check for "messy" tables (merged rows)
                    # Only check for messiness if this looks like a TRANSACTION table
                    # (has headers like date, amount, balance, withdrawal, deposit, etc.)
                    # This avoids flagging non-transaction tables (like customer details) as messy
                    looks_like_transaction_table = any(keyword in header_str for keyword in 
                        ['date', 'amount', 'balance', 'withdrawal', 'deposit', 'debit', 'credit', 
                         'particulars', 'narration', 'description', 'transaction'])
                    
                    is_messy_table = False
                    if looks_like_transaction_table:
                        # Heuristic: If the FIRST column has multiple newlines (>5), it's likely a merged row table (like HDFC)
                        # If only a few newlines (1-3), it's just wrapped text and is fine.
                        for row in table:
                            # Check first cell (Date) for many newlines
                            if row and row[0] and str(row[0]).count('\n') > 5:
                                is_messy_table = True
                                page_has_messy_tables = True
                                break
                            # Also check if *many* cells have newlines (e.g. > 50% of cells in a row)
                            # This handles cases where Date might be clean but everything else is merged
                            newline_cells = sum(1 for cell in row if cell and str(cell).count('\n') > 5)
                            if len(row) > 0 and newline_cells / len(row) > 0.5:
                                 is_messy_table = True
                                 page_has_messy_tables = True
                                 break
                            if is_messy_table:
                                break
                    
                    if is_messy_table:
                        # If a table is messy, we skip it and rely on text parsing for the whole page.
                        # We don't want to mix potentially bad table data with good text data.
                        continue 
                    else:
                        for row in table:
                            # Clean row
                            cleaned_row = [cell.strip() if cell else '' for cell in row]
                            # Check if it's a "merged" row (1 column containing everything)
                            if len(cleaned_row) == 1 and cleaned_row[0]:
                                # Strategy 2: Regex Parsing for Merged Rows
                                # Pattern: Date ... Amount ... Balance (or Balance ... Amount due to wrapping)
                                text = cleaned_row[0].replace('\n', ' ')
                                
                                # 1. Extract Date
                                date_match = re.search(r'^(\d{2}[/-]\d{2}[/-]\d{2,4})', text)
                                if date_match:
                                    date = date_match.group(1)
                                    
                                    # 2. Extract all potential money values (e.g. 10,000.00 or 10,000.00Cr)
                                    # Regex: digits, commas, dot, 2 digits, optional Cr/Dr/suffix
                                    money_matches = list(re.finditer(r'([\d,]+\.\d{2})([A-Za-z]*)', text))
                                    
                                    if len(money_matches) >= 2:
                                        # We take the last two matches as Amount and Balance
                                        # But we need to decide which is which.
                                        val1_full = money_matches[-2].group(0)
                                        val1_num = money_matches[-2].group(1)
                                        val1_suffix = money_matches[-2].group(2).lower()
                                        
                                        val2_full = money_matches[-1].group(0)
                                        val2_num = money_matches[-1].group(1)
                                        val2_suffix = money_matches[-1].group(2).lower()
                                        
                                        # Heuristic: Balance usually has Cr/Dr. Amount often doesn't in this format.
                                        # Also, Balance is usually the last number visually, but wrapping might swap them.
                                        
                                        amount = None
                                        balance = None
                                        
                                        if 'cr' in val1_suffix or 'dr' in val1_suffix:
                                            if 'cr' not in val2_suffix and 'dr' not in val2_suffix:
                                                # Val1 is Balance, Val2 is Amount
                                                balance = val1_full
                                                amount = val2_full
                                        elif 'cr' in val2_suffix or 'dr' in val2_suffix:
                                            # Val2 is Balance, Val1 is Amount
                                            balance = val2_full
                                            amount = val1_full
                                        else:
                                            # Neither has suffix, assume standard order: Amount, Balance
                                            amount = val1_full
                                            balance = val2_full
                                        
                                        # Description is everything between Date and the first money match (of the last two)
                                        # Or just remove Date and Money from text
                                        # Let's try to slice the string
                                        desc_start = date_match.end()
                                        # We need the start index of the "first" of our two money values in the original string
                                        # But we used finditer on the *replaced* text.
                                        # money_matches[-2] is the Amount (or Balance).
                                        desc_end = money_matches[-2].start()
                                        
                                        desc = text[desc_start:desc_end].strip()
                                        
                                        if amount and balance:
                                            extracted_rows_from_tables_on_this_page.append([date, desc, amount, balance])
                                        else:
                                            extracted_rows_from_tables_on_this_page.append(cleaned_row)
                                else:
                                    extracted_rows_from_tables_on_this_page.append(cleaned_row)
                            elif any(cleaned_row):
                                extracted_rows_from_tables_on_this_page.append(cleaned_row)

            # Strategy 3: Raw Text Parsing (Fallback or Primary)
            # We run this if no tables found OR if we detected a "messy" table (which we skipped above)
            # To avoid duplicates, we should only run this if we didn't extract good rows from tables.
            # But checking "if not all_rows" is risky because we might have extracted some rows from a summary table on Page 1.
            # So we should run text parsing for the *current page* if tables were messy or missing.
            # But extract_tables() returns all tables on page.
            
            # Revised Logic:
            # Check if page has messy tables.
            # This check is already done above, `page_has_messy_tables` is set.
            
            # Also check for "sparse" tables - tables with very few rows (like Kotak which only has headers)
            page_has_sparse_tables = False
            if tables:
                max_table_rows = max(len(table) for table in tables if table)
                if max_table_rows < 3:  # Only header rows, no real data
                    page_has_sparse_tables = True
            
            if not tables or page_has_messy_tables or page_has_sparse_tables:
                text = page.extract_text()
                if text:
                    # State for multi-line descriptions
                    current_row = None
                    
                    for line in text.split('\n'):

                        # Regex 1: Standard DD/MM/YYYY or DD-MM-YYYY
                        match1 = re.search(r'^(\d{2}[/-]\d{2}[/-]\d{2,4})\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2}[A-Za-z]*)$', line)
                        
                        # Regex 2: DBS Format (DD-Mon-YYYY) with double date
                        # e.g. 02-Apr-2023 02-Apr-2023 UPI... 312.00 10,802.65
                        match2 = re.search(r'^(\d{2}-[A-Za-z]{3}-\d{4})\s+(?:\d{2}-[A-Za-z]{3}-\d{4}\s+)?(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2}[A-Za-z]*)$', line)
                        
                        # Regex 1b: Indian Bank Format 2 (DD/MM/YY)
                        # e.g. 01/04/24 01/04/24 s /UPI/409224310724/Payment from 1393.00 8437.37Cr
                        match1c = None
                        match1b = re.search(r'^(\d{2}/\d{2}/\d{2})\s+(?:\d{2}/\d{2}/\d{2})\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2}[A-Za-z]*)$', line)
                        if match1b:
                             match1c = (match1b.group(1), match1b.group(2), match1b.group(3), match1b.group(4))
             
             
                        # e.g. 05-04-2024S88727140 0006585769 Charges for PORD Customer 4.72 2,02,682.19CR
                        # e.g. 05-04-2024S88727140 0006585769 Charges for PORD Customer 4.72 2,02,682.19CR
                        # Format: DD-MM-YYYYTranID RefNum Particulars [Debit] [Credit] BalanceCR/DR
                        match3 = None
                        iob2_match = re.match(r'^(\d{2}-\d{2}-\d{4})([A-Z]\d+|\s*IB\d+)?\s*(\d+)?\s+(.+?)(?:\s+([\d,]+\.\d{2}))?\s+([\d,]+\.\d{2})(CR|DR)?$', line)
                        if iob2_match:
                            date = iob2_match.group(1)
                            tran_id = iob2_match.group(2) or ''
                            ref_num = iob2_match.group(3) or ''
                            particulars = iob2_match.group(4).strip()
                            amount1 = iob2_match.group(5) or '0.00'  # May be debit or credit
                            balance = iob2_match.group(6)
                            balance_suffix = iob2_match.group(7) or ''
                            
                            # Description includes tran_id if present
                            desc = particulars
                            if tran_id:
                                desc = tran_id.strip() + ' ' + desc
                            if ref_num:
                                desc = ref_num + ' ' + desc
                            
                            # For IOB-2, we store as (Date, Desc, Amount, Balance+Suffix)
                            match3 = (date, desc.strip(), amount1, balance + balance_suffix)
                        
                        # Regex 4: Kotak Format
                        # e.g. 1 02 Apr 2023 LOCKER RENT FOR 46/R1/0035 CMS- -1,770.00 19,654.09
                        # Format: # DD Mon YYYY Description Ref# [+/-]Amount Balance
                        # Note: Description may be followed by time (08:32 PM) on the next line which gets joined
                        match4 = None
                        kotak_match = re.match(r'^(\d+)\s+(\d{2}\s+[A-Za-z]{3}\s+\d{4})\s+(.+?)\s+([+-]?[\d,]+\.\d{2})\s+([\d,]+\.\d{2})$', line)
                        if kotak_match:

                            serial = kotak_match.group(1)
                            date = kotak_match.group(2)
                            description = kotak_match.group(3).strip()
                            amount = kotak_match.group(4)
                            balance = kotak_match.group(5)
                            
                            # Clean time stamps from description (e.g., "08:32 PM")
                            description = re.sub(r'\s+\d{2}:\d{2}\s+[AP]M$', '', description)
                            
                            # For Kotak, store as (Date, Desc, Amount, Balance)
                            match4 = (date, description, amount, balance)
                        
                        match = match1 or match2 or match1c or match3 or match4
                        
                        if match:
                            # If we have a pending row, add it first
                            if current_row:
                                all_rows.append(current_row)
                            
                            # Start new row - handle both match objects and tuples
                            if isinstance(match, tuple):
                                # List unpacking for tuple matches (Indian Bank, Kotak)
                                t_date, t_desc, t_amt, t_bal = match
                                t_date, t_desc, t_amt, t_bal = match
                                current_row = [t_date, t_desc.strip(), t_amt, t_bal]
                            else:
                                current_row = list(match.groups())

                            # Post-processing: specific fixes based on bank name
                            # If Indian Bank, strip date prefix from Description if it leaked in
                            if bank_name == 'Indian Bank':
                                if isinstance(current_row, dict):
                                    desc_val = current_row.get('Description', '')
                                    if re.match(r'^\s*\d{2}/\d{2}/\d{2}', desc_val):
                                        current_row['Description'] = re.sub(r'^\s*\d{2}/\d{2}/\d{2}\s*', '', desc_val).strip()
                                elif isinstance(current_row, list):
                                    if len(current_row) >= 2:
                                        desc_val = current_row[1]
                                        if re.match(r'^\s*\d{2}/\d{2}/\d{2}', desc_val):
                                            current_row[1] = re.sub(r'^\s*\d{2}/\d{2}/\d{2}\s*', '', desc_val).strip()


                        # Check for Opening Balance line (BOB-2 specific) to seed running_balance
                        # Format: Opening Balance : 56,135.47Cr
                        op_bal_match = re.search(r'Opening Balance\s*:\s*([\d,]+\.\d{2})([A-Za-z]*)', line, re.IGNORECASE)
                        if op_bal_match:
                            amount_str = op_bal_match.group(1).replace(',', '')
                            suffix = op_bal_match.group(2).lower()
                            running_balance = float(amount_str)
                            if 'dr' in suffix:
                                running_balance *= -1
                        
                        # Regex 5: BOB-2 Format
                        # Format: GL.Date Val.Date Description Amount Balance UserIDs
                        # e.g. 14-12-2024 14-12-2024 UPI/434991474329/... 112.00 4,068.37Cr CDCI CDCI
                        bob2_match = re.match(r'^(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})([A-Za-z]*)', line)
                        if bob2_match and bank_name == 'Bank of Baroda':
                            gl_date = bob2_match.group(1)
                            val_date = bob2_match.group(2)
                            desc = bob2_match.group(3).strip()
                            amt_str = bob2_match.group(4)
                            bal_str = bob2_match.group(5)
                            bal_suffix = bob2_match.group(6).lower()
                            
                            # Clean values
                            amt_val = float(amt_str.replace(',', ''))
                            bal_val = float(bal_str.replace(',', ''))
                            if 'dr' in bal_suffix:
                                bal_val *= -1
                                
                            # Determine Debit/Credit based on running_balance
                            debit = ''
                            credit = ''
                            
                            if running_balance is not None:
                                # Check if Balance increased (Credit) or decreased (Debit)
                                # Round to 2 decimals to avoid float issues
                                diff = bal_val - running_balance
                                
                                # If Balance increased by approx Amount -> Credit
                                if abs(diff - amt_val) < 1.0:
                                    credit = amt_str
                                # If Balance decreased by approx Amount -> Debit
                                elif abs(diff + amt_val) < 1.0:
                                    debit = amt_str
                                else:
                                    # Fallback: Check if Merchant + UPI -> Credit?
                                    # Or default to Debit?
                                    # For safely, put in Debit if unsure, but this might be wrong.
                                    # Let's assume Credit if typical for this file (Credits > Debits?)
                                    # Without context, we default to Debit as it's more common for "Expenses" but UPI collections are Credits.
                                    # Let's rely on text analysis: if it's "Interest" -> Credit.
                                    # If it's pure number match failing, maybe look at description logic later.
                                    # For now, default to Debit.
                                    debit = amt_str
                            else:
                                # No running balance seeded. Fallback to heuristics.
                                # "UPI" in description could be either.
                                # Let's assume the first number is Debit (standard convention) unless we know otherwise.
                                debit = amt_str
                                
                            # Update running balance
                            running_balance = bal_val
                            
                            current_row = [gl_date, desc, debit, credit, bal_str + bal_suffix]
                            if current_row:
                                all_rows.append(current_row)
                            continue

                        elif current_row:
                            # If no date match, but we have a current row, append text to description
                            # Check if line looks like a footer, page header, or junk content to avoid
                            line_lower = line.lower().strip()
                            
                            # Skip common page elements
                            if any(skip in line_lower for skip in [
                                'page', 'confidential', 'statement of account',
                                'closing balance', 'statement summary', 'statement dr. count', '*** end of statement ***',
                                'dr. count', 'cr. count', 'summary', 'in case your account', 'statement',
                                'transaction with extra care',
                                # IOB-specific page headers/footers
                                'rep27', 'register', 'report for the period',
                                'brought forward', '----', 'date tran ref',
                                'particulars', 'debit amt', 'credit amt', 'balance amt',
                                'contra', 'indian overseas bank', 'transaction details',
                                'account number', 'service outlet',
                                # IOB URL footers
                                'https://', 'http://', 'iob.in', 'finbranch', 
                                'tran_rpt.jsp', 'arjspmorph',
                                # IOB summary/footer lines
                                'total', 'otal(', 'curr. inr', 'manager', 'chief manager',
                                'date :'  # Footer date stamp
                            ]):
                                continue
                            
                            # Skip empty or very short lines
                            if len(line.strip()) < 3:
                                continue
                            
                            # Skip lines that look like "Id Date" (column header continuation)
                            if line.strip() in ['Id', 'Date', 'Id Date']:
                                continue
                            
                            # Skip lines that look like standalone dates (footer timestamps)
                            # e.g., "11/09/2025" or "11-09-2025"
                            if re.match(r'^\d{2}[/-]\d{2}[/-]\d{4}$', line.strip()):
                                continue
                            
                            # Append to description (Group 2 in regex, which is index 1 in list)
                            if isinstance(current_row, dict):
                                current_row['Description'] += " " + line.strip()
                            else:
                                current_row[1] += " " + line.strip()
                    
                    # Append the last row
                    if current_row:
                        all_rows.append(current_row)
            else:
                # If tables were found and none were messy, add the extracted rows from tables
                all_rows.extend(extracted_rows_from_tables_on_this_page)
    
    # For text-parsed data (Strategy 3), rows will have exactly 4 elements
    # For table data, rows may have varying lengths
    # Filter rows: if most have exactly 4 elements, keep only those (text-parsed)
    # Otherwise, keep all rows (table-extracted)
    if len(all_rows) > 0:
        row_lengths = [len([x for x in row if x is not None]) for row in all_rows]
        four_col_count = sum(1 for length in row_lengths if length == 4)
        
        # If >80% of rows have exactly 4 non-null elements, filter to 4-column rows (text-parsed)
        if four_col_count / len(all_rows) > 0.8:
            # Text-parsed data - keep only rows with 4 elements
            filtered_rows = [row[:4] if isinstance(row, list) else list(row)[:4] for row in all_rows if len([x for x in row if x is not None]) >= 4]
            df = pd.DataFrame(filtered_rows)
            if len(df.columns) == 4:
                df.columns = ['Date', 'Description', 'Amount', 'Balance']
                # Filter out header rows that might have been captured
                df = df[df['Date'] != 'Date']
        else:
            # Check for 5-column rows (e.g. BOB-2, TMB Text Strategy)
            five_col_count = sum(1 for length in row_lengths if length == 5)
            if five_col_count / len(all_rows) > 0.8:
                filtered_rows = [row[:5] if isinstance(row, list) else list(row)[:5] for row in all_rows if len([x for x in row if x is not None]) >= 5]
                df = pd.DataFrame(filtered_rows)
                if len(df.columns) == 5:
                    df.columns = ['Date', 'Description', 'Debit', 'Credit', 'Balance']
            else:
                # Table-extracted data - keep all rows as-is
                df = pd.DataFrame(all_rows)
    else:
        df = pd.DataFrame(all_rows)
    
    # Fallback to OCR if no data extracted
    if df.empty:
        print("Standard extraction failed. Attempting OCR...")
        df, bank_name_ocr = extract_from_pdf_ocr(filepath)
        if bank_name == "Unknown Bank":
            bank_name = bank_name_ocr
        
    return df, bank_name

def extract_from_csv(filepath):
    return pd.read_csv(filepath)

def extract_from_excel(filepath):
    return pd.read_excel(filepath)

def extract_from_pdf_ocr(filepath):
    """
    Extracts text from scanned/image-based PDFs using OCR (Tesseract).
    Fallback for PDFs where pdfplumber cannot extract tables or text.
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError:
        print("OCR packages not installed. Install with: pip install pytesseract pdf2image")
        return pd.DataFrame()
    
    # Convert PDF pages to images
    images = convert_from_path(filepath, dpi=200)
    
    all_rows = []
    bank_name = "Unknown Bank (OCR)"
    
    for i, img in enumerate(images):
        # OCR the page with PSM 6 (Assume a single uniform block of text)
        text = pytesseract.image_to_string(img, config='--psm 6')
        
        # Detect bank from first page
        if i == 0:
            bank_name = detect_bank(text)
            
        lines = text.split('\n')
        
        current_row = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # TMB format: DD-MM-YYYY Description [ChqNo] [Withdrawal] [Deposit] [Balance]
            # Match transaction lines starting with date
            date_match = re.match(r'^(\d{2}-\d{2}-\d{4})\s+(.+)', line)
            
            if date_match:
                # Save previous row
                if current_row:
                    all_rows.append(current_row)
                
                date = date_match.group(1)
                rest = date_match.group(2)
                
                # Look for amount patterns at the end: numbers with commas and decimals
                # Pattern: amounts like 1,234.56 or 0 or 0.00
                # We look for the last 3 numbers which likely represent Withdrawal, Deposit, Balance
                # But sometimes ChqNo is there too.
                
                # Strategy: Find all numbers at the end of the string
                # Regex to find numbers (including 0) at the end
                # This is tricky because description can contain numbers.
                # We assume amounts are separated by spaces at the end.
                
                parts = rest.split()
                amounts = []
                description_parts = []
                
                # Iterate backwards to find amounts
                for part in reversed(parts):
                    # Check if part is a number (allow commas and decimals)
                    if re.match(r'^[\d,]+\.?\d*$', part):
                        amounts.insert(0, part)
                    else:
                        # Stop when we hit something that's not a number
                        # But wait, description can end with numbers.
                        # We assume we need at least Balance, and likely Deposit/Withdrawal.
                        # TMB usually has 3 columns at end: Withdrawal, Deposit, Balance
                        if len(amounts) >= 3:
                            break
                        description_parts.insert(0, part)
                
                # Reconstruct description from the remaining parts (and any parts we didn't consume)
                # Actually, a better way:
                # If we found >= 3 amounts, take the last 3 as W, D, B
                # If we found 2 amounts, maybe D, B or W, B?
                # TMB OCR sample: "0.89 0 6,263.11" -> 3 amounts
                
                if len(amounts) >= 3:
                    balance = amounts[-1]
                    deposit = amounts[-2]
                    withdrawal = amounts[-3]
                    # Description is everything before these
                    # We need to be careful not to include ChqNo in amounts if it looks like a number
                    # But if we take last 3, ChqNo should be in description or ignored
                    
                    # Re-find the position of these amounts in 'rest' to split correctly
                    # This is safer than splitting by space
                    
                    # Construct suffix to search for
                    suffix = f"{withdrawal} {deposit} {balance}"
                    idx = rest.rfind(suffix)
                    if idx != -1:
                        description = rest[:idx].strip()
                    else:
                        # Fallback
                        description = " ".join(parts[:-3])
                        
                    current_row = [date, description, withdrawal, deposit, balance]
                    
                elif len(amounts) == 2:
                    # Maybe Withdrawal/Deposit and Balance?
                    # Hard to say. Let's assume Amount and Balance
                    balance = amounts[-1]
                    amount = amounts[-2]
                    current_row = [date, rest.replace(f"{amount} {balance}", "").strip(), amount, '', balance]
                else:
                    # Just date and description, amounts might be on next line (though PSM 6 usually puts them on same line)
                    current_row = [date, rest, '', '', '']
            
            elif current_row:
                # Continuation line - append to description
                # Skip junk lines
                line_lower = line.lower()
                if any(skip in line_lower for skip in [
                    'page', 'statement', 'account', 'balance', 'date', 'particulars',
                    'withdrawal', 'deposit', 'branch', 'customer', 'address', 'mobile',
                    'e-mail', 'tamilnad', 'mercantile', 'be a step'
                ]):
                    continue
                # Check if it's just numbers/amounts (continuation of previous line's amounts)
                if re.match(r'^[\d,\.\s]+$', line):
                    continue
                # Append to description
                current_row[1] += ' ' + line
        
        # Don't forget the last row
        if current_row:
            all_rows.append(current_row)
    
    if all_rows:
        df = pd.DataFrame(all_rows, columns=['Date', 'Description', 'Debit', 'Credit', 'Balance'])
        return df, bank_name
    
    return pd.DataFrame(), bank_name



def clean_currency(x):
    if isinstance(x, str):
        # Remove commas
        clean_str = x.replace(',', '').strip()
        # Check for Cr/Dr
        factor = 1.0
        if clean_str.lower().endswith('dr'):
            factor = -1.0
            clean_str = clean_str[:-2]
        elif clean_str.lower().endswith('cr'):
            clean_str = clean_str[:-2]
        
        try:
            return float(clean_str) * factor
        except:
            return 0.0
    return x


def generate_tally_xml(df):
    """
    Generates Tally-compatible XML from the cleaned DataFrame.
    """
    try:
        # Import html here to avoid circular imports or just use standard lib
        import html
    except:
        pass

    xml = ['<ENVELOPE>', ' <HEADER>', '  <TALLYREQUEST>Import Data</TALLYREQUEST>', ' </HEADER>', ' <BODY>', '  <IMPORTDATA>', '   <REQUESTDESC>', '    <REPORTNAME>Vouchers</REPORTNAME>', '   </REQUESTDESC>', '   <REQUESTDATA>']
    
    for index, row in df.iterrows():
        try:
            date_val = pd.to_datetime(row['Date'], dayfirst=True)
            date_str = date_val.strftime('%Y%m%d')
        except:
            continue # Skip invalid dates

        narr = str(row['Description']).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        try:
            debit = float(row.get('Debit', 0))
            credit = float(row.get('Credit', 0))
        except:
            debit = 0.0
            credit = 0.0
            
        # Tally Logic:
        # Payment Vch: Bank Amount = Positive (Credit), Party Amount = Negative (Debit)
        # Receipt Vch: Bank Amount = Negative (Debit), Party Amount = Positive (Credit)
        
        if debit > 0:
            vch_type = "Payment"
            bank_is_deemed_positive = "No" # Credit
            party_is_deemed_positive = "Yes" # Debit
            bank_amount = debit 
            party_amount = -debit
        else:
            vch_type = "Receipt"
            bank_is_deemed_positive = "Yes" # Debit
            party_is_deemed_positive = "No" # Credit
            bank_amount = -credit
            party_amount = credit

        xml.append('    <TALLYMESSAGE xmlns:UDF="TallyUDF">')
        xml.append(f'     <VOUCHER VCHTYPE="{vch_type}" ACTION="Create" OBJVIEW="Accounting Voucher View">')
        xml.append(f'      <DATE>{date_str}</DATE>')
        xml.append(f'      <NARRATION>{narr}</NARRATION>')
        xml.append(f'      <VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME>')
        xml.append(f'      <EFFECTIVEDATE>{date_str}</EFFECTIVEDATE>')
        
        # Bank Ledger
        xml.append('      <ALLLEDGERENTRIES.LIST>')
        xml.append('       <LEDGERNAME>Bank Account</LEDGERNAME>')
        xml.append(f'       <ISDEEMEDPOSITIVE>{bank_is_deemed_positive}</ISDEEMEDPOSITIVE>')
        xml.append(f'       <AMOUNT>{bank_amount:.2f}</AMOUNT>')
        xml.append('      </ALLLEDGERENTRIES.LIST>')
        
        # Suspense Ledger
        xml.append('      <ALLLEDGERENTRIES.LIST>')
        xml.append('       <LEDGERNAME>Suspense Account</LEDGERNAME>')
        xml.append(f'       <ISDEEMEDPOSITIVE>{party_is_deemed_positive}</ISDEEMEDPOSITIVE>')
        xml.append(f'       <AMOUNT>{party_amount:.2f}</AMOUNT>')
        xml.append('      </ALLLEDGERENTRIES.LIST>')
        
        xml.append('     </VOUCHER>')
        xml.append('    </TALLYMESSAGE>')
        
    xml.extend(['   </REQUESTDATA>', '  </IMPORTDATA>', ' </BODY>', '</ENVELOPE>'])
    
    return '\n'.join(xml)

