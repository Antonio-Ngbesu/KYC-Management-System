"""
More detailed connection string debug
"""
import os
from dotenv import load_dotenv
import re

load_dotenv()

connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
if connection_string:
    print(f"Full length: {len(connection_string)}")
    
    # Extract account key to check its format
    key_match = re.search(r'AccountKey=([^;]+)', connection_string)
    if key_match:
        account_key = key_match.group(1)
        print(f"Account key length: {len(account_key)}")
        print(f"Account key ends with '='?: {account_key.endswith('=')}")
        print(f"Account key sample (first 10 chars): {account_key[:10]}...")
        print(f"Account key sample (last 10 chars): ...{account_key[-10:]}")
    else:
        print("❌ Could not extract AccountKey from connection string")
        
    # Check account name
    name_match = re.search(r'AccountName=([^;]+)', connection_string)
    if name_match:
        account_name = name_match.group(1)
        print(f"Account name: {account_name}")
else:
    print("❌ No connection string found")
