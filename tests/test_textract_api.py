import pytest
from unittest.mock import patch, Mock
from botocore.exceptions import ClientError
from src.textract_api import analyze_document

@pytest.fixture
def mock_boto3():
    with patch('src.textract_api.boto3') as mock:
        yield mock

def test_analyze_document_success(mock_boto3):
    mock_client = Mock()
    mock_boto3.client.return_value = mock_client
    mock_client.analyze_document.return_value = {'MockResponse': 'Success'}

    result = analyze_document('test.jpg', 'test-bucket')

    assert result == {'MockResponse': 'Success'}
    mock_client.analyze_document.assert_called_once_with(
        Document={'S3Object': {'Bucket': 'test-bucket', 'Name': 'test.jpg'}},
        FeatureTypes=["TABLES", "FORMS"]
    )

def test_analyze_document_client_error(mock_boto3):
    mock_client = Mock()
    mock_boto3.client.return_value = mock_client
    mock_client.analyze_document.side_effect = ClientError(
        {'Error': {'Code': 'TestException', 'Message': 'Test error message'}},
        'analyze_document'
    )

    result = analyze_document('test.jpg', 'test-bucket')

    assert result is None
    mock_client.analyze_document.assert_called_once()