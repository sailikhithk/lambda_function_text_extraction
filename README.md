# Textract Document Extraction

This project automates the extraction of information from gas statement PDFs using Amazon Textract. It processes PDF documents, extracts key-value pairs and tables, and applies custom processing and template matching to produce structured output.

## Features

- PDF to JPG conversion
- Automated upload to Amazon S3
- Document analysis using Amazon Textract
- Custom document-specific processing
- Template matching for standardized output
- Multiprocessing for improved performance

## Prerequisites

- Python 3.7+
- AWS account with Textract access
- Boto3
- Other dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/textract-document-extraction.git
   cd textract-document-extraction
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up your AWS credentials:
   - Create a `.env` file in the project root
   - Add your AWS credentials and configuration:
     ```
     AWS_ACCESS_KEY_ID=your_access_key
     AWS_SECRET_ACCESS_KEY=your_secret_key
     REGION_NAME=your_aws_region
     BUCKET=your_s3_bucket_name
     ```

## Usage

Run the main script with a PDF file as an argument:

```
python main.py path/to/your/document.pdf
```

To save the output to a file:

```
python main.py path/to/your/document.pdf --output results.json
```

## Project Structure

```
textract_document_extraction/
├── main.py
├── requirements.txt
├── config.py
├── README.md
├── src/
│   ├── __init__.py
│   ├── document_preparation.py
│   ├── textract_api.py
│   ├── response_parser.py
│   ├── document_specific_processing.py
│   ├── template_matching.py
│   ├── post_processing.py
│   └── utils.py
├── templates/
│   └── template.json
└── tests/
    ├── __init__.py
    ├── test_document_preparation.py
    ├── test_textract_api.py
    ├── test_response_parser.py
    ├── test_document_specific_processing.py
    ├── test_template_matching.py
    └── test_post_processing.py
```

## Running Tests

To run the test suite:

```
pytest
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.