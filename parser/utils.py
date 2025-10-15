import re
import json
import pandas as pd
import pdfplumber
from datetime import datetime

def parse_pdf(file_path):
    data = {
        'card_issuer': '',
        'card_last_4': '',
        'card_variant': '',
        'billing_cycle': '',
        'payment_due_date': '',
        'total_balance': '',
        'transaction_count': 0,
        'transactions': []
    }
    
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ''
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
            
            # Convert to uppercase for easier matching
            text_upper = text.upper()
            
            # Enhanced Card Issuer Detection
            issuers = [
                ('HDFC', ['HDFC', 'HOUSING DEVELOPMENT FINANCE']),
                ('ICICI', ['ICICI', 'ICICI BANK']),
                ('SBI', ['SBI', 'STATE BANK OF INDIA', 'STATE BANK']),
                ('AXIS', ['AXIS', 'AXIS BANK']),
                ('KOTAK', ['KOTAK', 'KOTAK MAHINDRA']),
                ('AMERICAN EXPRESS', ['AMERICAN EXPRESS', 'AMEX']),
                ('CITIBANK', ['CITIBANK', 'CITI BANK', 'CITI']),
                ('STANDARD CHARTERED', ['STANDARD CHARTERED', 'SC BANK']),
                ('YES BANK', ['YES BANK']),
                ('INDUSIND', ['INDUSIND', 'INDUSIND BANK']),
                ('RBL', ['RBL', 'RBL BANK', 'RATNAKAR']),
                ('AU SMALL FINANCE', ['AU SMALL FINANCE', 'AU BANK']),
                ('HSBC', ['HSBC']),
            ]
            
            for issuer_name, keywords in issuers:
                for keyword in keywords:
                    if keyword in text_upper:
                        data['card_issuer'] = issuer_name.title()
                        break
                if data['card_issuer']:
                    break
            
            # Enhanced Card Number Extraction (last 4 digits)
            card_patterns = [
                r'(?:card\s*(?:number|no\.?|#)?[\s:]*)?[\*xX]{12}(\d{4})',  # ************1234
                r'(?:card\s*(?:number|no\.?|#)?[\s:]*)?[\*xX\s]{4}[\*xX\s]{4}[\*xX\s]{4}(\d{4})',  # **** **** **** 1234
                r'(?:card\s*(?:ending|ends)\s*(?:in|with)[\s:]*)?(\d{4})',  # card ending in 1234
                r'(?:a/c|account)[\s:]*[\*xX]*(\d{4})',  # a/c ****1234
                r'xxxx\s*xxxx\s*xxxx\s*(\d{4})',  # xxxx xxxx xxxx 1234
            ]
            
            for pattern in card_patterns:
                card_match = re.search(pattern, text, re.IGNORECASE)
                if card_match:
                    data['card_last_4'] = card_match.group(1)
                    break
            
            # Enhanced Card Variant Detection
            variants = [
                'PLATINUM', 'GOLD', 'SILVER', 'TITANIUM', 'SIGNATURE', 
                'INFINITE', 'PREFERRED', 'CLASSIC', 'PRESTIGE', 'ULTIMATE',
                'REWARDS', 'CASHBACK', 'ELITE', 'PRIME', 'SELECT'
            ]
            for variant in variants:
                if variant in text_upper:
                    data['card_variant'] = variant.title()
                    break
            
            # Enhanced Billing Cycle Detection
            cycle_patterns = [
                r'(?:billing|statement)\s*(?:period|cycle|date)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*(?:to|-)?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:from|period)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*(?:to|-)?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\s*(?:to|-)\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})',  # 01 Sep 2024 to 30 Sep 2024
            ]
            
            for pattern in cycle_patterns:
                cycle_match = re.search(pattern, text, re.IGNORECASE)
                if cycle_match:
                    data['billing_cycle'] = f"{cycle_match.group(1)} to {cycle_match.group(2)}"
                    break
            
            # Enhanced Payment Due Date Detection
            due_patterns = [
                r'(?:payment\s*)?due\s*(?:date|by)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:pay\s*by|payment\s*date)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'due\s*on[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:payment\s*)?due[\s:]*(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})',  # Due: 15 Oct 2024
            ]
            
            for pattern in due_patterns:
                due_match = re.search(pattern, text, re.IGNORECASE)
                if due_match:
                    data['payment_due_date'] = due_match.group(1)
                    break
            
            # Enhanced Total Balance Detection
            balance_patterns = [
                r'(?:total\s*)?(?:amount\s*)?(?:due|payable|outstanding)[\s:]*(?:rs\.?|₹|inr)?\s*([\d,]+\.?\d*)',
                r'(?:total|balance|closing\s*balance)[\s:]*(?:rs\.?|₹|inr)?\s*([\d,]+\.?\d*)',
                r'(?:minimum\s*)?(?:payment\s*)?(?:due|amount)[\s:]*(?:rs\.?|₹|inr)?\s*([\d,]+\.?\d*)',
                r'(?:current\s*)?(?:dues?|outstanding)[\s:]*(?:rs\.?|₹|inr)?\s*([\d,]+\.?\d*)',
            ]
            
            for pattern in balance_patterns:
                balance_match = re.search(pattern, text, re.IGNORECASE)
                if balance_match:
                    amount = balance_match.group(1).replace(',', '')
                    try:
                        if float(amount) > 0:  # Ensure it's a positive number
                            data['total_balance'] = balance_match.group(1)
                            break
                    except:
                        continue
            
            # Transaction Count
            transaction_patterns = [
                r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s+[^\d]+\s*(?:rs\.?|₹|inr)?\s*[\d,]+\.?\d*',
                r'(?:rs\.?|₹|inr)\s*[\d,]+\.?\d*\s+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            ]
            
            transactions = []
            for pattern in transaction_patterns:
                transactions.extend(re.findall(pattern, text, re.IGNORECASE))
            
            data['transaction_count'] = len(set(transactions))  # Remove duplicates
            
            # If no data found, add debug info
            if not any([data['card_issuer'], data['card_last_4'], data['card_variant']]):
                print(f"DEBUG: No data extracted from PDF. First 500 chars:")
                print(text[:500] if text else "No text extracted")
            
    except Exception as e:
        print(f"PDF parsing error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return data


def parse_csv(file_path):
    data = {
        'card_issuer': '',
        'card_last_4': '',
        'card_variant': '',
        'billing_cycle': '',
        'payment_due_date': '',
        'total_balance': '',
        'transaction_count': 0,
        'transactions': []
    }
    
    try:
        df = pd.read_csv(file_path)
        
        # Normalize column names - remove spaces and convert to lowercase
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Possible column name variations
        column_mappings = {
            'card_issuer': ['card_issuer', 'issuer', 'bank', 'bank_name', 'card_bank'],
            'card_number': ['card_number', 'card', 'card_no', 'account_number', 'account'],
            'card_variant': ['variant', 'card_type', 'card_variant', 'type', 'card_category'],
            'billing_cycle': ['billing_cycle', 'cycle', 'statement_period', 'period'],
            'due_date': ['due_date', 'payment_due_date', 'payment_date', 'due'],
            'balance': ['balance', 'total_balance', 'amount', 'amount_due', 'total_amount', 'outstanding']
        }
        
        # Extract data based on column mappings
        for field, possible_cols in column_mappings.items():
            for col in possible_cols:
                if col in df.columns and not df[col].empty:
                    if field == 'card_number':
                        card_num = str(df[col].iloc[0])
                        data['card_last_4'] = card_num[-4:] if len(card_num) >= 4 else card_num
                    elif field == 'card_issuer':
                        data['card_issuer'] = str(df[col].iloc[0])
                    elif field == 'card_variant':
                        data['card_variant'] = str(df[col].iloc[0])
                    elif field == 'billing_cycle':
                        data['billing_cycle'] = str(df[col].iloc[0])
                    elif field == 'due_date':
                        data['payment_due_date'] = str(df[col].iloc[0])
                    elif field == 'balance':
                        data['total_balance'] = str(df[col].iloc[0])
                    break
        
        data['transaction_count'] = len(df)
        
    except Exception as e:
        print(f"CSV parsing error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return data


def parse_json(file_path):
    data = {
        'card_issuer': '',
        'card_last_4': '',
        'card_variant': '',
        'billing_cycle': '',
        'payment_due_date': '',
        'total_balance': '',
        'transaction_count': 0,
        'transactions': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Handle both single object and array formats
        if isinstance(json_data, list) and len(json_data) > 0:
            json_data = json_data[0]
        
        # Create case-insensitive key mapping
        keys_lower = {k.lower().replace(' ', '_'): k for k in json_data.keys()}
        
        # Possible field name variations
        field_mappings = {
            'card_issuer': ['card_issuer', 'issuer', 'bank', 'bank_name', 'cardissuer'],
            'card_number': ['card_number', 'card', 'cardnumber', 'card_no', 'account_number'],
            'card_variant': ['variant', 'card_type', 'card_variant', 'cardvariant', 'type'],
            'billing_cycle': ['billing_cycle', 'cycle', 'billingcycle', 'statement_period'],
            'due_date': ['due_date', 'payment_due_date', 'duedate', 'payment_date'],
            'balance': ['balance', 'total_balance', 'totalbalance', 'amount', 'amount_due']
        }
        
        # Extract data
        for field, possible_keys in field_mappings.items():
            for key in possible_keys:
                if key in keys_lower:
                    actual_key = keys_lower[key]
                    if field == 'card_number':
                        card_num = str(json_data[actual_key])
                        data['card_last_4'] = card_num[-4:] if len(card_num) >= 4 else card_num
                    elif field == 'card_issuer':
                        data['card_issuer'] = str(json_data[actual_key])
                    elif field == 'card_variant':
                        data['card_variant'] = str(json_data[actual_key])
                    elif field == 'billing_cycle':
                        data['billing_cycle'] = str(json_data[actual_key])
                    elif field == 'due_date':
                        data['payment_due_date'] = str(json_data[actual_key])
                    elif field == 'balance':
                        data['total_balance'] = str(json_data[actual_key])
                    break
        
        # Count transactions if available
        for key in ['transactions', 'transaction', 'txns', 'txn_list']:
            if key in keys_lower:
                transactions = json_data[keys_lower[key]]
                data['transaction_count'] = len(transactions) if isinstance(transactions, list) else 0
                break
        
    except Exception as e:
        print(f"JSON parsing error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return data