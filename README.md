# Apple Maps Bulk Listing Manager

A comprehensive Python application for managing bulk location listings on Apple Maps via the Apple Business Connect API and third-party aggregators (Yext, Uberall, Rio SEO).

## Features

- **Multi-format Data Support**: Read from CSV, Excel, JSON, and database sources
- **Data Validation**: Comprehensive validation with Pydantic schemas
- **Multiple Aggregator Support**: Apple Business Connect, Yext, Uberall, Rio SEO
- **Bulk Processing**: Async concurrent uploads with progress tracking
- **Error Handling**: Retry logic with exponential backoff and failed record quarantine
- **Real-time Monitoring**: Progress tracking and status updates
- **CLI Interface**: Rich command-line interface with interactive progress

## Installation

### Prerequisites
- Python 3.9+
- PostgreSQL database (optional, SQLite for development)

### Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd apple-maps-manager
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database:**
```bash
python -m src.main init-db
```

## Configuration

Create a `.env` file with your API credentials:

```env
# Apple Business Connect
APPLE_CLIENT_ID=your_apple_client_id
APPLE_CLIENT_SECRET=your_apple_client_secret
APPLE_TEAM_ID=your_apple_team_id
APPLE_KEY_ID=your_apple_key_id
APPLE_PRIVATE_KEY_PATH=path/to/your/private/key.p8

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/apple_maps_db

# Aggregator APIs
YEXT_API_KEY=your_yext_api_key
UBERALL_API_KEY=your_uberall_api_key
RIO_SEO_API_KEY=your_rio_seo_api_key
```

## Usage

### CLI Commands

#### Preview File
```bash
python -m src.main preview data/input/locations.csv
```

#### Upload Locations
```bash
# Validate data only
python -m src.main upload data/input/locations.csv --validate-only

# Upload to Apple Business Connect
python -m src.main upload data/input/locations.csv --aggregator apple

# Upload to Yext
python -m src.main upload data/input/locations.csv --aggregator yext
```

#### Test Connections
```bash
# Test Apple connection
python -m src.main test-connection --aggregator apple
```

### Data Format

The system expects location data with these required fields:

```json
{
  "business_name": "Store Name",
  "street_address": "123 Main St",
  "city": "New York",
  "state": "NY",
  "postal_code": "10001",
  "country": "US",
  "phone": "+12125551234",
  "website": "https://example.com"
}
```

### Supported Input Formats

1. **CSV**: Standard comma-separated values
2. **Excel**: XLSX and XLS files
3. **JSON**: JSON arrays or objects
4. **Databases**: Direct database queries

### File Structure

```
apple-maps-manager/
├── src/
│   ├── config/          # Configuration management
│   ├── api/             # API clients
│   ├── data/            # Data processing
│   ├── engine/          # Upload engine
│   ├── storage/         # Database models
│   ├── main.py          # CLI entry point
├── data/
│   ├── input/           # Input files
│   ├── output/          # Generated reports
│   ├── failed/          # Failed records
│  └── logs/            # Application logs
├── requirements.txt
├── .env.example
└── README.md
```

## API Documentation

### Main Classes

#### BulkUploader
Handles bulk upload operations:
```python
uploader = BulkUploader(settings)
await uploader.upload_from_file(
    file_path="data/locations.csv",
    aggregator="apple",
    batch_size=100
)
```

#### DataProcessor
Processes and validates location data:
```python
processor = DataProcessor()
processed_data = processor.process_dataframe(df)
```

#### DataTransformer
Transforms data between different formats:
```python
transformer = DataTransformer()
apple_format = transformer.transform_to_aggregator_format(
    location_data, 
    AggregatorType.APPLE
)
```

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
flake8 src/
```

### Type Checking
```bash
mypy src/
```

## Error Handling

The system provides comprehensive error handling:

1. **Validation Errors**: Detected during data validation
2. **API Errors**: Handled with retry logic
3. **Connection Errors**: Managed with exponential backoff
4. **Failed Records**: Stored in quarantine for later processing

### Failed Records Queue
Failed uploads are stored in a database queue and can be retried:

```bash
python -m src.main retry --max-records 100
```

## Monitoring

The system provides real-time monitoring:

- **Progress Tracking**: Real-time upload progress
- **Error Logging**: Detailed error reporting
- **Performance Metrics**: Throughput and timing statistics
- **Health Checks**: API connectivity status

## Deployment

### Production Configuration
- Use PostgreSQL for production
- Configure appropriate logging levels
- Set up monitoring and alerting
- Secure credential storage

### Docker Support
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "src.main", "upload", "data/input/locations.csv"]
```

## Support

For issues and questions:
- Check the documentation
- Review logs in `data/logs/`
- Enable debug mode with `--debug`

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request# Apple-Maps-Bulk-Listing-Manager
