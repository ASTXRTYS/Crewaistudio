# Health Tracking Agent Setup Guide

## 🎯 Overview
This guide shows you how to build an AI agent in CrewAI Studio that:
1. Receives health data via Telegram
2. Parses structured health information
3. Maintains a persistent PDF journal
4. Stores data in JSON for long-term tracking
5. Returns updated files to users

## 🛠️ Tools Available

### ✅ Custom Tools Created:
1. **TelegramBotTool** - Handle Telegram messaging
2. **HealthDataParserTool** - Parse natural language health data
3. **PDFJournalTool** - Manage persistent PDF journals
4. **CustomFileWriteTool** - Store JSON data (already available)

### ✅ Existing Tools You Can Use:
- **JSONSearchTool** - Query your health data
- **PDFSearchTool** - Search through journal entries
- **CustomApiTool** - Connect to external health APIs

## 🚀 Step-by-Step Setup

### Step 1: Create Telegram Bot
1. **Message @BotFather** on Telegram
2. **Create new bot**: `/newbot`
3. **Get bot token** and save it
4. **Set environment variable**:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   ```

### Step 2: Create Health Tracking Agent

#### Agent Configuration:
```json
{
  "name": "Health Tracker Agent",
  "role": "Health data processor and journal manager",
  "goal": "Parse health messages, update PDF journal, and maintain JSON database",
  "backstory": "Expert health data analyst with experience in fitness tracking and journal management",
  "verbose": true,
  "allow_delegation": false
}
```

#### Tools to Assign:
1. **HealthDataParserTool** - Parse incoming messages
2. **PDFJournalTool** - Manage PDF journal
3. **CustomFileWriteTool** - Store JSON data
4. **TelegramBotTool** - Send responses and files
5. **JSONSearchTool** - Query historical data

### Step 3: Create Tasks

#### Task 1: Parse Health Data
```json
{
  "description": "Parse incoming Telegram message for health data (weight, calories, macros, workouts, fasting)",
  "expected_output": "Structured health data with confidence score",
  "tools": ["HealthDataParserTool"]
}
```

#### Task 2: Update PDF Journal
```json
{
  "description": "Append parsed health data to persistent PDF journal",
  "expected_output": "Updated PDF journal file path",
  "tools": ["PDFJournalTool"]
}
```

#### Task 3: Store JSON Data
```json
{
  "description": "Store parsed data in JSON file for long-term tracking",
  "expected_output": "JSON file path with appended data",
  "tools": ["CustomFileWriteTool"]
}
```

#### Task 4: Send Response
```json
{
  "description": "Send updated PDF journal back to user via Telegram",
  "expected_output": "Confirmation of file sent",
  "tools": ["TelegramBotTool"]
}
```

### Step 4: Create Crew
```json
{
  "name": "Health Tracking Crew",
  "agents": ["Health Tracker Agent"],
  "tasks": ["Parse Health Data", "Update PDF Journal", "Store JSON Data", "Send Response"],
  "verbose": true,
  "process": "sequential"
}
```

## 📝 Message Format Examples

### Supported Health Data:
```
Weight: 75.5 kg
Calories: 2100
Protein: 150g
Carbs: 200g
Fat: 70g
Workout: Upper body - bench press, rows, shoulder press
Fasting: 16 hours
Sleep: 7.5 hours
Steps: 8500
Water: 2.5 liters
```

### Natural Language Examples:
- "Today I weighed 75.5 kg, ate 2100 calories with 150g protein"
- "Workout: Upper body - bench press 3x8, rows 3x10"
- "Fasted for 16 hours, slept 7.5 hours, walked 8500 steps"

## 🔧 Configuration Files

### Environment Variables (.env):
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
OPENAI_API_KEY=your_openai_key_here
```

### Journal Configuration:
- **PDF Location**: `journals/` directory
- **JSON Data**: `health_data.json`
- **Metadata**: `journals/{journal_name}_metadata.json`

## 📊 Data Structure

### Parsed Health Data:
```json
{
  "timestamp": "2025-07-06T22:30:00",
  "user_id": "telegram_user_id",
  "raw_message": "Weight: 75.5 kg, calories: 2100",
  "parsed_data": {
    "weight": "75.5 kg",
    "calories": "2100"
  },
  "confidence_score": 0.8
}
```

### JSON Database Structure:
```json
{
  "entries": [
    {
      "id": "entry_001",
      "timestamp": "2025-07-06T22:30:00",
      "user_id": "telegram_user_id",
      "data": {
        "weight": "75.5 kg",
        "calories": "2100"
      }
    }
  ],
  "metadata": {
    "total_entries": 1,
    "last_updated": "2025-07-06T22:30:00"
  }
}
```

## 🎯 Usage Workflow

1. **User sends message** to Telegram bot
2. **Agent receives message** via TelegramBotTool
3. **Agent parses data** using HealthDataParserTool
4. **Agent updates PDF** using PDFJournalTool
5. **Agent stores JSON** using CustomFileWriteTool
6. **Agent sends PDF** back via TelegramBotTool

## 🔍 Advanced Features

### Query Historical Data:
```python
# Use JSONSearchTool to query past entries
"Show me my weight trend over the last 30 days"
"Find all workouts from last week"
"What's my average calorie intake?"
```

### PDF Journal Features:
- **Persistent state** - PDF grows over time
- **Metadata tracking** - Entry counts, dates
- **Formatted output** - Clean, readable entries
- **Search capability** - Find specific entries

### Extensibility:
- **Add new metrics** - Modify HealthDataParserTool patterns
- **Connect APIs** - Use CustomApiTool for external data
- **Multiple users** - Support different Telegram users
- **Data visualization** - Generate charts and graphs

## 🚨 Troubleshooting

### Common Issues:
1. **Telegram bot not responding** - Check bot token and permissions
2. **PDF not updating** - Verify journals directory permissions
3. **Data not parsing** - Check message format against patterns
4. **File not sending** - Ensure file paths are correct

### Debug Steps:
1. Check CrewAI Studio logs
2. Verify tool configurations
3. Test individual tools
4. Check file permissions

## 📈 Next Steps

1. **Deploy to production** - Set up webhook for Telegram
2. **Add data visualization** - Create charts and graphs
3. **Implement notifications** - Alert for missing entries
4. **Add goal tracking** - Monitor progress toward targets
5. **Export capabilities** - Generate reports and summaries

## 🔗 Resources

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [CrewAI Documentation](https://docs.crewai.com/)
- [ReportLab Documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [Health Data Standards](https://www.hl7.org/fhir/)

---

**Your health tracking agent is now ready to use!** 🎉 