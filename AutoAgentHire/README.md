# AutoAgentHire: AI-Powered Job Application Automation Platform

AutoAgentHire is an intelligent job application automation system that leverages AI and web scraping to streamline the job search and application process. The platform automatically finds relevant job openings, matches them to your profile, generates personalized cover letters, and submits applications on your behalf.

## 🌟 Features

### Core Functionality
- **Intelligent Job Scraping**: Automated scraping of job postings from LinkedIn and other platforms
- **AI-Powered Matching**: Uses machine learning to match jobs to your profile and preferences
- **Smart Resume Parsing**: NLP-based extraction of skills, experience, and qualifications from your resume
- **Automated Cover Letter Generation**: LLM-powered personalized cover letter creation for each application
- **Automated Job Applications**: Seamless application submission with human-like behavior patterns

### Advanced Capabilities
- **Vector-based Similarity Search**: RAG-powered semantic matching for better job recommendations
- **Multi-platform Support**: Extensible architecture for LinkedIn, Indeed, and other job boards
- **Application Tracking**: Comprehensive monitoring of application status and success rates
- **Rate Limiting & Stealth**: Built-in protections to avoid detection and account restrictions
- **Scheduled Automation**: Set up recurring job searches and applications

### API & Integration
- **RESTful API**: Complete FastAPI-based backend with comprehensive documentation
- **Real-time Monitoring**: Live application status and performance metrics
- **Customizable Workflows**: Flexible configuration for different job search strategies
- **Background Processing**: Asynchronous job processing for scalable operations

## 🏗️ Architecture

```
AutoAgentHire/
├── app/                              # Main application folder
│   ├── main.py                       # FastAPI entry point
│   ├── config.py                     # Environment variables & settings
│   ├── routes/                       # API routes
│   │   └── jobs.py                   # Job search & apply endpoints
│   ├── services/                     # Business logic
│   │   ├── job_scraper.py            # LinkedIn scraping logic
│   │   ├── resume_parser.py          # NLP resume parsing
│   │   ├── matcher.py                # AI matching & scoring
│   │   ├── cover_letter_generator.py # LLM-based cover letter creation
│   │   └── auto_apply.py             # Automation flow
│   ├── utils/                        # Helper utilities
│   │   ├── logger.py                 # Logging configuration
│   │   └── vectorstore.py            # RAG embeddings & similarity
│   └── models/                       # Data models & schemas
│       └── job_schema.py             # Pydantic models
├── automation/                       # Browser automation scripts
│   └── linkedin_bot.py               # LinkedIn automation bot
├── requirements.txt                  # Python dependencies
├── .env                              # Environment configuration
├── README.md                         # This file
└── run.sh                            # Application startup script
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Google Chrome or Chromium browser
- OpenAI API key
- LinkedIn account

### Installation

1. **Clone the repository**
   ```bash
   cd AutoAgentHire
   ```

2. **Run the setup script**
   ```bash
   ./run.sh
   ```

3. **Configure your environment**
   Edit the `.env` file with your credentials:
   ```bash
   # API Keys
   OPENAI_API_KEY=your_openai_api_key_here
   
   # LinkedIn Credentials
   LINKEDIN_EMAIL=your_linkedin_email@example.com
   LINKEDIN_PASSWORD=your_linkedin_password_here
   
   # Other settings...
   ```

4. **Upload your resume**
   Place your resume PDF at `./uploads/resume.pdf`

5. **Start the application**
   The `run.sh` script will automatically start the FastAPI server at `http://localhost:8000`

### API Documentation
Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## 📖 Usage Examples

### Basic Job Search
```python
import requests

# Search for jobs
response = requests.post("http://localhost:8000/api/v1/jobs/search", json={
    "keywords": "Python Developer",
    "location": "San Francisco, CA",
    "experience_level": "mid",
    "limit": 20
})

jobs = response.json()["jobs"]
```

### Automated Job Applications
```python
# Start auto-apply process
response = requests.post("http://localhost:8000/api/v1/jobs/auto-apply", json={
    "keywords": "Software Engineer",
    "location": "Remote",
    "max_applications_per_run": 5,
    "min_match_score": 0.7,
    "generate_cover_letter": True
})
```

