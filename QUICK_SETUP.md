# CrewAI Studio Quick Setup Guide

## 🚀 Quick Start on Any Computer

### Prerequisites
- Python 3.9+ installed
- Git installed
- Internet connection

### Step 1: Clone Your Repository
```bash
git clone <YOUR_REPOSITORY_URL>
cd CrewAI-Studio-main
```

### Step 2: Set Up Virtual Environment
```bash
# On macOS/Linux:
./install_venv.sh

# On Windows:
install_venv.bat
```

### Step 3: Activate Virtual Environment
```bash
# On macOS/Linux:
source the/bin/activate

# On Windows:
the\Scripts\activate
```

### Step 4: Run CrewAI Studio
```bash
streamlit run app/app.py
```

### Step 5: Access Studio
Open your browser and go to: **http://localhost:8501**

## 📁 What's Included
- ✅ Complete CrewAI Studio setup
- ✅ Custom knowledge base (knowledge_base.json)
- ✅ All required dependencies
- ✅ Ready-to-use configuration

## 🔄 Syncing Changes
When you make changes on one computer:

```bash
# Commit your changes
git add .
git commit -m "Your changes description"
git push

# On another computer, pull the latest
git pull
```

## 🛠️ Troubleshooting
- If you get permission errors, run: `chmod +x *.sh`
- If Python version issues occur, ensure Python 3.9+ is installed
- If dependencies fail, try: `pip install -r requirements.txt`

## 📝 Notes
- Your knowledge base and configurations are preserved
- Database files are local (not synced) for security
- Virtual environment is recreated on each computer 