import json
import logging
import re
from difflib import SequenceMatcher
import boto3
import os
import watchtower

# Set up CloudWatch logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler())

# Initialize S3 client
s3_client = boto3.client('s3', region_name=os.getenv('REGION_NAME'))
S3_BUCKET = os.getenv('S3_BUCKET')
TEMPLATE_S3_KEY = os.getenv('TEMPLATE_S3_KEY', 'templates/template.json')

def load_template():
    """
    Loads the template from S3 or local file system.
    :return: Loaded template as a dictionary.
    """
    try:
        logger.info(f"Attempting to load template from S3: {S3_BUCKET}/{TEMPLATE_S3_KEY}")
        # Try to load from S3 first
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=TEMPLATE_S3_KEY)
        template_content = response['Body'].read().decode('utf-8')
        logger.info(f"Successfully loaded template from S3: {S3_BUCKET}/{TEMPLATE_S3_KEY}")
        return json.loads(template_content)
    except Exception as e:
        logger.error(f"Error loading template from S3: {e}", exc_info=True)
        try:
            # Try to load from local file system
            local_path = os.path.join(os.path.dirname(__file__), '..', TEMPLATE_S3_KEY)
            logger.info(f"Attempting to load template from local file: {local_path}")
            with open(local_path, 'r') as file:
                template_content = file.read()
            logger.info(f"Successfully loaded template from local file: {local_path}")
            return json.loads(template_content)
        except Exception as e:
            logger.warning(f"Failed to load template from local file: {e}", exc_info=True)
            # Use a default template structure
            logger.info("Using default template structure")
            return {
                "Statement": {},
                "Physical Information": {},
                "Analysis": {},
                "Fees": {},
                "Settlement Information": {},
                "Total Producer Payment": "float_dollar",
                "Contact Information": {}
            }

def clean_key(key):
    """
    Cleans a key string by removing non-alphanumeric characters and converting to lower case.
    :param key: Key string to clean.
    :return: Cleaned key string.
    """
    clean_key = re.sub(r'[^a-zA-Z0-9\s]', '', key).lower().strip()
    logger.debug(f"Cleaned key: '{key}' -> '{clean_key}'")
    return clean_key

def match_template(processed_kv, parsed_tables):
    """
    Matches the processed key-value pairs and tables against the template.
    :param processed_kv: Dictionary of processed key-value pairs.
    :param parsed_tables: List of parsed tables.
    :return: Matched data as a dictionary.
    """
    logger.info("Starting template matching process")
    template = load_template()
    if not template:
        logger.error("No template loaded. Exiting the matching process.")
        return {}

    matched_data = {}
    try:
        for section, section_template in template.items():
            logger.info(f"Matching section: {section}")
            if isinstance(section_template, dict):
                matched_data[section] = match_section(processed_kv, parsed_tables, section_template)
            else:
                matched_value = find_matching_value(processed_kv, section)
                if matched_value is not None:
                    matched_data[section] = convert_value(matched_value, section_template)
                    logger.info(f"Matched and converted value for section '{section}': {matched_value}")
        logger.info("Template matching completed successfully.")
    except Exception as e:
        logger.error(f"Error during template matching: {e}", exc_info=True)

    logger.debug(f"Matched data: {matched_data}")
    return matched_data

def match_section(processed_kv, parsed_tables, section_template):
    """
    Matches a section of the template with key-value pairs and tables.
    :param processed_kv: Dictionary of processed key-value pairs.
    :param parsed_tables: List of parsed tables.
    :param section_template: Template section to match.
    :return: Matched section data as a dictionary.
    """
    logger.info(f"Matching section template: {section_template}")
    section_data = {}
    try:
        for key, value_type in section_template.items():
            logger.info(f"Matching key: '{key}' with value type: '{value_type}'")
            if isinstance(value_type, dict) and 'TableName' in value_type:
                matched_table = find_matching_table(parsed_tables, value_type['TableName'])
                if matched_table:
                    section_data[key] = matched_table
                    logger.info(f"Matched table for key '{key}' with template table name '{value_type['TableName']}'.")
            else:
                matched_value = find_matching_value(processed_kv, key)
                if matched_value is not None:
                    section_data[key] = convert_value(matched_value, value_type)
                    logger.info(f"Matched value for key '{key}': {matched_value}")
    except Exception as e:
        logger.error(f"Error matching section '{section_template}': {e}", exc_info=True)

    return section_data

