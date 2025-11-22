# SOGS - Snowflake Optimizer & Governance Suite

A comprehensive platform for Snowflake cost optimization, performance tuning, governance, security, and database migration.

## Features

### 1. Cost Intelligence Engine
- **Real-time Cost Monitoring**: Track credit usage and spending across warehouses
- **Idle Warehouse Detection**: Identify warehouses consuming resources unnecessarily
- **Cost Anomaly Detection**: AI-powered alerts for unusual spending patterns
- **Predictive Cost Analysis**: Forecast future costs based on historical trends
- **Automated Recommendations**: Actionable insights for cost reduction

### 2. AI-Powered Performance Advisor
- **Query Profiling**: Deep analysis of query performance and execution patterns
- **Slow Query Detection**: Identify and analyze resource-intensive queries
- **Optimization Recommendations**: AI-driven suggestions for query improvements
- **Clustering Key Analysis**: Automatic clustering key recommendations
- **Performance Metrics Dashboard**: Visual insights into query performance

### 3. Governance & Security Hub
- **User Access Auditing**: Track and monitor user access patterns
- **Role Hierarchy Management**: Visualize and manage role-based access control
- **Sensitive Data Detection**: Automatic identification of PII and sensitive columns
- **Data Masking Policy Templates**: Pre-built templates for common data types
- **Failed Login Monitoring**: Security threat detection and alerting
- **Compliance Dashboard**: GDPR, HIPAA, and SOC2 compliance tracking

### 4. AI & ML Monitoring
- **Cortex AI Usage Tracking**: Monitor Snowflake Cortex AI function usage and credits
- **LLM Model Analytics**: Track usage across different language models (Llama, Mistral, Arctic, etc.)
- **Credit Consumption**: Real-time monitoring of AI/ML credit usage
- **User Activity**: Track AI/ML adoption by user
- **Performance Metrics**: Monitor AI call duration and error rates
- **Cost Optimization**: Recommendations for model selection and usage patterns
- **Function Breakdown**: Usage statistics for COMPLETE, SENTIMENT, TRANSLATE, SUMMARIZE, etc.
- **Model Comparison**: Compare performance and cost across different LLM models

### 5. Migration & Integration Toolkit
- **SQL Dialect Conversion**: Automatic conversion from Oracle, MySQL, MS SQL to Snowflake
- **Schema Compatibility Analysis**: Identify migration challenges before they occur
- **DDL Generation**: Automatic table creation scripts for Snowflake
- **Data Validation Tools**: Verify data integrity post-migration
- **ELT Pipeline Templates**: Pre-built templates for common migration patterns
- **Migration Best Practices**: Expert guidance throughout the migration process

## Quick Start

### Option 1: Run with Docker (Recommended)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Snowflake
   ```

2. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   Open your browser and navigate to `http://localhost:8000`

### Option 2: Run Locally with Python

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Snowflake
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Access the application**:
   Open your browser and navigate to `http://localhost:8000`

## Configuration

### Snowflake Credentials

You can configure Snowflake credentials in two ways:

#### Method 1: Via Web UI (Recommended)
1. Navigate to `http://localhost:8000`
2. Fill in the Snowflake credentials form
3. Click "Connect to Snowflake"

#### Method 2: Via Environment Variables
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your Snowflake credentials:
   ```env
   SNOWFLAKE_ACCOUNT=your-account.snowflakecomputing.com
   SNOWFLAKE_USER=your-username
   SNOWFLAKE_PASSWORD=your-password
   SNOWFLAKE_WAREHOUSE=COMPUTE_WH
   SNOWFLAKE_DATABASE=YOUR_DATABASE
   SNOWFLAKE_SCHEMA=PUBLIC
   SNOWFLAKE_ROLE=ACCOUNTADMIN
   ```

### Required Snowflake Permissions

To access all features, your Snowflake user needs the following privileges:

- **ACCOUNTADMIN** or **SYSADMIN** role (recommended)
- Access to `SNOWFLAKE.ACCOUNT_USAGE` schema for usage metrics
- Read access to `INFORMATION_SCHEMA` for schema analysis
- Permissions to view warehouse metering and query history

Minimum privileges:
```sql
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE YOUR_ROLE;
GRANT USAGE ON WAREHOUSE YOUR_WAREHOUSE TO ROLE YOUR_ROLE;
GRANT USAGE ON DATABASE YOUR_DATABASE TO ROLE YOUR_ROLE;
GRANT USAGE ON SCHEMA YOUR_DATABASE.YOUR_SCHEMA TO ROLE YOUR_ROLE;
```

## Using the Application

### Dashboard
The dashboard provides a comprehensive overview of your Snowflake environment:
- Cost summary (last 30 days)
- Active recommendations across all modules
- Quick access to key metrics

### Cost Intelligence
Monitor and optimize your Snowflake costs:
- View cost summaries and breakdowns by warehouse
- Identify idle warehouses
- Detect cost anomalies
- Get automated cost reduction recommendations

### Performance Advisor
Optimize query performance:
- View slow-running queries
- Analyze individual queries for optimization opportunities
- Get AI-powered recommendations for query improvements
- Review table statistics and clustering opportunities

### Governance & Security
Ensure compliance and security:
- Audit user access patterns
- Monitor failed login attempts
- Detect sensitive data columns
- Review and create data masking policies
- Generate compliance reports

