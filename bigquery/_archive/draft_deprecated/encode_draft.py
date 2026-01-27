echo import pandas as pd > check_encoding.py
echo import chardet >> check_encoding.py
echo. >> check_encoding.py
echo def detect_encoding(file_path): >> check_encoding.py
echo     with open(file_path, 'rb') as f: >> check_encoding.py
echo         result = chardet.detect(f.read()) >> check_encoding.py
echo     return result >> check_encoding.py
echo. >> check_encoding.py
echo print("Checking Canadian file...") >> check_encoding.py
echo canadian_enc = detect_encoding('canadian_drafts_master_consolidated.csv') >> check_encoding.py
echo print("Canadian encoding:", canadian_enc) >> check_encoding.py
echo. >> check_encoding.py
echo print("Checking USHL file...") >> check_encoding.py
echo ushl_enc = detect_encoding('ushl_master_consolidated.csv') >> check_encoding.py
echo print("USHL encoding:", ushl_enc) >> check_encoding.py