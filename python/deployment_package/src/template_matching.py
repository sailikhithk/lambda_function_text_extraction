import json
import logging
import re
from difflib import SequenceMatcher

# Corrected logging configuration to use /tmp directory
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/tmp/template_matching.log"),  # Updated path to use /tmp
        logging.StreamHandler()
    ]
)

def load_template():
    try:
        with open('templates/template.json', 'r') as json_file:
            logging.info("Loading template from 'templates/template.json'.")
            return json.load(json_file)
    except FileNotFoundError:
        logging.error("Template file not found. Ensure 'templates/template.json' exists.")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON template: {e}")
        return {}

def clean_key(key):
    clean_key = re.sub(r'[^a-zA-Z0-9\s]', '', key).lower().strip()
    logging.debug(f"Cleaned key: '{key}' -> '{clean_key}'")
    return clean_key

def match_template(processed_kv, parsed_tables):
    template = load_template()
    if not template:
        logging.error("No template loaded. Exiting the matching process.")
        return {}

    matched_data = {}
    try:
        for section, section_template in template.items():
            if isinstance(section_template, dict):
                matched_data[section] = match_section(processed_kv, parsed_tables, section_template)
            else:
                matched_value = find_matching_value(processed_kv, section)
                if matched_value is not None:
                    matched_data[section] = convert_value(matched_value, section_template)
        logging.info("Template matching completed successfully.")
    except Exception as e:
        logging.error(f"Error during template matching: {e}")

    return matched_data

def match_section(processed_kv, parsed_tables, section_template):
    section_data = {}
    try:
        for key, value_type in section_template.items():
            if isinstance(value_type, dict) and 'TableName' in value_type:
                matched_table = find_matching_table(parsed_tables, value_type['TableName'])
                if matched_table:
                    section_data[key] = matched_table
                    logging.info(f"Matched table for '{key}' with template table name '{value_type['TableName']}'.")
            else:
                matched_value = find_matching_value(processed_kv, key)
                if matched_value is not None:
                    section_data[key] = convert_value(matched_value, value_type)
                    logging.info(f"Matched value for '{key}': {matched_value}")
    except Exception as e:
        logging.error(f"Error matching section '{section_template}': {e}")

    return section_data

def find_matching_value(kv_pairs, template_key):
    best_match = None
    best_ratio = 0
    clean_template_key = clean_key(template_key)

    try:
        for key, value in kv_pairs.items():
            clean_key_name = clean_key(key)
            ratio = SequenceMatcher(None, clean_template_key, clean_key_name).ratio()
            logging.debug(f"Comparing '{clean_template_key}' with '{clean_key_name}' - Ratio: {ratio}")
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = value

        # Lowered the threshold and added special case for Total Producer Payment
        if best_ratio > 0.7 or (template_key == "Total Producer Payment" and best_ratio > 0.5):
            logging.info(f"Best match for '{template_key}' found with ratio {best_ratio}.")
            return best_match
        else:
            logging.info(f"No suitable match found for '{template_key}' (Best ratio: {best_ratio}).")
            return None
    except Exception as e:
        logging.error(f"Error finding matching value for '{template_key}': {e}")
        return None

def find_matching_table(tables, table_name):
    try:
        for table in tables:
            if table and len(table) > 0 and isinstance(table[0], list):
                first_cell = table[0][0] if table[0] else ''
                ratio = SequenceMatcher(None, table_name.lower(), first_cell.lower()).ratio()
                logging.debug(f"Comparing table name '{table_name}' with '{first_cell}' - Ratio: {ratio}")
                if ratio > 0.8:
                    logging.info(f"Matched table for '{table_name}' with ratio {ratio}.")
                    return table
    except Exception as e:
        logging.error(f"Error finding matching table for '{table_name}': {e}")

    logging.info(f"No suitable table match found for '{table_name}'.")
    return None

def convert_value(value, value_type):
    try:
        if value_type == 'float_dollar':
            converted_value = float(re.sub(r'[^\d.-]', '', value))
        elif value_type == 'float':
            converted_value = float(value.replace(',', ''))
        elif value_type == 'int':
            converted_value = int(value.replace(',', ''))
        elif value_type == 'float_percentage':
            converted_value = float(value.rstrip('%')) / 100
        elif value_type == 'date':
            # Implement date parsing logic here if needed
            converted_value = value
        else:
            converted_value = value
        logging.debug(f"Converted value '{value}' to '{converted_value}' as {value_type}.")
        return converted_value
    except ValueError as e:
        logging.error(f"Error converting value '{value}' to {value_type}: {e}")
        return value

def log_matching_results(matched_data):
    try:
        logging.info("Matched key-value pairs:")
        for key, value in matched_data.items():
            if isinstance(value, dict):
                logging.info(f"{key}:")
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, list):
                        logging.info(f"  {sub_key}: [table with {len(sub_value)} rows]")
                    else:
                        logging.info(f"  {sub_key}: {sub_value}")
            else:
                logging.info(f"{key}: {value}")
    except Exception as e:
        logging.error(f"Error logging matching results: {e}")