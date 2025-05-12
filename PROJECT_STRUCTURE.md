# DJ Schedule Manager - Project Structure

## Directory Structure

```
DJ Schedule Manager/
├── app/                    # Application package
│   ├── __init__.py
│   ├── main.py            # Main application logic (renamed from app.py)
│   ├── utils/             # Utility functions
│   │   ├── __init__.py
│   │   ├── schedule_parser.py
│   │   ├── validation.py
│   │   └── folder_enforcer.py
│   ├── config/            # Configuration files
│   │   ├── __init__.py
│   │   └── travel_times.py
│   ├── shared/            # Shared components
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   └── types.py
│   └── static/            # Static files
│       ├── css/
│       │   └── style.css
│       └── images/
├── tests/                 # Test files
│   ├── __init__.py
│   └── test_folder_structure_enforcer.py
├── deployment/            # Deployment configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx/
│       └── nginx.conf
├── scripts/              # Utility scripts
│   ├── deploy.sh
│   └── backup.sh
├── .env.example         # Example environment variables
├── .gitignore
├── requirements.txt     # Project dependencies
├── requirements-dev.txt # Development dependencies
└── README.md           # Project documentation
```

## Web Deployment Structure

### Docker Configuration
- `Dockerfile`: Multi-stage build for production
- `docker-compose.yml`: Service orchestration
- `nginx/nginx.conf`: Web server configuration

### Environment Variables
Required environment variables:
```
DOMAIN_NAME=your-domain.com
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
```

### Nginx Configuration
- SSL/TLS setup
- Reverse proxy to Streamlit
- Static file serving
- Security headers

## Deployment Steps

1. **Domain Setup**
   - Point domain to your server
   - Set up SSL certificate
   - Configure DNS records

2. **Server Setup**
   - Install Docker and Docker Compose
   - Set up environment variables
   - Configure firewall

3. **Application Deployment**
   - Build Docker image
   - Start services
   - Monitor logs

## Security Considerations

1. **SSL/TLS**
   - Force HTTPS
   - HSTS headers
   - Modern cipher suites

2. **Application Security**
   - Rate limiting
   - CORS configuration
   - Security headers

3. **Data Protection**
   - Regular backups
   - Secure environment variables
   - Access logging

## Monitoring

1. **Health Checks**
   - Application status
   - Database connectivity
   - Resource usage

2. **Logging**
   - Application logs
   - Access logs
   - Error tracking

3. **Metrics**
   - Response times
   - Error rates
   - Resource utilization

## Backup Strategy

1. **Regular Backups**
   - Database dumps
   - Configuration files
   - User data

2. **Backup Storage**
   - Secure cloud storage
   - Multiple locations
   - Retention policy

## Development Workflow

1. **Local Development**
   - Docker Compose for local testing
   - Hot reloading
   - Debug configuration

2. **CI/CD Pipeline**
   - Automated testing
   - Docker image building
   - Deployment automation

3. **Version Control**
   - Feature branches
   - Pull requests
   - Semantic versioning

## Coding Standards

### Function Naming Conventions
- All validation/check functions must start with `can_`
  - Example: `can_move_slot()`, `can_handle_travel_time()`
- All suggestion/recommendation functions must start with `suggest_`
  - Example: `suggest_replacements()`, `suggest_alternative_slots()`
- All parsing functions must start with `parse_`
  - Example: `parse_schedule()`, `parse_choice()`

### Documentation Standards
- Each file must have a header comment describing:
  - Purpose of the file
  - Input/output expectations
  - Dependencies
- Each function must be documented with:
  - Purpose
  - Parameters
  - Return values
  - Example usage

### Import Order
1. Standard library imports
2. Third-party imports
3. Local application imports

### Type Hints
- All function parameters and return values should have type hints
- Use `Optional[Type]` for parameters that can be None
- Use `List[Type]` for list parameters
- Use `Dict[KeyType, ValueType]` for dictionary parameters

### Error Handling
- Use specific exception types
- Include meaningful error messages
- Log errors appropriately
- Handle edge cases gracefully

### Testing
- Unit tests for all utility functions
- Integration tests for main application flow
- Test both success and failure cases
- Mock external dependencies

## Schedule Input Format

```
[Korean Day] Venue Name:
HH:MM-HH:MM DJ Name
```

Korean Day Indicators:
- 월 (Monday)
- 화 (Tuesday)
- 수 (Wednesday)
- 목 (Thursday)
- 금 (Friday)
- 토 (Saturday)
- 일 (Sunday)
- 주말 (Weekend)

## Features

- Simple text-based schedule input
- Structured display of schedules by venue
- Clean and intuitive user interface
- Smart conflict detection
- DJ switching recommendations
- Travel time consideration between venues
- Schedule validation
- Bulk DJ removal for specific days
- Replacement suggestions for removed slots 