### Job Matching
```python
# Get matched jobs based on your profile
response = requests.post("http://localhost:8000/api/v1/jobs/match", json={
    "keywords": "Machine Learning Engineer",
    "location": "New York, NY",
    "limit": 10
})

matched_jobs = response.json()
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for AI features | Required |
| `LINKEDIN_EMAIL` | LinkedIn account email | Required |
| `LINKEDIN_PASSWORD` | LinkedIn account password | Required |
| `MAX_APPLICATIONS_PER_DAY` | Daily application limit | 50 |
| `APPLICATION_DELAY_MIN` | Min delay between applications (seconds) | 30 |
| `APPLICATION_DELAY_MAX` | Max delay between applications (seconds) | 120 |
| `SIMILARITY_THRESHOLD` | Job matching threshold | 0.8 |
| `DEBUG` | Enable debug mode | False |

### Application Settings

Customize the behavior by modifying the configuration in `app/config.py` or through environment variables.

## 🛡️ Safety & Ethics

### Built-in Protections
- **Rate Limiting**: Prevents excessive requests that could trigger platform restrictions
- **Human-like Behavior**: Randomized delays and actions to mimic natural usage patterns
- **Respectful Automation**: Follows robots.txt and platform terms of service
- **Error Handling**: Graceful failure handling to prevent account issues

### Best Practices
- **Credential Security**: Never commit credentials to version control
- **Responsible Usage**: Respect platform rate limits and terms of service
- **Quality Applications**: Use AI matching to apply only to relevant positions
- **Monitoring**: Regularly check application success rates and adjust settings

## 🔧 Development

### Project Structure
The application follows a clean architecture pattern:
- **Routes**: Handle HTTP requests and responses
- **Services**: Contain business logic and external integrations
- **Models**: Define data structures and validation
- **Utils**: Provide common utilities and helpers
- **Automation**: Browser automation and scraping logic

### Adding New Job Platforms
1. Create a new scraper service in `app/services/`
2. Implement the platform-specific scraping logic
3. Add automation bot in `automation/`
4. Update the job matcher to handle new data formats

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_job_scraper.py
```

## 📊 Monitoring & Analytics

### Application Statistics
- Total jobs scraped and analyzed
- Application success rates
- Average job match scores
- Daily application counts
- Response rates from companies

### API Endpoints for Monitoring
- `GET /api/v1/jobs/applications/status` - Application statistics
- `GET /health` - System health check
- `GET /` - Service information

## 🤝 Contributing

We welcome contributions! Please read our contributing guidelines and submit pull requests for any improvements.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is designed to assist with job searching and should be used responsibly. Users are responsible for:
- Ensuring compliance with platform terms of service
- Providing accurate information in applications
- Monitoring automated activities
- Respecting rate limits and platform policies

The developers are not responsible for any account restrictions or issues that may arise from improper usage.

## 🆘 Support

### Common Issues
1. **Login failures**: Check LinkedIn credentials and 2FA settings
2. **Scraping errors**: Verify Chrome/Chromium installation
3. **API errors**: Confirm OpenAI API key and credits
4. **Rate limiting**: Adjust delay settings in configuration

### Getting Help
- Open an issue on GitHub
- Check the documentation at `/docs`
- Review the logs in `autoagenthire.log`

## 🗺️ Roadmap

### Upcoming Features
- [ ] Support for additional job platforms (Indeed, Glassdoor)
- [ ] Advanced resume optimization suggestions
- [ ] Integration with ATS systems
- [ ] Mobile app for monitoring applications
- [ ] Enhanced AI interview preparation
- [ ] Company research automation
- [ ] Salary negotiation assistance

### Version History
- **v1.0.0**: Initial release with LinkedIn automation
- **v1.1.0**: Added AI-powered cover letter generation
- **v1.2.0**: Implemented vector-based job matching
- **v1.3.0**: Enhanced scraping and stealth capabilities

---

**AutoAgentHire** - Revolutionizing job searching with AI automation 🚀