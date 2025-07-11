# AUREN 2.0 Production Readiness - Cursor Instructions

## 🎯 OBJECTIVE
Transform AUREN 2.0 from 85% to 95% production readiness by resolving all dependency conflicts and implementing architectural improvements.

## 📋 TASK LIST

### TASK 1: Create Directory Structure
Create the following directories if they don't exist:
```
/auren/CURSOR_INSTRUCTIONS/
/auren/src/core/
/auren/src/utils/
/auren/requirements/
/auren/scripts/
```

### TASK 2: Resolve Dependencies
1. Create `/auren/scripts/resolve_dependencies.sh` with the content from `dependency-resolution` artifact
2. Make it executable: `chmod +x /auren/scripts/resolve_dependencies.sh`
3. Create `/auren/requirements/` structure:
   - `base.txt` - Core dependencies only
   - `ai.txt` - AI/ML dependencies
   - `dev.txt` - Development dependencies
   - `prod.txt` - Production dependencies

### TASK 3: Implement Core Module
Create these files in `/auren/src/core/`:
1. `__init__.py` - Core module initialization (from architecture-improvements artifact)
2. `config.py` - Centralized configuration management
3. `exceptions.py` - Custom exception classes

### TASK 4: Add Dependency Checker
Create `/auren/src/utils/dependency_check.py` with runtime dependency verification

### TASK 5: Update Main Application
Update `/auren/src/app.py` to include dependency checking on startup

### TASK 6: Update CI/CD Pipeline
Replace `/auren/.github/workflows/ci.yml` with the updated pipeline configuration

### TASK 7: Create Documentation
Create `/auren/CURSOR_INSTRUCTIONS/implementation_log.md` to track what was done

## 📝 STEP-BY-STEP IMPLEMENTATION

### Step 1: Dependency Resolution Files

Create `/auren/requirements/base.txt`:
```
# Core framework dependencies
fastapi==0.109.0
uvicorn==0.27.0
pydantic>=2.6.1
python-multipart==0.0.6
python-dotenv==1.0.0
PyYAML==6.0.1
numpy==1.26.3
scipy==1.11.4
requests==2.31.0
aiohttp==3.9.1
```

Create `/auren/requirements/ai.txt`:
```
# AI/ML dependencies (flexible versions)
crewai==0.30.11
crewai-tools==0.2.6
openai==1.12.0
sentence-transformers>=2.3.0
chromadb  # Let pip resolve
sqlalchemy  # Let pip resolve
faiss-cpu>=1.7.4
```

Create `/auren/requirements/cv.txt`:
```
# Computer Vision dependencies
opencv-python-headless==4.9.0.80
mediapipe==0.10.9
```

Create `/auren/requirements/dev.txt`:
```
# Development dependencies
pytest==7.4.4
pytest-cov==4.1.0
pytest-asyncio==0.23.3
pytest-mock==3.12.0
mypy==1.8.0
black==23.12.1
isort==5.13.2
flake8==7.0.0
bandit[toml]==1.7.6
```

Create `/auren/requirements/prod.txt`:
```
-r base.txt
-r ai.txt
-r cv.txt
prometheus-client==0.19.0
structlog==24.1.0
```

### Step 2: Run Dependency Resolution
```bash
cd /auren
./scripts/resolve_dependencies.sh
```

### Step 3: Verify All Tests Pass
```bash
pytest tests/ -v
```

### Step 4: Update requirements.txt
```bash
# After successful resolution
cp requirements.lock requirements.txt
```

### Step 5: Commit Changes
```bash
git add .
git commit -m "feat: resolve dependency conflicts and improve architecture

- Implement layered dependency management
- Add comprehensive dependency resolution script  
- Create core module with centralized config
- Add runtime dependency verification
- Update CI/CD pipeline with staged checks
- Split requirements into logical groups
- Add requirements.lock for production builds

Resolves: dependency conflicts between CrewAI ecosystem
Improves: system architecture and maintainability  
Status: 95% production ready"

git push
```

## ✅ VERIFICATION CHECKLIST

After implementation, verify:
- [ ] All dependency conflicts resolved
- [ ] `pip install -r requirements.txt` completes without errors
- [ ] All tests pass: `pytest tests/`
- [ ] No security issues: `bandit -r src/`
- [ ] Type checking passes: `mypy src/`
- [ ] Application starts: `python start_auren.py`

## 🎯 SUCCESS CRITERIA

The implementation is successful when:
1. No dependency conflict warnings during installation
2. All 5 integration tests pass (up from 4/5)
3. Security scan shows 0 high, 0 medium issues
4. Application starts without import errors
5. CI/CD pipeline passes all checks

## 📊 EXPECTED RESULTS

| Metric | Before | After |
|--------|--------|-------|
| Production Readiness | 85% | 95% |
| Integration Tests | 4/5 | 5/5 |
| Security Issues | 0 | 0 |
| Dependency Conflicts | 3 | 0 |
| Architecture Score | B | A |

## 🚨 IMPORTANT NOTES

1. **DO NOT** pin chromadb or sqlalchemy versions in the final requirements
2. **DO** use requirements.lock for production deployments
3. **ALWAYS** run tests after dependency changes
4. **BACKUP** current requirements.txt before changes

## 💡 TROUBLESHOOTING

If dependency resolution fails:
1. Try removing the virtual environment and starting fresh
2. Check for conflicting global packages
3. Use `pip install --force-reinstall` for stubborn packages
4. Consult the dependency compatibility matrix

## 📝 FINAL STEP

After successful implementation:
1. Document the new commit hash
2. Update `/auren/CLAUDE_STATUS_REPORT.md` with new status
3. Report back with verification results

---

**Cursor, please execute these instructions systematically and report the new commit hash upon completion.** 