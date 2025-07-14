import json
import os
import csv
from io import StringIO
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import uvicorn
import regex
from dotenv import load_dotenv

# Load environment variables from root directory
load_dotenv(dotenv_path="../.env")

# Security configuration
API_KEY = os.getenv("API_KEY", "your-secure-api-key-here-change-this-in-production")

# API Key authentication function
async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return True

# FastAPI app initialization
app = FastAPI(
    title="Profile Verification System",
    description="Secure API for profile verification and CSV processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173",
                   "https://localhost:3000", "https://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Pydantic models
class CSVProcessRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    data: str = Field(..., min_length=1)

    @field_validator('filename')
    def validate_filename(cls, v):
        if not v.endswith('.csv'):
            raise ValueError('Filename must end with .csv')
        return v

class CSVProcessResponse(BaseModel):
    success: bool
    message: str
    processed_rows: int
    validation_results: List[Dict[str, Any]]
    summary: Dict[str, Any]
    processed_csv_data: str

# Utility functions
def validate_csv_content(csv_content: str) -> Dict[str, Any]:
    """Validate CSV content and return validation results"""
    try:
        # Parse CSV content
        csv_reader = csv.DictReader(StringIO(csv_content))
        rows = list(csv_reader)

        if not rows:
            raise ValueError("CSV file is empty or has no data rows")

        # Basic validation results
        validation_results = []
        total_rows = len(rows)
        valid_rows = 0

        for i, row in enumerate(rows):
            row_validation = {
                "row_number": i + 1,
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "data": row
            }

            # Check for empty required fields
            required_fields = ["name", "email", "phone"]
            for field in required_fields:
                if field in row and not row[field].strip():
                    row_validation["errors"].append(f"Missing required field: {field}")
                    row_validation["is_valid"] = False

            # Email validation
            if "email" in row and row["email"]:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not regex.match(email_pattern, row["email"]):
                    row_validation["errors"].append("Invalid email format")
                    row_validation["is_valid"] = False

            # Phone validation (basic)
            if "phone" in row and row["phone"]:
                phone_pattern = r'^\+?[\d\s\-\(\)]{10,}$'
                if not regex.match(phone_pattern, row["phone"]):
                    row_validation["warnings"].append("Phone number format may be invalid")

            if row_validation["is_valid"]:
                valid_rows += 1

            validation_results.append(row_validation)

        summary = {
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "invalid_rows": total_rows - valid_rows,
            "validation_rate": (valid_rows / total_rows) * 100 if total_rows > 0 else 0,
            "headers": list(csv_reader.fieldnames) if csv_reader.fieldnames else []
        }

        return {
            "validation_results": validation_results,
            "summary": summary
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV validation error: {str(e)}"
        )

# API Routes
@app.get("/")
async def root():
    return {"message": "Profile Verification System API", "version": "1.0.0", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/process-csv", response_model=CSVProcessResponse)
async def process_csv(
    file: UploadFile = File(...),
    _: bool = Depends(verify_api_key)
):
    """Process uploaded CSV file with validation and security checks"""

    # Security checks
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )

    # File size check (max 10MB)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 10MB limit"
        )

    try:
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')

        print(f"Processing CSV file: {file.filename}")
        print(f"File size: {len(content)} bytes")

        # Validate and process CSV
        validation_data = validate_csv_content(csv_content)

        print(f"Total rows: {validation_data['summary']['total_rows']}")
        print(f"Valid rows: {validation_data['summary']['valid_rows']}")
        print(f"Invalid rows: {validation_data['summary']['invalid_rows']}")

        return CSVProcessResponse(
            success=True,
            message="CSV file processed successfully",
            processed_rows=validation_data['summary']['total_rows'],
            validation_results=validation_data['validation_results'],
            summary=validation_data['summary'],
            processed_csv_data=csv_content
        )

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File encoding error. Please ensure the file is UTF-8 encoded."
        )
    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CSV file: {str(e)}"
        )

@app.post("/api/process-csv-data", response_model=CSVProcessResponse)
async def process_csv_data(
    request: CSVProcessRequest,
    _: bool = Depends(verify_api_key)
):
    """Process CSV data sent as JSON payload"""

    try:
        print(f"Processing CSV data from: {request.filename}")
        print(f"Data length: {len(request.data)} characters")

        # Validate and process CSV
        validation_data = validate_csv_content(request.data)

        print(f"Total rows: {validation_data['summary']['total_rows']}")
        print(f"Valid rows: {validation_data['summary']['valid_rows']}")
        print(f"Invalid rows: {validation_data['summary']['invalid_rows']}")

        return CSVProcessResponse(
            success=True,
            message="CSV data processed successfully",
            processed_rows=validation_data['summary']['total_rows'],
            validation_results=validation_data['validation_results'],
            summary=validation_data['summary'],
            processed_csv_data=request.data
        )

    except Exception as e:
        print(f"Error processing CSV data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CSV data: {str(e)}"
        )

if __name__ == "__main__":
    print("🚀 Starting Profile Verification Server...")
    print("📍 Server available at: http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("=" * 50)

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
