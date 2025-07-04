# Profile Verification FastAPI Server

A secure FastAPI server for processing and validating CSV files with profile verification data.

## Features

- 🔐 **JWT-based Authentication**: Secure API endpoints with token-based authentication
- 📊 **CSV Processing**: Upload and validate CSV files with detailed validation results
- 🔒 **HTTPS Support**: Optional SSL/TLS encryption for secure communication
- 📈 **Data Validation**: Comprehensive validation of profile data including email, phone, and required fields
- 🚀 **FastAPI**: Modern, fast API framework with automatic documentation
- 🔧 **Development Tools**: Hot reload, interactive API docs, and health checks

## Quick Start

### Option 1: Using the Startup Script (Recommended)

```bash
cd server
python start_server.py
```

### Option 2: Manual Setup

1. **Install Dependencies**:
   ```bash
   cd server
   pip install -r requirements.txt
   ```

2. **Generate SSL Certificates (Optional)**:
   ```bash
   python generate_certs.py
   ```

3. **Start the Server**:
   ```bash
   python app.py
   ```

## API Endpoints

### Authentication
- **POST** `/api/token` - Get access token for API authentication

### CSV Processing
- **POST** `/api/process-csv-data` - Process CSV data sent as JSON
- **POST** `/api/process-csv` - Process uploaded CSV file

### Health & Status
- **GET** `/` - Root endpoint with API info
- **GET** `/health` - Health check endpoint

## API Documentation

Once the server is running, access the interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## CSV Format Requirements

The CSV file should contain the following columns (customize as needed):
- `name` - Required field
- `email` - Required field with email validation
- `phone` - Optional field with basic phone validation

### Example CSV:
```csv
name,email,phone
John Doe,john@example.com,+1234567890
Jane Smith,jane@example.com,+0987654321
```

## Security Features

- **JWT Authentication**: All processing endpoints require valid JWT tokens
- **Input Validation**: Comprehensive validation of CSV data and file formats
- **File Size Limits**: Maximum 10MB file size limit
- **CORS Protection**: Configured CORS for specific origins
- **HTTPS Support**: Optional SSL/TLS encryption

## Environment Variables

Create a `.env` file in the server directory:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# SSL (Optional)
SSL_CERT_FILE=server/certs/cert.pem
SSL_KEY_FILE=server/certs/key.pem
```

## Development

### Running in Development Mode

```bash
# With hot reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# With HTTPS
uvicorn app:app --reload --host 0.0.0.0 --port 8000 --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem
```

### Testing the API

1. **Get Access Token**:
   ```bash
   curl -X POST "http://localhost:8000/api/token" \
        -H "Content-Type: application/json"
   ```

2. **Process CSV Data**:
   ```bash
   curl -X POST "http://localhost:8000/api/process-csv-data" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer YOUR_TOKEN_HERE" \
        -d '{"filename": "test.csv", "data": "name,email,phone\nJohn Doe,john@example.com,+1234567890"}'
   ```

## Production Deployment

For production deployment:

1. **Use a proper secret key**: Generate a secure random secret key
2. **Use real SSL certificates**: Obtain certificates from a trusted CA
3. **Configure environment variables**: Set proper environment variables
4. **Use a reverse proxy**: Consider using Nginx or similar
5. **Set up monitoring**: Add logging and monitoring solutions

## Troubleshooting

### Common Issues

1. **SSL Certificate Errors**:
   - Run `python generate_certs.py` to create self-signed certificates
   - Or start without HTTPS for development

2. **Permission Errors**:
   - Use `pip install --user -r requirements.txt` to install packages locally

3. **Port Already in Use**:
   - Change the port in the environment variables or app.py

### Logs

The server will print detailed logs including:
- CSV processing results
- Validation errors and warnings
- Request/response information

## License

This project is licensed under the MIT License. 