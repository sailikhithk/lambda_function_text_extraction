def get_text(result, blocks_map):
    text = ''
    if 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'WORD':
                        text += word['Text'] + ' '
                    if word['BlockType'] == 'SELECTION_ELEMENT':
                        if word['SelectionStatus'] == 'SELECTED':
                            text += 'X '
    return text.strip()

def find_value_block(key_block, value_map):
    for relationship in key_block['Relationships']:
        if relationship['Type'] == 'VALUE':
            for value_id in relationship['Ids']:
                value_block = value_map[value_id]
                return value_block
    return None

def find_word_boundingbox(findword, response):
    word_find = {}
    for item in response["Blocks"]:
        if item["BlockType"] == "LINE":
            if findword in item["Text"]:
                word_find[findword] = {
                    'Top': item['Geometry']['BoundingBox']['Top'],
                    'Height': item['Geometry']['BoundingBox']['Height'],
                    'Left': item['Geometry']['BoundingBox']['Left'],
                    'Width': item['Geometry']['BoundingBox']['Width']
                }
    return word_find

def find_Key_value_inrange(response, top, left, word_height, no_line_below, no_line_above=0, right=1, margin=0.02):
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
    
    kv_pair = {}
    for block_id, key_block in key_map.items():
        value_block = find_value_block(key_block, value_map)
        if value_block:
            key = get_text(key_block, block_map)
            val = get_text(value_block, block_map)
            vb_top = value_block['Geometry']['BoundingBox']['Top']
            vb_left = value_block['Geometry']['BoundingBox']['Left']
            vb_width = value_block['Geometry']['BoundingBox']['Width']
            
            if (vb_top >= top - no_line_above * word_height - margin * top and
                vb_top <= top + no_line_below * word_height + margin * word_height and
                vb_left >= left - margin * left and
                vb_left + vb_width <= right + margin * right):
                kv_pair[key] = val
    
    return kv_pair
