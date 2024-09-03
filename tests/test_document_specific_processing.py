import pytest
from unittest.mock import patch
from src.document_specific_processing import process_checkboxes

@pytest.fixture
def sample_parsed_kv():
    return {
        'Name': 'John Doe',
        'Age': '30',
        'Employed': 'Yes'
    }

@pytest.fixture
def sample_response():
    return {
        'Blocks': [
            {'Id': '1', 'BlockType': 'WORD', 'Text': 'Employed', 'Geometry': {'BoundingBox': {'Top': 0.5, 'Left': 0.1, 'Width': 0.2, 'Height': 0.05}}},
            {'Id': '2', 'BlockType': 'SELECTION_ELEMENT', 'SelectionStatus': 'SELECTED', 'Geometry': {'BoundingBox': {'Top': 0.55, 'Left': 0.1, 'Width': 0.05, 'Height': 0.05}}},
        ]
    }

@patch('src.document_specific_processing.find_word_boundingbox')
@patch('src.document_specific_processing.find_Key_value_inrange')
def test_process_checkboxes(mock_find_kv, mock_find_word, sample_parsed_kv, sample_response):
    mock_find_word.return_value = {'Employed': {'Top': 0.5, 'Left': 0.1, 'Height': 0.05, 'Width': 0.2}}
    mock_find_kv.return_value = {'Employed': 'Yes'}

    result = process_checkboxes(sample_parsed_kv, sample_response)

    assert result == {
        'Name': 'John Doe',
        'Age': '30',
        'Employed': 'Yes'
    }
    mock_find_word.assert_called()
    mock_find_kv.assert_called()