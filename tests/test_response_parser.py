import pytest
from src.response_parser import form_kv_from_JSON, get_tables_fromJSON, parse_response

@pytest.fixture
def sample_response():
    return {
        'Blocks': [
            {'Id': '1', 'BlockType': 'KEY_VALUE_SET', 'EntityTypes': ['KEY']},
            {'Id': '2', 'BlockType': 'KEY_VALUE_SET', 'EntityTypes': ['VALUE']},
            {'Id': '3', 'BlockType': 'WORD', 'Text': 'Name'},
            {'Id': '4', 'BlockType': 'WORD', 'Text': 'John'},
            {'Id': '5', 'BlockType': 'TABLE'},
            {'Id': '6', 'BlockType': 'CELL', 'RowIndex': 1, 'ColumnIndex': 1, 'Text': 'Header'},
            {'Id': '7', 'BlockType': 'CELL', 'RowIndex': 2, 'ColumnIndex': 1, 'Text': 'Data'},
        ],
        'Relationships': [
            {'Type': 'CHILD', 'Ids': ['3']},
            {'Type': 'VALUE', 'Ids': ['2']},
            {'Type': 'CHILD', 'Ids': ['4']},
            {'Type': 'CHILD', 'Ids': ['6', '7']},
        ]
    }

def test_form_kv_from_JSON(sample_response):
    result = form_kv_from_JSON(sample_response)
    assert result == {'Name': 'John'}

def test_get_tables_fromJSON(sample_response):
    result = get_tables_fromJSON(sample_response)
    assert result == [[['Header'], ['Data']]]

def test_parse_response(sample_response):
    kv_pairs, tables = parse_response(sample_response)
    assert kv_pairs == {'Name': 'John'}
    assert tables == [[['Header'], ['Data']]]