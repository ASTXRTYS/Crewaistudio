# AI ASSISTANT OPERATIONAL RULES FOR AUREN

**Version**: 4.0  
**Last Updated**: July 31, 2025  
**Status**: ✅ PRODUCTION READY - Comprehensive Blueprint Deployed

---

## 🎯 PRIMARY DIRECTIVE: The Source of Truth Funnel

**ALWAYS START HERE**. This is the single entry point for all operations, ensuring every action is grounded in the most current strategic and technical reality.

1.  **START WITH THE MASTER BLUEPRINT (NEW SOURCE OF TRUTH)**:
    - Read `AUREN_DOCS/AUREN_MASTER_SYSTEM_BLUEPRINT_v22_COMPREHENSIVE.md`. This is the single source of truth for **what the system is, what it will become, and its current operational status**. It is a hybrid document combining strategic vision, technical reality, and documented implementation gaps.

2.  **CONSULT THE MASTER OPERATIONS GUIDE**:
    - Read `AUREN_DOCS/SOPs/SOP-001-AUREN-MASTER-OPERATIONS-GUIDE.md`. This is the single source of truth for **how to operate the system on a daily basis**.

3.  **REVIEW THE MASTER TECHNICAL SPECIFICATION**:
    - Read `AUREN_DOCS/SOPs/SOP-003-AUREN-MASTER-TECHNICAL-SPECIFICATION.md` for in-depth technical details on specific components.

4.  **CHECK CREDENTIALS**:
    - Reference `AUREN_DOCS/00_QUICK_START/CREDENTIALS_VAULT.md` for all access.

---

## 📋 OPERATIONAL RULES (LOCKED CONFIGURATION)

### Rule 1: Trust the Master Blueprint
- **ALWAYS** reference the `AUREN_MASTER_SYSTEM_BLUEPRINT_v22_COMPREHENSIVE.md` as the primary source of truth.
- **NEVER** deviate from the documented architecture or procedures.
- **UPDATE** documentation if a change is approved by the Lead Architect.

### Rule 2: Access Standards
- **ALL** server access **MUST** use `sshpass` as documented in `SSH_ACCESS_STANDARD.md`.
- **NEVER** use plain SSH.

### Rule 3: Git Branch Management
- **CREATE** new branches for all feature work.
- **NEVER** work directly on `main` without explicit permission.
- **COMMIT** frequently with clear messages.

### Rule 4: Post-Implementation Protocol (CRITICAL)
1.  **VERIFY**: Use the `SYSTEM_VERIFICATION_CHECKLIST.md` after every deployment.
2.  **LOG**: Update the `CHANGELOG.md` with a summary of the changes.
3.  **UPDATE**: If any part of the locked configuration was changed (with approval), update the master SOPs and the Master Blueprint.

---

## 🚀 QUICK REFERENCE PATHS (UPDATED)

```
# --------------------------------------------------
#          LOCKED CONFIGURATION - DO NOT CHANGE
# --------------------------------------------------

# MASTER SOURCE OF TRUTH (WHAT THE SYSTEM IS & WILL BECOME)
Master Blueprint:   /AUREN_DOCS/AUREN_MASTER_SYSTEM_BLUEPRINT_v22_COMPREHENSIVE.md

# MASTER OPERATIONS GUIDE (HOW TO RUN THE SYSTEM)
Operations:         /AUREN_DOCS/SOPs/SOP-001-AUREN-MASTER-OPERATIONS-GUIDE.md

# MASTER TECHNICAL SPECIFICATION (DEEP DIVE)
Technical Specs:    /AUREN_DOCS/SOPs/SOP-003-AUREN-MASTER-TECHNICAL-SPECIFICATION.md

# SYSTEM STATUS & VERIFICATION
System Status:      /AUREN_DOCS/CURRENT_SYSTEM_STATE.md
Verification:       /AUREN_DOCS/SYSTEM_VERIFICATION_CHECKLIST.md
Change History:     /AUREN_DOCS/CHANGELOG.md

# CREDENTIALS & ACCESS
All Passwords:      /AUREN_DOCS/00_QUICK_START/CREDENTIALS_VAULT.md
SSH Standard:       /AUREN_DOCS/00_QUICK_START/SSH_ACCESS_STANDARD.md

# LIVE SYSTEM
PWA URL:            https://auren-omacln1ad-jason-madrugas-projects.vercel.app
Monitoring Script:  /root/monitor-auren.sh (on server)
```

---

## ⚡ GOLDEN RULES (UPDATED)

1.  **TRUST THE MASTER BLUEPRINT** - Start with `AUREN_MASTER_SYSTEM_BLUEPRINT_v22_COMPREHENSIVE.md` and the master SOPs.
2.  **DOCUMENT EVERYTHING** - Update the `CHANGELOG.md` after every change.
3.  **VERIFY DEPLOYMENTS** - Use the `SYSTEM_VERIFICATION_CHECKLIST.md`.
4.  **SSHPASS ALWAYS** - No exceptions.
5.  **NEVER CHANGE LOCKED CONFIG** - Follow the documented procedures.
6.  **`vercel --prod --public`** - Always use this for PWA deployments.

---
*This rules file has been updated to reflect the final, locked configuration of the AUREN system. All previous versions are now obsolete.* 