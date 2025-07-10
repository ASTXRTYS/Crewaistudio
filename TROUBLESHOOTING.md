# 🔧 CrewAI Studio Troubleshooting Guide

This guide helps you resolve common startup and runtime issues with CrewAI Studio.

## 🚀 Quick Start (Recommended)

**Always use the robust startup script:**
```bash
./start_app.sh
```

This script automatically handles cache clearing, environment validation, and dependency checks.

## 🐛 Common Issues & Solutions

### 1. **Import Errors**

#### **Error:** `ModuleNotFoundError: No module named 'agents'`
**Solution:**
- Ensure you're running from the correct directory
- Use the startup script: `./start_app.sh`
- Or manually add this to the top of `app/app.py`:
```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```

#### **Error:** `ImportError: attempted relative import with no known parent package`
**Solution:**
- This is fixed by the sys.path manipulation above
- Clear Python cache: `find . -name "*.pyc" -delete && find . -name "__pycache__" -type d -exec rm -rf {} +`

### 2. **Pydantic V2 Compatibility Issues**

#### **Error:** `PydanticUserError: Field 'args_schema' defined on a base class was overridden`
**Solution:**
Run the validation script to check all tools:
```bash
python validate_tools.py
```

**Manual Fix Pattern:**
```python
# ❌ Wrong (missing type annotation):
class MyTool(BaseTool):
    args_schema = MyInputModel

# ✅ Correct (proper typing):
from typing import Type
from pydantic import BaseModel

class MyTool(BaseTool):
    name: str = "My Tool"
    description: str = "Tool description"
    args_schema: Type[BaseModel] = MyInputModel
```

### 3. **File Path Issues**

#### **Error:** `FileNotFoundError: [Errno 2] No such file or directory: 'img/crewai_logo.png'`
**Solution:**
- Use relative paths from the correct working directory
- Fixed in `app/app.py` line 117: `st.image("../img/crewai_logo.png")`

#### **Error:** `File does not exist: app/app.py`
**Solution:**
- Make sure you're in the project root directory
- Run: `cd ~/Downloads/CrewAI-Studio-main`
- Then use: `./start_app.sh`

### 4. **Cache-Related Issues**

#### **Symptoms:** Old code behavior persists after changes
**Solution:**
Clear Python cache before starting:
```bash
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
```

### 5. **Database/Tool Loading Issues**

#### **Error:** `KeyError: 'ReadPdfTextTool'` or similar tool not found
**Solution:**
1. Run tool validation: `python validate_tools.py`
2. Check `app/my_tools.py` for proper tool registration
3. Ensure all tool imports are working

## 🛡️ Prevention Checklist

### Before Making Changes:
- [ ] Run `python validate_tools.py` to check tools
- [ ] Clear Python cache if making import changes
- [ ] Test with `./start_app.sh` instead of manual commands

### When Adding New Tools:
- [ ] Use proper Pydantic V2 type annotations
- [ ] Add `args_schema: Type[BaseModel] = YourInputModel`
- [ ] Type class attributes: `name: str = "..."`
- [ ] Test import with validation script

### When Moving/Renaming Files:
- [ ] Update all import statements
- [ ] Update `TOOL_CLASSES` registry in `my_tools.py`
- [ ] Test with `./start_app.sh`

## 🔍 Diagnostic Commands

### Check if app is running:
```bash
ps aux | grep streamlit | grep -v grep
```

### Check specific port:
```bash
curl -I http://localhost:8501
curl -I http://localhost:8502
curl -I http://localhost:8503
```

### Test basic Streamlit functionality:
```bash
echo 'import streamlit as st; st.title("Test")' > test.py
streamlit run test.py
rm test.py
```

### Validate all tools:
```bash
python validate_tools.py
```

## 📋 Environment Requirements

### Python Version:
- Python 3.11+ recommended
- Virtual environment active

### Critical Files:
- `app/app.py` - Main application
- `agents/my_agent.py` - Agent definitions
- `utils.py` - Utility functions
- `img/crewai_logo.png` - Logo image

### Port Usage:
- Default: 8501
- Alternative: 8502, 8503
- Check with: `lsof -i :8501`

## 🆘 Emergency Recovery

If nothing works:

1. **Full Reset:**
```bash
cd ~/Downloads/CrewAI-Studio-main
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
./start_app.sh
```

2. **Manual Startup:**
```bash
cd ~/Downloads/CrewAI-Studio-main
source the/bin/activate  # or your venv
cd app
python -c "import streamlit; print('Streamlit OK')"
python -c "import app; print('App imports OK')"
streamlit run app.py
```

3. **Test Individual Components:**
```bash
python validate_tools.py
python -c "from agents.my_agent import MyAgent; print('Agent OK')"
python -c "from my_tools import TOOL_CLASSES; print('Tools OK')"
```

## 📞 Getting Help

If issues persist:
1. Run all diagnostic commands above
2. Share error messages and output
3. Include your operating system and Python version
4. Mention which startup method you used

---
*Last updated: 2025-01-09 - After successful resolution of import/Pydantic issues* 