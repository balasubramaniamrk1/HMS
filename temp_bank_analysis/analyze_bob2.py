
import pdfplumber
import sys

filepath = 'BOB-2.pdf'

try:
    with pdfplumber.open(filepath) as pdf:
        for i in range(min(3, len(pdf.pages))):
            print(f"\n--- PAGE {i+1} TEXT ---")
            text = pdf.pages[i].extract_text()
            print(text)
            print(f"\n--- PAGE {i+1} TABLES ---")
            tables = pdf.pages[i].extract_tables()
            if tables:
                for j, table in enumerate(tables):
                    print(f"Table {j}:")
                    for row in table:
                        print(row)
            else:
                print("No tables found.")
except Exception as e:
    print(f"Error: {e}")
