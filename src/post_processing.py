# File: src/post_processing.py

import json
from datetime import datetime

def post_process(matched_data):
    final_json = {}

    for key, value in matched_data.items():
        if isinstance(value, dict):
            final_json[key] = process_section(value)
        elif isinstance(value, list):
            final_json[key] = process_table(value)
        else:
            final_json[key] = process_value(key, value)

    return final_json

def process_section(section):
    processed_section = {}
    for key, value in section.items():
        if isinstance(value, list):
            processed_section[key] = process_table(value)
        else:
            processed_section[key] = process_value(key, value)
    return processed_section

def process_table(table):
    return [item.dict() if hasattr(item, 'dict') else item for item in table]

def process_value(key, value):
    if isinstance(value, str):
        if key.lower().endswith(('date', 'run date')):
            return process_date(value)
        elif 'amount' in key.lower() or key.lower().endswith(('quantity', 'rate', 'value')):
            return process_number(value)
    return value

def process_date(value):
    try:
        return datetime.strptime(value, "%b %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return value

def process_number(value):
    return float_correction(value)

def string_correction(value):
    return value.replace("O", "0").replace("o", "0")

def int_correction(value):
    value = string_correction(value)
    value = value.replace(",", "")
    try:
        return int(float(value))
    except ValueError:
        return value

def float_correction(value):
    if isinstance(value, str):
        value = string_correction(value)
        value = value.replace(",", "")
        value = remove_duplicate_decimals(value)
        
        if value.startswith('$'):
            value = value.replace('$', "").strip()
        
        try:
            return float(value)
        except ValueError:
            return value
    return value

def remove_duplicate_decimals(value):
    parts = value.split('.')
    if len(parts) > 2:
        return f"{parts[0]}.{''.join(parts[1:])}"
    return value