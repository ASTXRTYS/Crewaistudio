# AUREN 2.0 - Biometric Optimization System

A comprehensive AI-powered system for biometric optimization, featuring advanced protocols, agentic RAG, and WhatsApp integration.

## 🚀 Features

### Core Protocols
- **Journal Protocol**: Peptide tracking and dosing management
- **MIRAGE Protocol**: Visual biometric analysis (ptosis, inflammation, symmetry)
- **VISOR Protocol**: Media registry and documentation system

### AI Components
- **Agentic RAG**: Intelligent information retrieval with reasoning
- **CrewAI Agents**: Multi-agent coordination for complex analysis
- **Biometric Analysis**: Facial landmark detection and scoring
- **Alert Management**: Real-time monitoring and intervention

### Integration
- **WhatsApp Integration**: Mobile interface for daily updates
- **REST API**: Full API for external integrations
- **Real-time Processing**: Live biometric analysis and alerts

## 📋 Requirements

### Environment Variables
```bash
# LLM Providers
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your_token
WHATSAPP_PHONE_ID=your_phone_id
WHATSAPP_BUSINESS_ID=your_business_id
WHATSAPP_WEBHOOK_TOKEN=auren_biometric_secure_2024

# Biometric Thresholds
PTOSIS_WARNING_THRESHOLD=6.5
PTOSIS_CRITICAL_THRESHOLD=7.0
INFLAMMATION_WARNING_THRESHOLD=3
INFLAMMATION_CRITICAL_THRESHOLD=4

# System Configuration
LOG_LEVEL=INFO
ENVIRONMENT=development
API_PORT=8000
```

### Python Dependencies
```bash
pip install -r requirements.txt
```

## 🏃‍♂️ Quick Start

1. **Clone and Setup**
```bash
git clone <repository>
cd auren
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
cp .env.template .env
# Edit .env with your API keys
```

3. **Start AUREN 2.0**
```bash
python start_auren.py
```

4. **Access the System**
- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 📚 API Endpoints

### Core Protocols
```bash
# Create protocol entry
POST /api/protocols/{protocol}/entry
{
  "type": "peptide_dose",
  "data": {
    "compound": "Retatrutide",
    "dose": 2.4,
    "unit": "mg"
  }
}
```

### Biometric Analysis
```bash
# Analyze biometric data
POST /api/biometric/analyze
{
  "image_path": "/path/to/photo.jpg"
}
```

### Convergence Analysis
```bash
# Analyze correlations
POST /api/convergence/analyze
{
  "source": "journal",
  "data": {
    "type": "peptide_dose",
    "compound": "BPC-157"
  }
}
```

### AI Crew Processing
```bash
# Process with AI agents
POST /api/crew/process
{
  "type": "daily_update",
  "query": "Analyze my recent biometric trends"
}
```

### RAG Queries
```bash
# Query the RAG system
POST /api/rag/query
{
  "query": "How has my ptosis changed over the last week?",
  "context": {"user_id": "123"},
  "urgency": "normal"
}
```

### WhatsApp Integration
```bash
# Send WhatsApp message
POST /api/whatsapp/send
{
  "to": "+1234567890",
  "message": "Your daily reminder is ready!",
  "type": "text"
}
```

## 🔧 System Architecture

### Directory Structure
```
auren/
├── src/
│   ├── protocols/          # Journal, MIRAGE, VISOR protocols
│   ├── biometric/          # Analysis and correlation tools
│   ├── agents/            # CrewAI agent implementations
│   ├── rag/              # Agentic RAG system
│   ├── integrations/      # WhatsApp and external APIs
│   └── app.py            # Main application
├── data/                 # Persistent data storage
├── logs/                 # System logs
├── config/              # Configuration files
└── tests/               # Test suite
```

### Core Components

#### 1. Protocol System
- **Journal Protocol**: Tracks peptide dosing, weight, nutrition
- **MIRAGE Protocol**: Analyzes facial biometrics (ptosis, inflammation)
- **VISOR Protocol**: Manages media files and documentation

#### 2. Biometric Analysis
- Facial landmark detection
- Ptosis scoring (0-10 scale)
- Inflammation assessment (0-5 scale)
- Symmetry analysis
- Lymphatic fullness tracking

#### 3. Agentic RAG
- **Naive**: Simple one-shot retrieval
- **Advanced**: Query expansion and re-ranking
- **Corrective**: Quality checking and correction
- **Agentic**: Full reasoning loop with planning

#### 4. CrewAI Agents
- **AUREN UI**: Main coordinator agent
- **Visual Analyst**: Biometric analysis specialist
- **Peptide Specialist**: Protocol optimization expert
- **Convergence Analyst**: Cross-protocol correlation expert

#### 5. Alert Management
- Real-time biometric monitoring
- Protocol-defined thresholds
- Intervention recommendations
- WhatsApp notifications

## 📊 Usage Examples

### Daily Biometric Check-in
1. User sends morning photos via WhatsApp
2. System analyzes facial biometrics
3. MIRAGE protocol creates entry with scores
4. Alert system checks for issues
5. CrewAI agents provide recommendations

### Peptide Protocol Management
1. User logs peptide dose via WhatsApp
2. Journal protocol records the entry
3. Convergence analysis correlates with visual data
4. System provides protocol adjustments
5. RAG system retrieves relevant historical data

### Weekly Analysis
1. System aggregates 7 days of data
2. CrewAI agents perform comprehensive analysis
3. Convergence analysis identifies patterns
4. System generates detailed report
5. WhatsApp delivers insights to user

## 🔍 Monitoring and Alerts

### Biometric Thresholds
- **Ptosis Warning**: ≥6.5 (add 600kcal refeed)
- **Ptosis Critical**: ≥7.0 (implement full recovery)
- **Inflammation Warning**: ≥3 (anti-inflammatory protocol)
- **Inflammation Critical**: ≥4 (medical review recommended)

### Alert Types
- **Info**: Positive milestones and achievements
- **Warning**: Elevated biometrics requiring attention
- **Critical**: Immediate intervention required

## 🛠️ Development

### Running Tests
```bash
pytest tests/
```

### Adding New Protocols
1. Create protocol class in `src/protocols/`
2. Implement required methods
3. Add to protocol registry in `app.py`
4. Create corresponding API endpoints

### Extending Biometric Analysis
1. Add new analysis methods to `BiometricAnalyzer`
2. Update scoring algorithms
3. Add new alert thresholds
4. Update WhatsApp formatting

## 📈 Performance

### System Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB for data and logs
- **Network**: Stable internet for API calls

### Optimization Tips
- Use SSD storage for vector database
- Configure Redis for caching
- Monitor API rate limits
- Implement proper logging rotation

## 🔒 Security

### API Security
- Environment variable protection
- Input validation on all endpoints
- Rate limiting for public endpoints
- Webhook signature verification

### Data Privacy
- Local data storage by default
- Encrypted API communications
- Secure WhatsApp webhook handling
- Audit logging for all operations

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Submit pull request
5. Ensure all tests pass

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the API documentation at `/docs`
- Review system logs in `/auren/logs/`
- Open an issue on GitHub
- Contact the development team

---

**AUREN 2.0** - Advanced biometric optimization through intelligent AI coordination. 