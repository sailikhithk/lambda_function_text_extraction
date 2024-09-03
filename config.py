import os

#AWS CONFIG
AWS_ACCESS_KEY_ID = os.environ.get("KEY")
AWS_SECRET_ACCESS_KEY = os.environ.get("VALUE")
AWS_REGION = "us-east-1"

# S3 Configuration
BUCKET = "starwarsbff"
S3_BUCKET = "starwarsbff"

# Textract Configuration
TEXTRACT_FEATURES = ["TABLES", "FORMS"]

# Template Configuration
TEMPLATE_S3_KEY = os.environ.get('TEMPLATE_S3_KEY', 'templates/template.json')

# Logging Configuration
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Input and Output Paths
INPUT_PREFIX = 'input/'
OUTPUT_PREFIX = 'output/'
INTERMEDIATE_PREFIX = 'intermediate/'

# Performance Configuration
MAX_CONCURRENT_PAGES = int(os.environ.get('MAX_CONCURRENT_PAGES', 5))

# Error Handling
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', 3))
RETRY_DELAY = int(os.environ.get('RETRY_DELAY', 5))

# Ensure critical environment variables are set
if not S3_BUCKET:
    raise ValueError("S3_BUCKET environment variable is not set")

# Function to get full S3 path
def get_s3_path(key):
    return f's3://{S3_BUCKET}/{key}'

# Print configuration (for debugging purposes)
print("Current configuration:")
print(f"S3_BUCKET: {S3_BUCKET}")
print(f"AWS_REGION: {AWS_REGION}")
print(f"TEMPLATE_S3_KEY: {TEMPLATE_S3_KEY}")
print(f"LOG_LEVEL: {LOG_LEVEL}")