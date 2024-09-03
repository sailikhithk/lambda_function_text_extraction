import pytest
from unittest.mock import patch, mock_open
from src.template_matching import load_template, match_template, find_matching_value, find_matching_table

@pytest.fixture
def sample_template():
    return {
        "Name": "string",
        "Age": "int",
        "Employment": {
            "TableName": "EmploymentHistory",
            "Columns": ["Company", "Position", "Years"]
        }
    }

@pytest.fixture
def sample_processed_kv():
    return {
        "Name": "John Doe",
        "Age": "30",
        "Occupation": "Engineer"
    }

@pytest.fixture
def sample_parsed_tables():
    return [
        [
            ["Company", "Position", "Years"],
            ["TechCorp", "Engineer", "5"],
            ["DataInc", "Analyst", "3"]
        ]
    ]

def test_load_template():
    mock_json = '{"Name": "string", "Age": "int"}'
    with patch("builtins.open", mock_open(read_data=mock_json)):
        template = load_template()
    assert template == {"Name": "string", "Age": "int"}

def test_match_template(sample_template, sample_processed_kv, sample_parsed_tables):
    matched_kv, matched_tables = match_template(sample_processed_kv, sample_parsed_tables, sample_template)
    assert matched_kv == {"Name": "John Doe", "Age": "30"}
    assert matched_tables == {
        "Employment": [
            ["Company", "Position", "Years"],
            ["TechCorp", "Engineer", "5"],
            ["DataInc", "Analyst", "3"]
        ]
    }

def test_find_matching_value():
    kv_pairs = {"Full Name": "John Doe", "User Age": "30"}
    assert find_matching_value(kv_pairs, "Name") == "John Doe"
    assert find_matching_value(kv_pairs, "Age") == "30"
    assert find_matching_value(kv_pairs, "Address") == "NO_EXTRACTED_VALUE_KEY"

def test_find_matching_table():
    tables = [
        [["Name", "Age"], ["John", "30"]],
        [["Company", "Position", "Years"], ["TechCorp", "Engineer", "5"]]
    ]
    assert find_matching_table(tables, "Employment") == [["Company", "Position", "Years"], ["TechCorp", "Engineer", "5"]]
    assert find_matching_table(tables, "NonExistent") == []