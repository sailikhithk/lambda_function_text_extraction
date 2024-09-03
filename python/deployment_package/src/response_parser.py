from src.utils import get_text, find_value_block

def form_kv_from_JSON(response):
    blocks = response['Blocks']
    key_map, value_map, block_map = {}, {}, {}

    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        if block['BlockType'] == "KEY_VALUE_SET":
            if 'KEY' in block['EntityTypes']:
                key_map[block_id] = block
            else:
                value_map[block_id] = block

    kvs = {}
    for block_id, key_block in key_map.items():
        value_block = find_value_block(key_block, value_map)
        key = get_text(key_block, block_map)
        val = get_text(value_block, block_map)
        kvs[key] = val

    return kvs

def get_tables_fromJSON(response):
    blocks = response['Blocks']
    blocks_map = {}
    table_blocks = []

    for block in blocks:
        blocks_map[block['Id']] = block
        if block['BlockType'] == "TABLE":
            table_blocks.append(block)

    if len(table_blocks) <= 0:
        print("<b> NO Table FOUND </b>")

    all_tables = []
    for table_result in table_blocks:
        table_matrix = []
        rows = get_rows_columns_map(table_result, blocks_map)
        for row_index, cols in rows.items():
            this_row = []
            for col_index, text in cols.items():
                this_row.append(text)
            table_matrix.append(this_row)
        all_tables.append(table_matrix)

    return all_tables

def get_rows_columns_map(table_result, blocks_map):
    rows = {}
    for relationship in table_result['Relationships']:
        if relationship['Type'] == 'CHILD':
            for child_id in relationship['Ids']:
                cell = blocks_map[child_id]
                if cell['BlockType'] == 'CELL':
                    row_index = cell['RowIndex']
                    col_index = cell['ColumnIndex']
                    if row_index not in rows:
                        rows[row_index] = {}
                    rows[row_index][col_index] = get_text(cell, blocks_map)
    return rows

def parse_response(response):
    kv_pairs = form_kv_from_JSON(response)
    tables = get_tables_fromJSON(response)
    return kv_pairs, tables