### AI & ML Monitoring
Track and optimize Snowflake AI/ML usage:
- View AI/ML usage summary and credit consumption
- Monitor Cortex AI function usage (COMPLETE, SENTIMENT, TRANSLATE, etc.)
- Track LLM model performance (Llama, Mistral, Arctic, etc.)
- Analyze usage by user and identify adoption patterns
- View expensive AI calls and optimization opportunities
- Get recommendations for model selection and cost optimization
- Access list of supported Cortex functions and LLM models

### Migration Toolkit
Accelerate your migration to Snowflake:
- Convert SQL from other databases (Oracle, MySQL, MS SQL)
- Analyze schema compatibility
- Get migration best practices and recommendations
- Generate ELT pipeline templates

## API Documentation

Once the application is running, access the interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key API Endpoints

#### Credentials
- `POST /api/credentials/configure` - Configure Snowflake credentials
- `GET /api/credentials/test` - Test current credentials

#### Cost Intelligence
- `GET /api/cost/summary` - Get cost summary
- `GET /api/cost/by-warehouse` - Get cost breakdown by warehouse
- `GET /api/cost/idle-warehouses` - Get idle warehouses
- `GET /api/cost/recommendations` - Get cost optimization recommendations

#### Performance
- `GET /api/performance/slow-queries` - Get slow queries
- `POST /api/performance/analyze-query` - Analyze a specific query
- `GET /api/performance/recommendations` - Get performance recommendations

#### Governance
- `GET /api/governance/user-access-audit` - Get user access audit
- `POST /api/governance/detect-sensitive-columns` - Detect sensitive columns
- `GET /api/governance/failed-logins` - Get failed login attempts
- `GET /api/governance/compliance-report` - Generate compliance report

#### AI/ML Monitoring
- `GET /api/ai-ml/summary` - Get AI/ML usage summary
- `GET /api/ai-ml/cortex-by-function` - Get Cortex usage by function
- `GET /api/ai-ml/llm-models` - Get LLM model usage statistics
- `GET /api/ai-ml/usage-by-user` - Get AI/ML usage by user
- `GET /api/ai-ml/usage-trend` - Get AI/ML usage trend over time
- `GET /api/ai-ml/expensive-calls` - Get expensive AI/ML calls
- `GET /api/ai-ml/error-rate` - Get AI/ML error rate statistics
- `GET /api/ai-ml/recommendations` - Get AI/ML optimization recommendations
- `GET /api/ai-ml/cortex-functions` - Get list of available Cortex functions
- `GET /api/ai-ml/supported-models` - Get list of supported LLM models

#### Migration
- `POST /api/migration/convert-sql` - Convert SQL dialect
- `POST /api/migration/analyze-schema` - Analyze schema compatibility
- `GET /api/migration/recommendations` - Get migration best practices

## Docker Commands

### Build the image:
```bash
docker build -t sogs:latest .
```

### Run the container:
```bash
docker run -p 8000:8000 sogs:latest
```

### Using Docker Compose:
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build -d
```

## Architecture

```
sogs/
├── app.py                      # Main FastAPI application
├── config.py                   # Configuration management
├── snowflake_manager.py        # Snowflake connection manager
├── modules/
│   ├── cost_intelligence.py   # Cost monitoring and optimization
│   ├── performance_advisor.py # Query performance analysis
│   ├── governance_security.py # Governance and security features
│   └── migration_toolkit.py   # Migration and conversion tools
├── templates/
│   └── index.html             # Web UI
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose configuration
└── README.md                  # This file
```

## Technology Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: Snowflake
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Containerization**: Docker & Docker Compose
- **Key Libraries**:
  - `snowflake-connector-python` - Snowflake connectivity
  - `fastapi` - Web framework
  - `uvicorn` - ASGI server
  - `pydantic` - Data validation
  - `sqlparse` - SQL parsing and analysis

## Security Best Practices

1. **Never commit credentials**: Use `.env` files (excluded from git) or environment variables
2. **Use least privilege**: Grant only necessary Snowflake permissions
3. **Rotate credentials regularly**: Update Snowflake passwords periodically
4. **Enable MFA**: Use multi-factor authentication for Snowflake accounts
5. **Monitor access**: Regularly review user access audit logs
6. **Secure deployment**: Use HTTPS in production environments

## Troubleshooting

### Connection Issues
- Verify Snowflake account URL format: `account-name.snowflakecomputing.com`
- Check network connectivity to Snowflake
- Verify credentials and role permissions
- Ensure warehouse is running

### Permission Errors
- Grant `IMPORTED PRIVILEGES` on SNOWFLAKE database
- Verify role has access to ACCOUNT_USAGE schema
- Check warehouse and database permissions

### Docker Issues
- Ensure Docker daemon is running
- Check port 8000 is not in use: `lsof -i :8000`
- Verify Docker has sufficient resources allocated

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

This project is licensed under the MIT License.

## Support

For issues, questions, or feature requests, please open an issue on the GitHub repository.

## Roadmap

Future enhancements planned:
- Advanced ML-based cost prediction
- Automated warehouse scaling
- Integration with BI tools
- Custom alerting and notifications
- Multi-tenant support
- Advanced data lineage tracking
- Automated query optimization execution
- Integration with dbt for transformation workflows

---

**Built with ❄️ for Snowflake optimization**
