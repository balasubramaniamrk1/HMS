
import re
import pandas as pd

# Mock data provided by user
test_cases = [
    {
        "bank": "DBS Bank",
        "line": "UPI~309268981917~mprakash33337@ybl~P 02-Apr-2023 02-Apr-2023 UPI~309268981917~mprakash33337@ybl~P 312.00 10,802.65 RAKASH M -YBLa4811926b70f4b37ab882cf030f"
    },
    {
        "bank": "HDFC Bank",
        "line": "MONTHLYINTERESTCREDIT50300701637747 3304220230410781 10/04/23 10/04/23 MONTHLYINTERESTCREDIT50300701637747 3304220230410781 10/04/23 2,743.00 210,806.82"
    },
    {
        "bank": "Indian Bank", # Derived from 'Indian Bank-2'
        "line": "s /UPI/409224310724/Payment from 01/04/24 01/04/24 s /UPI/409224310724/Payment from 1393.00 8437.37Cr PhonePe /BRANCH : ATM SERVI CE BRANCH IOBA0000097/P AKILA /XXXXX /7550110380@ibl /UPI/40920190280"
    },
    {
        "bank": "Indian Overseas Bank", # Derived from 'IOB -2'
        "line": "S54229698 NEFT-RBIS-RBI094249036941 02-04-2024S54229698 NEFT-RBIS-RBI094249036941 14,279.00 92,248.17CR"
    },
    {
        "bank": "Kotak Mahindra Bank",
        "line": "LOCKER RENT FOR 46/R1/0035 CMS- 1 02 Apr 2023 LOCKER RENT FOR 46/R1/0035 CMS- -1,770.00 19,654.09 08:32 PM 210709000010"
    }
]

def debug_line(bank_name, line):
    print(f"\n--- Testing: {bank_name} ---")
    print(f"Line: {line}")
    
    # Simulate the logic in utils.py (Strategy 3 Loop)
    # We will copy-paste relevant regex logic from utils.py here or import if possible.
    # Since we can't easily import the *internal* loop, we simulate it.
    
    current_row = []
    
    # 1. Regex Match Attempt (Simulating lines 1130+ of utils.py)
    
    # Indian Bank (match1)
    # ^(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+([\d,]+\.\d{2})\s+([A-Za-z]{2})\s+([\d,]+\.\d{2})([A-Za-z]{2})$
    match1 = re.match(r'^(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+([\d,]+\.\d{2})\s+([A-Za-z]{2})\s+([\d,]+\.\d{2})([A-Za-z]{2})$', line)
    
    # IOB (match2)
    # ^(\d{2}-\d{2}-\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s+([CD][rn])\s+([\d,]+\.\d{2})([CD][rn])$
    match2 = re.match(r'^(\d{2}-\d{2}-\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s+([CD][rn])\s+([\d,]+\.\d{2})([CD][rn])$', line, re.IGNORECASE)
    
    # Generic Date Start
    # ^(\d{2}[/-]\w{3}[/-]\d{2,4}|\d{2}[/-]\d{2}[/-]\d{2,4})
    date_match = re.match(r'^(\d{2}[/-]\w{3}[/-]\d{2,4}|\d{2}[/-]\d{2}[/-]\d{2,4})', line)
    
    # IOB-2 Specific Logic (from code)
    # ^(\d{2}-\d{2}-\d{4})\s+(\S+)\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})([A-Za-z]*)
    iob2_match = re.match(r'^(\d{2}-\d{2}-\d{4})\s+(\S+)\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})([A-Za-z]*)', line)
    
    # Kotak Logic
    # ^(\d+)\s+(\d{2}\s+[A-Za-z]{3}\s+\d{4})\s+(.+?)\s+([+-]?[\d,]+\.\d{2})\s+([\d,]+\.\d{2})$
    kotak_match = re.match(r'^(\d+)\s+(\d{2}\s+[A-Za-z]{3}\s+\d{4})\s+(.+?)\s+([+-]?[\d,]+\.\d{2})\s+([\d,]+\.\d{2})$', line)

    matched = False
    
    if bank_name == 'Indian Overseas Bank' and iob2_match:
         print("Matched IOB-2 Regex")
         print(iob2_match.groups())
         matched = True
         
    elif bank_name == 'Kotak Mahindra Bank' and kotak_match:
         print("Matched Kotak Regex")
         print(kotak_match.groups())
         matched = True
         
    elif date_match:
         print("Matched Generic Date Regex")
         print(date_match.groups())
         matched = True
    
    if not matched:
        print("NO MATCH found at start of line.")
        
        # New Logic from utils.py
        date_search = re.search(r'(\d{2}[/-]\w{3}[/-]\d{2,4}|\d{2}[/-]\d{2}[/-]\d{2,4}|\d{2}\s+[A-Za-z]{3}\s+\d{4})', line)
                            
        if date_search:
            print(f"Proposed Fix: Found date at index {date_search.start()}: {date_search.group(0)}")
            # Split line around date
            pre_text = line[:date_search.start()].strip()
            date_text = date_search.group(0)
            post_text = line[date_search.end():].strip()
            
            parts = post_text.split()
            amounts = []
            
            # Find amounts at end of post_text
            last_amount_idx = -1
            skipped_count = 0
            MAX_SKIP = 20
            
            for i, part in enumerate(reversed(parts)):
                clean_part = re.sub(r'[a-zA-Z,]', '', part.lower())
                # Allow negative numbers (starting with -)
                if re.match(r'^-?[\d\.]+$', clean_part) and '.' in clean_part:
                    amounts.insert(0, part)
                    last_amount_idx = i
                    skipped_count = 0
                else:
                    if part.lower() in ['dr', 'cr']:
                            amounts.insert(0, part)
                    else:
                            if len(amounts) >= 2: 
                                break
                            elif len(amounts) > 0:
                                break
                            else:
                                skipped_count += 1
                                if skipped_count > MAX_SKIP:
                                    break
            
            print(f"Extracted Amounts: {amounts}")
            
            description = pre_text
            if len(amounts) > 0:
                first_amt_token = amounts[0]
                split_idx = -1
                for idx in range(len(parts)-1, -1, -1):
                    if parts[idx] == first_amt_token:
                        split_idx = idx
                        break
                        
                desc_post_parts = parts[:split_idx] if split_idx != -1 else parts
                post_desc_str = " ".join(desc_post_parts)
                
                # Deduplication Strategy:
                if pre_text in post_desc_str:
                    post_desc_str = post_desc_str.replace(pre_text, '').strip()
                
                if post_desc_str in pre_text:
                    post_desc_str = ""
                
                description += " " + post_desc_str
            
            print(f"Final Description: {description.strip()}")
            
            merged_amounts = []
            i = 0
            while i < len(amounts):
                curr = amounts[i]
                if i + 1 < len(amounts) and amounts[i+1].lower() in ['dr', 'cr']:
                    curr += amounts[i+1]
                    i += 1
                merged_amounts.append(curr)
                i += 1
            print(f"Merged Amounts: {merged_amounts}")
            
        else:
            print("Proposed Fix: No date found anywhere.")

if __name__ == "__main__":
    for case in test_cases:
        debug_line(case['bank'], case['line'])
