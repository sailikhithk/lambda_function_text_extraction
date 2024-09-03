from src.utils import find_word_boundingbox, find_Key_value_inrange

def process_checkboxes(parsed_kv, response):
    checkbox_groups = {}
    words_to_find = ['Silver', 'Ethane', 'Residue', 'Production', 'Sale', 'Asset', 'Gasoline', 'Gas']

    for word in words_to_find:
        dict_word = find_word_boundingbox(word, response)
        if dict_word:
            top = dict_word[word]['Top']
            left = dict_word[word]['Left']
            height = dict_word[word]['Height']
            
            dict_group = find_Key_value_inrange(response, top, left, height, no_line_below=5, no_line_above=0, right=1, margin=0.02)
            dict_group = {x.rstrip(): v.rstrip() for x, v in dict_group.items()}
            checkbox_groups[word] = dict_group

    # Remove checkbox groups from parsed_kv
    for group in checkbox_groups.values():
        parsed_kv = {k: v for k, v in parsed_kv.items() if k not in group}

    # Process checkbox groups
    check_box_group_final = {}
    for key, group in checkbox_groups.items():
        check_box_group_final[key] = [k for k, v in group.items() if v != '']
        if len(check_box_group_final[key]) == 1:
            check_box_group_final[key] = check_box_group_final[key][0]
        if isinstance(check_box_group_final[key], str) and check_box_group_final[key].endswith(';'):
            check_box_group_final[key] = check_box_group_final[key][:-1]

    # Combine processed checkboxes with other key-value pairs
    return {**parsed_kv, **check_box_group_final}
