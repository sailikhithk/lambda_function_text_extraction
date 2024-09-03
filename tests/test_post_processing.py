import pytest
from src.post_processing import post_process, process_value, process_date, process_number, string_correction, int_correction, float_correction, remove_duplicate_decimals

def test_post_process():
    matched_kv = {
        "Name": "John Doe",
        "Age": "30",
        "Hire Date": "2023-01-15",
        "Salary": "$75,000.00"
    }
    matched_tables = {
        "Employment": [
            ["Company", "Position", "Years"],
            ["TechCorp", "Engineer", "5"],
            ["DataInc", "Analyst", "3"]
        ]
    }
    result = post_process(matched_kv, matched_tables)
    assert result == {
        "Name": "John Doe",
        "Age": 30,
        "Hire Date": "2023-01-15",
        "Salary": 75000.0,
        "Employment": [
            ["Company", "Position", "Years"],
            ["TechCorp", "Engineer", "5"],
            ["DataInc", "Analyst", "3"]
        ]
    }

def test_process_value():
    assert process_value("hire date", "2023-01-15") == "2023-01-15"
    assert process_value("salary", "$75,000.00") == 75000.0
    assert process_value("name", "John Doe") == "John Doe"

def test_process_date():
    assert process_date("2023-01-15") == "2023-01-15"
    assert process_date("01/15/2023") == "01/15/2023"

def test_process_number():
    assert process_number("75,000.00") == 75000.00
    assert process_number("1,234,567") == 1234567.0
    assert process_number("invalid") == "invalid"

def test_string_correction():
    assert string_correction("1O0o") == "1000"
    assert string_correction("Hello W0rld") == "Hello W0rld"

def test_int_correction():
    assert int_correction("1,234") == 1234
    assert int_correction("1O0o") == 1000
    assert int_correction("invalid") == "invalid"

def test_float_correction():
    assert float_correction("1,234.56") == 1234.56
    assert float_correction("$1,234.56") == 1234.56
    assert float_correction("1.2.3.4") == 1.234
    assert float_correction("invalid") == "invalid"

def test_remove_duplicate_decimals():
    assert remove_duplicate_decimals("1.2.3.4") == "1.234"
    assert remove_duplicate_decimals("1.23") == "1.23"
    assert remove_duplicate_decimals("1..2..3") == "1.23"