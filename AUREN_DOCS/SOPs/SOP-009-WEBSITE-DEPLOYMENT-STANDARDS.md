# SOP-009: WEBSITE DEPLOYMENT STANDARDS

**Created**: July 31, 2025  
**Version**: 1.0  
**Owner**: Senior Engineer  
**Status**: ACTIVE - MANDATORY

---

## 🎯 **PURPOSE**

This SOP establishes professional website deployment standards to prevent deployment chaos, ensure reliability, and maintain stakeholder confidence.

---

## 🚨 **CRITICAL RULES**

### **Rule 1: Single Source of Truth**
- **ONLY** deploy from: `auren/dashboard_v2/`
- **NEVER** deploy from documentation or archive folders
- **ALL** website changes must be made in `auren/dashboard_v2/`

### **Rule 2: Mandatory Deployment Script**
- **ONLY** use: `scripts/deploy_website_professional.sh`
- **NEVER** do manual file transfers or ad-hoc deployment
- **ALWAYS** validate deployment success automatically

### **Rule 3: Validation Required**
- **EVERY** deployment must pass automatic validation
- **VERIFY** all 9 agents are live and displaying correctly
- **CONFIRM** expected content before marking deployment complete

---

## 🔧 **DEPLOYMENT PROCEDURE**

### **Pre-Deployment Checklist**
- [ ] Changes made only in `auren/dashboard_v2/`
- [ ] Local testing completed (if applicable)
- [ ] Git commit prepared with clear message
- [ ] Ready to validate deployment

### **Deployment Command**
```bash
# From project root:
./scripts/deploy_website_professional.sh
```

### **Expected Output**
```
🚀 PROFESSIONAL WEBSITE DEPLOYMENT
==================================
Date: [timestamp]
User: [username]

🔍 Validating source files...
✅ Source files validated

📤 Deploying to production server...
Target: /usr/share/nginx/html/
✅ Files uploaded successfully

🔍 Validating deployment (checking live website)...
✅ NUTROS confirmed live
✅ KINETOS confirmed live
✅ HYPERTROS confirmed live
✅ CARDIOS confirmed live
✅ SOMNOS confirmed live
✅ OPTICOS confirmed live
✅ ENDOS confirmed live
✅ AUREN confirmed live
✅ NEUROS (active agent) confirmed with emoji

🎉 DEPLOYMENT SUCCESSFUL!
✅ All 9 agents confirmed live at http://aupex.ai/agents/
✅ Website deployment completed successfully
```

### **Post-Deployment**
- [ ] Manually verify http://aupex.ai/agents/ shows all 9 agents
- [ ] Test NEUROS dashboard link works
- [ ] Update deployment documentation
- [ ] Git commit deployment confirmation

---

## 🏗️ **TECHNICAL DETAILS**

### **Deployment Target**
- **Server**: 144.126.215.218
- **Path**: `/usr/share/nginx/html/`
- **Protocol**: SCP with SSH key authentication
- **Validation**: HTTP content verification

### **Source Structure**
```
auren/dashboard_v2/           # MASTER SOURCE
├── index.html               # Homepage
├── agents/
│   ├── index.html           # Agents page (9 agents)
│   └── neuroscientist.html  # NEUROS dashboard
├── styles/                  # CSS files
└── js/                      # JavaScript files
```

### **Archive Location**
```
ARCHIVE/old_website_copies/  # Historical/duplicate files
└── [DO NOT DEPLOY FROM HERE]
```

---

## 🚫 **FORBIDDEN PRACTICES**

### **Never Do This:**
- ❌ Deploy from `AUPEX_WEBSITE_DOCUMENTATION/`
- ❌ Manual `scp` commands without validation
- ❌ Deploy without testing the script first
- ❌ Skip post-deployment verification
- ❌ Create new website copies in other directories

### **If Script Fails:**
1. **Check source files** in `auren/dashboard_v2/`
2. **Verify server connectivity** (ping 144.126.215.218)
3. **Check script permissions** (`chmod +x scripts/deploy_website_professional.sh`)
4. **Review script output** for specific error messages
5. **Manual verification** only as last resort

---

## 📊 **SUCCESS METRICS**

### **Deployment Standards:**
- **Time**: <5 minutes from start to validation
- **Success Rate**: 100% (script must pass validation)
- **Manual Intervention**: 0% (fully automated)
- **Post-deployment Issues**: 0% (validation prevents problems)

### **Website Standards:**
- **9 Agents**: All must be visible with correct names and emojis
- **NEUROS**: Must show as active with performance metrics
- **Coming Soon**: 8 agents with detailed professional descriptions
- **Links**: NEUROS dashboard link must work correctly

---

## 🔄 **MAINTENANCE**

### **Script Updates**
- **Owner**: Senior Engineer
- **Testing**: Required before any script modifications
- **Backup**: Keep previous version in git history
- **Documentation**: Update this SOP when script changes

### **Server Changes**
- **Coordinate**: With DevOps team for any nginx configuration changes
- **Update**: Script paths if server configuration changes
- **Test**: Deployment after any server maintenance

---

## 📞 **SUPPORT**

### **For Deployment Issues:**
1. **Check**: Script output for specific error messages
2. **Verify**: All source files are in correct location
3. **Test**: Manual `curl http://aupex.ai/agents/` to check live site
4. **Review**: This SOP for proper procedure

### **For Script Failures:**
1. **Permissions**: `ls -la scripts/deploy_website_professional.sh`
2. **Connectivity**: `ping 144.126.215.218`
3. **Source Files**: `ls -la auren/dashboard_v2/agents/index.html`
4. **Manual Recovery**: Only if script completely fails

---

**This SOP ensures professional, reliable website deployments with zero tolerance for the deployment chaos experienced previously.**

*Last Updated: July 31, 2025*  
*Next Review: August 31, 2025* 