import json
from datetime import datetime
import logging
import watchtower
import os

# Set up CloudWatch logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler())

def post_process(matched_data):
    """
    Main function to post-process matched data.
    :param matched_data: Dictionary of matched data.
    :return: Processed dictionary of final results.
    """
    logger.info("Starting post-processing of matched data")
    final_json = {}

    for key, value in matched_data.items():
        logger.info(f"Processing key: {key} with value type: {type(value).__name__}")
        if isinstance(value, dict):
            final_json[key] = process_section(value)
            logger.debug(f"Processed section for key: {key} -> {final_json[key]}")
        elif isinstance(value, list):
            final_json[key] = process_table(value)
            logger.debug(f"Processed table for key: {key} -> {final_json[key]}")
        else:
            final_json[key] = process_value(key, value)
            logger.debug(f"Processed value for key: {key} -> {final_json[key]}")

    logger.info("Post-processing completed")
    logger.debug(f"Final processed data: {final_json}")
    return final_json

def process_section(section):
    """
    Processes a section of the data.
    :param section: Dictionary section to be processed.
    :return: Processed section dictionary.
    """
    logger.info(f"Processing section: {section}")
    processed_section = {}
    for key, value in section.items():
        logger.info(f"Processing section key: {key} with value type: {type(value).__name__}")
        if isinstance(value, list):
            processed_section[key] = process_table(value)
            logger.debug(f"Processed table for section key: {key} -> {processed_section[key]}")
        else:
            processed_section[key] = process_value(key, value)
            logger.debug(f"Processed value for section key: {key} -> {processed_section[key]}")
    return processed_section

def process_table(table):
    """
    Processes a table by converting items into dictionaries if needed.
    :param table: List of table items.
    :return: Processed list of table items.
    """
    logger.info(f"Processing table with {len(table)} items")
    processed_table = [item if isinstance(item, dict) else {"value": item} for item in table]
    logger.debug(f"Processed table: {processed_table}")
    return processed_table

def process_value(key, value):
    """
    Processes a single value based on its key.
    :param key: The key associated with the value.
    :param value: The value to process.
    :return: Processed value.
    """
    logger.info(f"Processing value for key: {key}")
    if isinstance(value, str):
        if key.lower().endswith(('date', 'run date')):
            logger.info(f"Processing date value for key: {key}")
            return process_date(value)
        elif 'amount' in key.lower() or key.lower().endswith(('quantity', 'rate', 'value')):
            logger.info(f"Processing numeric value for key: {key}")
            return process_number(value)
    return value

def process_date(value):
    """
    Processes date values by converting them into a standard format.
    :param value: Date string.
    :return: Processed date string in YYYY-MM-DD format.
    """
    logger.info(f"Processing date: {value}")
    try:
        processed_date = datetime.strptime(value, "%b %d, %Y").strftime("%Y-%m-%d")
        logger.info(f"Converted date: {value} to {processed_date}")
        return processed_date
    except ValueError:
        logger.warning(f"Could not parse date: {value}")
        return value

def process_number(value):
    """
    Processes numeric values by converting them into floats.
    :param value: Numeric string.
    :return: Processed float or the original value if conversion fails.
    """
    logger.info(f"Processing number: {value}")
    return float_correction(value)

def string_correction(value):
    """
    Corrects common OCR errors in strings, such as converting 'O' to '0'.
    :param value: The string to correct.
    :return: Corrected string.
    """
    corrected_value = value.replace("O", "0").replace("o", "0")
    logger.debug(f"Corrected string: {value} -> {corrected_value}")
    return corrected_value

def int_correction(value):
    """
    Corrects and converts a string to an integer.
    :param value: The string to convert.
    :return: Converted integer or the original value if conversion fails.
    """
    value = string_correction(value)
    value = value.replace(",", "")
    try:
        corrected_int = int(float(value))
        logger.info(f"Converted value to int: {value} -> {corrected_int}")
        return corrected_int
    except ValueError:
        logger.warning(f"Could not convert to int: {value}")
        return value

def float_correction(value):
    """
    Corrects and converts a string to a float.
    :param value: The string to convert.
    :return: Converted float or the original value if conversion fails.
    """
    if isinstance(value, str):
        value = string_correction(value)
        value = value.replace(",", "")
        value = remove_duplicate_decimals(value)

        if value.startswith('$'):
            value = value.replace('$', "").strip()

        try:
            corrected_float = float(value)
            logger.info(f"Converted value to float: {value} -> {corrected_float}")
            return corrected_float
        except ValueError:
            logger.warning(f"Could not convert to float: {value}")
            return value
    return value

def remove_duplicate_decimals(value):
    """
    Removes duplicate decimal points in a numeric string.
    :param value: The string to process.
    :return: String with duplicate decimals removed.
    """
    parts = value.split('.')
    if len(parts) > 2:
        corrected_value = f"{parts[0]}.{''.join(parts[1:])}"
        logger.warning(f"Removed duplicate decimals: {value} -> {corrected_value}")
        return corrected_value
    return value

# Log a message when the module is loaded
logger.info("Post-processing module loaded successfully")
