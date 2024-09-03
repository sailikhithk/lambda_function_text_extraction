import pytest
from unittest.mock import patch, Mock
from src.document_preparation import prepare_document

@pytest.fixture
def mock_pdf2jpg():
    with patch('src.document_preparation.pdf2jpg') as mock:
        yield mock

@pytest.fixture
def mock_os():
    with patch('src.document_preparation.os') as mock:
        mock.path.splitext.return_value = ('sample', '.pdf')
        mock.path.join.return_value = '/tmp/pdf_pages'
        mock.walk.return_value = [('/tmp/pdf_pages', [], ['page1.jpg', 'page2.jpg'])]
        mock.listdir.return_value = ['page1.jpg', 'page2.jpg']
        yield mock

def test_prepare_document(mock_pdf2jpg, mock_os):
    mock_pdf2jpg.convert_pdf2jpg.return_value = True
    
    result = prepare_document('sample.pdf')
    
    assert len(result) == 2
    assert result == ['/tmp/pdf_pages/page1.jpg', '/tmp/pdf_pages/page2.jpg']
    mock_pdf2jpg.convert_pdf2jpg.assert_called_once()
    mock_os.makedirs.assert_called_once()

def test_prepare_document_error(mock_pdf2jpg, mock_os):
    mock_pdf2jpg.convert_pdf2jpg.side_effect = Exception("PDF conversion failed")
    
    result = prepare_document('sample.pdf')
    
    assert result == []
    mock_pdf2jpg.convert_pdf2jpg.assert_called_once()
    mock_os.makedirs.assert_called_once()