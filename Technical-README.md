# Textract Document Extraction

This project provides a complete setup for deploying an AWS Lambda function that processes PDF documents, converts them to images, and analyzes them using AWS Textract. All operations are handled using S3 to avoid using the AWS Lambda file system.

## Table of Contents
1. [Project Structure](#project-structure)
2. [Prerequisites](#prerequisites)
3. [Setup Guide](#setup-guide)
   - [1. Directory Structure](#1-directory-structure)
   - [2. Building the Docker Image](#2-building-the-docker-image)
   - [3. Packaging the Lambda Deployment](#3-packaging-the-lambda-deployment)
4. [AWS Lambda Configuration](#aws-lambda-configuration)
   - [1. Creating the Lambda Function](#1-creating-the-lambda-function)
   - [2. Setting Environment Variables](#2-setting-environment-variables)
   - [3. Adjusting Memory and Timeout](#3-adjusting-memory-and-timeout)
   - [4. Adding IAM Role](#4-adding-iam-role)
5. [Testing and Validation](#testing-and-validation)
6. [Additional Tips](#additional-tips)

## Project Structure

Below is the recommended directory structure for this project:

```
Textract-Document-Extraction/
│
├── python/
│   ├── deployment_package/
│   │   ├── out/                     # Directory for compiled packages (ignored in .gitignore)
│   │   ├── src/                     # Source code files
│   │   │   ├── document_preparation.py
│   │   │   ├── document_specific_processing.py
│   │   │   ├── post_processing.py
│   │   │   ├── response_parser.py
│   │   │   ├── template_matching.py
│   │   │   ├── textract_api.py
│   │   │   └── utils.py
│   │   ├── templates/               # Templates directory
│   │   ├── lambda_function.py       # Main Lambda function handler
│   │   ├── config.py                # Configuration file for environment variables
│   │   └── requirements.txt         # List of required Python packages
│   └── Dockerfile                   # Dockerfile for building deployment package
└── .gitignore                       # Git ignore file configuration
```

## Prerequisites

- AWS Account with access to IAM, S3, Lambda, and CloudWatch.
- Docker installed on your machine.
- AWS CLI installed and configured.
- Basic understanding of AWS services and Python.

## Setup Guide

### 1. Directory Structure

To create the above directory structure:

1. **Manually create directories and files** as shown in the structure above.
2. **Run the PowerShell script** provided in this guide to generate a directory tree listing (optional).

### 2. Building the Docker Image

Build the Docker image to compile Python dependencies compatible with AWS Lambda:

1. **Navigate to the deployment package directory:**
   ```bash
   cd C:\Users\likki\Downloads\Github\Textract-Document-Extraction\python\deployment_package
   ```

2. **Build the Docker image:**
   ```bash
   docker build --no-cache -t lambda-python-packages .
   ```

3. **Run the Docker container and extract compiled packages:**
   ```bash
   docker run --rm -v C:\Users\likki\Downloads\Github\Textract-Document-Extraction\python\deployment_package\out:/out --entrypoint "" lambda-python-packages /bin/sh -c "cp -r /lambda_package/* /out"
   ```

### 3. Packaging the Lambda Deployment

1. **Navigate to the deployment package directory:**
   ```bash
   cd C:\Users\likki\Downloads\Github\Textract-Document-Extraction\python\deployment_package
   ```

2. **Remove Recursive items:**
    ```bash
    Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
    ```

3. **Create the deployment package ZIP file:**
   ```bash
   Compress-Archive -Path .\out\*, .\lambda_function.py, .\config.py, .\src\*, .\templates\* -DestinationPath lambda_deployment_package.zip
   ```

## AWS Lambda Configuration

### 1. Creating the Lambda Function

1. Go to the [AWS Lambda Console](https://console.aws.amazon.com/lambda/).
2. Click **Create function**.
3. Choose **Author from scratch**.
4. Set the function name (e.g., `TextractDocumentProcessing`).
5. Set **Runtime** to Python 3.11.
6. Choose or create an execution role with appropriate permissions.

### 2. Setting Environment Variables

Add the following environment variables in the Lambda console:

- **BUCKET**: Name of your S3 bucket.
- **AWS_ACCESS_KEY_ID**: Access key for your IAM role.
- **AWS_SECRET_ACCESS_KEY**: Secret access key for your IAM role.
- **REGION_NAME**: AWS region where your resources are hosted.

### 3. Adjusting Memory and Timeout

1. **Memory Size**: Set the memory size to 1024 MB or more depending on your processing needs.
2. **Timeout**: Increase the timeout setting to 5 minutes (300 seconds) to accommodate longer processing times.

### 4. Adding IAM Role

Create an IAM role or use an existing role with the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket",
        "logs:*",
        "sts:AssumeRole"
      ],
      "Resource": [
        "arn:aws:s3:::starwarsbff",
        "arn:aws:s3:::starwarsbff/*",
        "arn:aws:logs:*:*:*",
        "arn:aws:iam::872378549974:role/StarwarsBFF"
      ]
    }
  ]
}
```

Ensure the trust policy allows Lambda or your specific IAM user to assume the role.

## Testing and Validation

### 1. Testing the Lambda Function

1. In the Lambda console, create a test event simulating an S3 upload.
2. Execute the test and review the logs in CloudWatch to verify proper execution.

### 2. Monitoring with CloudWatch Logs

1. Go to [CloudWatch Logs](https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups).
2. Check logs under `/aws/lambda/<function-name>` for detailed execution output.

## Additional Tips

- **Ensure Python Dependencies Compatibility:** Test locally and within Docker to ensure compatibility with AWS Lambda.
- **Update .gitignore:** Exclude unnecessary files and directories like virtual environments and compiled outputs.
- **Review Security Settings:** Regularly review IAM roles and permissions for security best practices.

This README provides a step-by-step guide for setting up and deploying the AWS Lambda function, including directory structure, Docker commands, and Lambda configurations. By following these instructions, even those with limited technical knowledge should be able to deploy and manage the Lambda function successfully.