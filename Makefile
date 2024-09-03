# Makefile for Textract Document Extraction Project on Windows

## build docker
docker build --no-cache -t lambda-python-packages .
docker run --rm -v C:\Users\likki\Downloads\Github\lambda_function_text_extraction\out:/out --entrypoint "" lambda-python-packages /bin/sh -c "cp -r /lambda_package/* /out"

# Navigate to the deployment package directory
cd C:\Users\likki\Downloads\Github\Textract-Document-Extraction\python\deployment_package

Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# Zip the contents of 'out', 'src', 'templates', and 'lambda_function.py' into a deployment package
Compress-Archive -Path .\out\*, .\lambda_function.py, .\config.py, .\src\*, .\templates\* -DestinationPath lambda_deployment_package.zip

# Use Python and pip from the active virtual environment
PYTHON := python  # Assuming 'python' is accessible in the PATH
PIP := pip        # Use the active pip environment

# Source directories
SRC_DIR := src
TEST_DIR := tests

.PHONY: all requirements dev-requirements install test lint format clean run

all: requirements install test

requirements:
	@echo "Generating requirements.txt..."
	$(PIP) install pip-tools
	# Correctly call pip-compile
	pip-compile --output-file=requirements.txt requirements.in

dev-requirements:
	@echo "Generating dev-requirements.txt..."
	$(PIP) install pip-tools
	# Correctly call pip-compile
	pip-compile --output-file=dev-requirements.txt dev-requirements.in

install: requirements
	@echo "Installing dependencies..."
	$(PIP) install -r requirements.txt

install-dev: dev-requirements
	@echo "Installing development dependencies..."
	$(PIP) install -r dev-requirements.txt

test: install
	@echo "Running tests..."
	pytest $(TEST_DIR)

lint: install-dev
	@echo "Linting code..."
	flake8 $(SRC_DIR)

format: install-dev
	@echo "Formatting code..."
	black $(SRC_DIR)

clean:
	@echo "Cleaning up..."
	@if exist $(VENV) rmdir /s /q $(VENV)
	@for /r %%i in (*.pyc) do del /f %%i
	@for /d /r %%i in (__pycache__) do rmdir /s /q %%i

run:
	@echo "Running the main script..."
	$(PYTHON) main.py

build:
	@echo "Making python package"
	python setup.py sdist bdist_wheel

# Add any other project-specific commands here
# Define a function to recursively print directory structure with indentation
function Show-DirectoryTree {
    param (
        [string]$Path,
        [string]$Indent = "",
        [string]$OutputFile
    )

    # Get all items in the current path, excluding 'venv' and '__pycache__'
    Get-ChildItem -Path $Path | Where-Object {
        $_.FullName -notmatch '\\venv' -and
        $_.FullName -notmatch '\\__pycache__' -and
		$_.FullName -notmatch '\\out'
    } | ForEach-Object {
        # Check if the current item is a directory
        if ($_.PSIsContainer) {
            # Print the directory name with a '+' sign and call recursively
            "$Indent+ $($_.Name)" | Out-File -FilePath $OutputFile -Append
            Show-DirectoryTree -Path $_.FullName -Indent "$Indent  " -OutputFile $OutputFile
        } else {
            # Print the file name with a '| ' sign
            "$Indent|   $($_.Name)" | Out-File -FilePath $OutputFile -Append
        }
    }
}

# Define the output file path
$outputFilePath = "directory_tree.txt"

# Clear the file if it exists, to ensure fresh output
if (Test-Path $outputFilePath) {
    Remove-Item $outputFilePath
}

# Call the function with the current directory and output file path
Show-DirectoryTree -Path . -OutputFile $outputFilePath

# Confirm completion
Write-Output "Directory tree has been written to $outputFilePath"

