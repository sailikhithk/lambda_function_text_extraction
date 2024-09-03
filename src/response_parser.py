import logging
import watchtower
from src.utils import get_text, find_value_block

# Set up CloudWatch logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler())

def form_kv_from_JSON(response):
    """
    Extracts key-value pairs from the Textract JSON response.
    :param response: Textract JSON response.
    :return: Dictionary of key-value pairs.
    """
    logger.info("Starting extraction of key-value pairs from JSON response")
    blocks = response.get('Blocks', [])
    key_map, value_map, block_map = {}, {}, {}

    # Map blocks by ID and categorize as key or value blocks
    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        if block['BlockType'] == "KEY_VALUE_SET":
            if 'KEY' in block['EntityTypes']:
                key_map[block_id] = block
                logger.debug(f"Found key block: {block_id}")
            else:
                value_map[block_id] = block
                logger.debug(f"Found value block: {block_id}")

    kvs = {}
    # Match key blocks to value blocks
    for block_id, key_block in key_map.items():
        value_block = find_value_block(key_block, value_map)
        key = get_text(key_block, block_map)
        val = get_text(value_block, block_map)
        kvs[key] = val
        logger.debug(f"Extracted key-value pair: {key} -> {val}")

    logger.info(f"Completed extraction of key-value pairs. Total pairs found: {len(kvs)}")
    return kvs

def get_tables_fromJSON(response):
    """
    Extracts tables from the Textract JSON response.
    :param response: Textract JSON response.
    :return: List of tables, each table represented as a matrix of text values.
    """
    logger.info("Starting extraction of tables from JSON response")
    blocks = response.get('Blocks', [])
    blocks_map = {}
    table_blocks = []

    # Map blocks and identify table blocks
    for block in blocks:
        blocks_map[block['Id']] = block
        if block['BlockType'] == "TABLE":
            table_blocks.append(block)
            logger.debug(f"Found table block: {block['Id']}")

    if not table_blocks:
        logger.warning("No tables found in the document")

    all_tables = []
    # Process each table block
    for table_result in table_blocks:
        table_matrix = []
        rows = get_rows_columns_map(table_result, blocks_map)
        for row_index, cols in rows.items():
            this_row = [text for col_index, text in sorted(cols.items())]
            table_matrix.append(this_row)
        all_tables.append(table_matrix)
        logger.debug(f"Extracted table: {table_matrix}")

    logger.info(f"Completed extraction of tables. Total tables found: {len(all_tables)}")
    return all_tables

def get_rows_columns_map(table_result, blocks_map):
    """
    Maps rows and columns of a table from Textract response.
    :param table_result: Table block from Textract response.
    :param blocks_map: Dictionary of blocks mapped by ID.
    :return: Dictionary mapping row indices to columns of text values.
    """
    logger.info(f"Mapping rows and columns for table block: {table_result['Id']}")
    rows = {}
    # Iterate over relationships to map cells to rows and columns
    for relationship in table_result.get('Relationships', []):
        if relationship['Type'] == 'CHILD':
            for child_id in relationship['Ids']:
                cell = blocks_map.get(child_id)
                if cell and cell['BlockType'] == 'CELL':
                    row_index = cell['RowIndex']
                    col_index = cell['ColumnIndex']
                    if row_index not in rows:
                        rows[row_index] = {}
                    rows[row_index][col_index] = get_text(cell, blocks_map)
                    logger.debug(f"Mapped cell ({row_index}, {col_index}): {rows[row_index][col_index]}")

    logger.info(f"Completed mapping of rows and columns for table block: {table_result['Id']}")
    return rows

def parse_response(response):
    """
    Parses the Textract JSON response to extract key-value pairs and tables.
    :param response: Textract JSON response.
    :return: Tuple containing dictionary of key-value pairs and list of tables.
    """
    logger.info("Starting parsing of Textract response")
    kv_pairs = form_kv_from_JSON(response)
    tables = get_tables_fromJSON(response)
    logger.info(f"Parsing completed. Extracted {len(kv_pairs)} key-value pairs and {len(tables)} tables.")
    return kv_pairs, tables

# Log a message when the module is loaded
logger.info("Response parser module loaded successfully")