def find_matching_value(kv_pairs, template_key):
    """
    Finds the best matching value for a given template key from the provided key-value pairs.
    :param kv_pairs: Dictionary of key-value pairs extracted from the document.
    :param template_key: The key from the template for which we need to find a matching value.
    :return: The best matching value or None if no suitable match is found.
    """
    logger.info(f"Finding matching value for template key: '{template_key}'")
    best_match = None
    best_ratio = 0
    clean_template_key = clean_key(template_key)

    try:
        # Iterate over all key-value pairs to find the best match
        for key, value in kv_pairs.items():
            clean_key_name = clean_key(key)
            ratio = SequenceMatcher(None, clean_template_key, clean_key_name).ratio()
            logger.debug(f"Comparing '{clean_template_key}' with '{clean_key_name}' - Similarity Ratio: {ratio}")

            # Update the best match if the current ratio is the highest
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = value
                logger.debug(f"New best match found: '{clean_key_name}' with ratio {ratio} for key '{template_key}'")

        # Apply thresholds to determine if the match is strong enough
        if best_ratio > 0.7 or (template_key == "Total Producer Payment" and best_ratio > 0.5):
            logger.info(f"Best match for '{template_key}' found with ratio {best_ratio}. Matched value: {best_match}")
            return best_match
        else:
            logger.info(f"No suitable match found for '{template_key}' (Best ratio: {best_ratio}). Returning None.")
            return None

    except Exception as e:
        logger.error(f"Error finding matching value for '{template_key}': {e}", exc_info=True)
        return None
def find_matching_table(tables, table_name):
    """
    Finds the best matching table from the provided tables based on the given table name.
    :param tables: List of tables extracted from the document.
    :param table_name: The name of the table as specified in the template.
    :return: The best matching table or None if no suitable match is found.
    """
    logger.info(f"Finding matching table for template table name: '{table_name}'")

    try:
        for table in tables:
            # Check if the table structure is as expected (list of lists)
            if table and isinstance(table, list) and len(table) > 0:
                if isinstance(table[0], list) and len(table[0]) > 0:
                    first_cell = table[0][0] if table[0][0] else ''
                    ratio = SequenceMatcher(None, table_name.lower(), first_cell.lower()).ratio()
                    logger.debug(f"Comparing table name '{table_name}' with first cell '{first_cell}' - Similarity Ratio: {ratio}")

                    # Consider a match if the similarity ratio is above the threshold
                    if ratio > 0.8:
                        logger.info(f"Matched table for '{table_name}' with ratio {ratio}. Table found with {len(table)} rows.")
                        return table
                else:
                    logger.warning(f"Unexpected table structure for '{table_name}': {table}")
    except Exception as e:
        logger.error(f"Error finding matching table for '{table_name}': {e}", exc_info=True)

    logger.info(f"No suitable table match found for '{table_name}'.")
    return None

def convert_value(value, value_type):
    """
    Converts a value to the specified type as defined in the template.
    :param value: The value to convert.
    :param value_type: The target type as defined in the template (e.g., 'float', 'int', 'date').
    :return: The converted value, or the original value if conversion fails.
    """
    logger.info(f"Converting value '{value}' to type '{value_type}'")

    try:
        if value_type == 'float_dollar':
            # Convert dollar values to float
            converted_value = float(re.sub(r'[^\d.-]', '', value))
        elif value_type == 'float':
            # Convert to float, handling commas
            converted_value = float(value.replace(',', ''))
        elif value_type == 'int':
            # Convert to integer, handling commas
            converted_value = int(value.replace(',', ''))
        elif value_type == 'float_percentage':
            # Convert percentage to a decimal float
            converted_value = float(value.rstrip('%')) / 100
        elif value_type == 'date':
            # Return date as-is; assume further formatting elsewhere if needed
            converted_value = value
        else:
            # Default: return the value as is
            converted_value = value
        
        logger.debug(f"Converted value '{value}' to '{converted_value}' as type {value_type}.")
        return converted_value

    except ValueError as e:
        logger.error(f"Error converting value '{value}' to {value_type}: {e}", exc_info=True)


def log_matching_results(matched_data):
    """
    Logs the matched key-value pairs and tables from the matched data.
    :param matched_data: The dictionary containing matched data.
    """
    try:
        logger.info("Logging matched key-value pairs and tables:")
        for key, value in matched_data.items():
            if isinstance(value, dict):
                logger.info(f"Section: {key}")
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, list):
                        logger.info(f"  {sub_key}: [Table with {len(sub_value)} rows]")
                    else:
                        logger.info(f"  {sub_key}: {sub_value}")
            else:
                logger.info(f"{key}: {value}")
    except Exception as e:
        logger.error(f"Error logging matching results: {e}")

# Log a message when the module is loaded
logger.info("Template matching module loaded successfully")
