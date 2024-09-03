import logging
import watchtower
import os
from src.utils import find_word_boundingbox, find_Key_value_inrange

# Set up CloudWatch logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler())

def process_checkboxes(parsed_kv, response):
    """
    Processes checkboxes from the parsed key-value pairs and Textract response data.
    :param parsed_kv: Dictionary of parsed key-value pairs
    :param response: Textract response containing the document data
    :return: Combined dictionary of processed checkboxes and remaining key-value pairs
    """
    logger.info("Starting checkbox processing")

    # Initialize checkbox groups and words to search
    checkbox_groups = {}
    words_to_find = ['Silver', 'Ethane', 'Residue', 'Production', 'Sale', 'Asset', 'Gasoline', 'Gas']
    logger.info(f"Words to find in document: {words_to_find}")

    # Process each word to find its bounding box and related key-value pairs
    for word in words_to_find:
        logger.info(f"Searching for bounding box of word: '{word}'")
        dict_word = find_word_boundingbox(word, response)
        if dict_word:
            top = dict_word[word]['Top']
            left = dict_word[word]['Left']
            height = dict_word[word]['Height']
            logger.info(f"Found bounding box for '{word}': Top={top}, Left={left}, Height={height}")

            dict_group = find_Key_value_inrange(
                response, top, left, height, no_line_below=5, no_line_above=0, right=1, margin=0.02
            )
            dict_group = {x.rstrip(): v.rstrip() for x, v in dict_group.items()}
            checkbox_groups[word] = dict_group
            logger.debug(f"Checkbox group for '{word}': {dict_group}")
        else:
            logger.warning(f"No bounding box found for word: '{word}'")

    # Remove checkbox groups from parsed key-value pairs
    original_kv_count = len(parsed_kv)
    for group in checkbox_groups.values():
        parsed_kv = {k: v for k, v in parsed_kv.items() if k not in group}
    logger.info(f"Removed checkbox groups from parsed key-value pairs. Original count: {original_kv_count}, New count: {len(parsed_kv)}")

    # Process checkbox groups to extract final values
    check_box_group_final = {}
    for key, group in checkbox_groups.items():
        logger.info(f"Processing checkbox group for '{key}'")
        check_box_group_final[key] = [k for k, v in group.items() if v != '']
        if len(check_box_group_final[key]) == 1:
            check_box_group_final[key] = check_box_group_final[key][0]
        if isinstance(check_box_group_final[key], str) and check_box_group_final[key].endswith(';'):
            check_box_group_final[key] = check_box_group_final[key][:-1]
        logger.debug(f"Processed checkbox group '{key}': {check_box_group_final[key]}")

    # Combine processed checkboxes with remaining key-value pairs
    result = {**parsed_kv, **check_box_group_final}
    logger.info(f"Checkbox processing completed. Final processed result: {result}")

    return result

# Log a message when the module is loaded
logger.info("Document-specific processing module loaded successfully")
