# SSH ACCESS STANDARD FOR AUREN
## Mandatory Use of sshpass for All Server Access

*Established: July 28, 2025*  
*Status: MANDATORY STANDARD*

---

## 🔐 OVERVIEW

All access to AUREN production servers MUST use `sshpass` for automated, scriptable deployments. This is the official standard established during the Biometric System deployment.

---

## 📦 INSTALLATION

### macOS
```bash
# Primary method
brew install hudochenkov/sshpass/sshpass

# Alternative if primary fails
brew install https://raw.githubusercontent.com/kadwanev/bigboybrew/master/Library/Formula/sshpass.rb
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install sshpass
```

### Linux (RHEL/CentOS)
```bash
sudo yum install epel-release
sudo yum install sshpass
```

---

## 🚀 USAGE PATTERNS

### Basic SSH Connection
```bash
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218
```

### Execute Remote Command
```bash
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 'docker ps'
```

### Copy Files to Server (SCP)
```bash
sshpass -p '.HvddX+@6dArsKd' scp -o StrictHostKeyChecking=no local_file.txt root@144.126.215.218:/remote/path/
```

### Copy Files from Server
```bash
sshpass -p '.HvddX+@6dArsKd' scp -o StrictHostKeyChecking=no root@144.126.215.218:/remote/file.txt ./local/
```

### Multi-line Commands (Here Document)
```bash
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 << 'ENDSSH'
echo "Running multiple commands"
docker ps
df -h
ENDSSH
```

---

## 💡 COMMON USE CASES

### 1. Check System Health
```bash
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 'curl -s http://localhost:8888/health | jq .'
```

### 2. View Docker Containers
```bash
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
```

### 3. Check Logs
```bash
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 'docker logs --tail 50 biometric-system-100'
```

### 4. Database Query
```bash
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 'docker exec -e PGPASSWORD=auren_secure_2025 auren-postgres psql -U auren_user -d auren_production -c "SELECT COUNT(*) FROM biometric_events;"'
```

---

## 🛡️ SECURITY CONSIDERATIONS

### DO's:
- ✅ Use sshpass in scripts for automation
- ✅ Store passwords in secure environment variables when possible
- ✅ Use `-o StrictHostKeyChecking=no` to avoid interactive prompts
- ✅ Limit sshpass usage to internal/development environments

### DON'Ts:
- ❌ Never commit passwords in scripts to version control
- ❌ Don't use sshpass on shared/public computers
- ❌ Avoid using in production without additional security layers
- ❌ Don't share sshpass commands in public forums

### Better Security Alternative (Future):
```bash
# Store password in environment variable
export SSHPASS='.HvddX+@6dArsKd'
sshpass -e ssh -o StrictHostKeyChecking=no root@144.126.215.218
```

---

## 📝 SCRIPT TEMPLATE

### Deployment Script Example
```bash
#!/bin/bash
# deploy.sh - Standard AUREN deployment script

# Configuration
SERVER_IP="144.126.215.218"
SSH_PASS='.HvddX+@6dArsKd'
SSH_USER="root"

# Function for SSH commands
execute_remote() {
    sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no "$SSH_USER@$SERVER_IP" "$1"
}

# Function for SCP
copy_to_server() {
    sshpass -p "$SSH_PASS" scp -o StrictHostKeyChecking=no "$1" "$SSH_USER@$SERVER_IP:$2"
}

# Example usage
echo "Checking server health..."
execute_remote "curl -s http://localhost:8888/health"

echo "Copying deployment file..."
copy_to_server "app.py" "/opt/auren_deploy/"

echo "Restarting service..."
execute_remote "docker restart biometric-system-100"
```

---

## 🚨 TROUBLESHOOTING

### sshpass: command not found
- Solution: Install sshpass using the installation commands above

### Host key verification failed
- Solution: Always use `-o StrictHostKeyChecking=no`

### Permission denied
- Solution: Verify password is correct and properly escaped

### Connection timeout
- Solution: Check server IP and firewall settings

---

## 📋 QUICK REFERENCE

### Essential Commands
```bash
# Connect to server
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218

# Run command
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 'command'

# Copy to server
sshpass -p '.HvddX+@6dArsKd' scp -o StrictHostKeyChecking=no file root@144.126.215.218:/path/

# Copy from server
sshpass -p '.HvddX+@6dArsKd' scp -o StrictHostKeyChecking=no root@144.126.215.218:/path/file ./
```

---

## ✅ COMPLIANCE CHECKLIST

When creating deployment scripts:
- [ ] Use sshpass for all SSH operations
- [ ] Include `-o StrictHostKeyChecking=no`
- [ ] Never hardcode passwords in committed files
- [ ] Test scripts locally before production use
- [ ] Document any special SSH requirements

---

## 📌 STANDARD ADOPTION

This standard was adopted on July 28, 2025, during the deployment of the AUREN Biometric System (Sections 1-8). All future deployments and automation scripts MUST follow this standard.

**Rationale**: Enables automated, non-interactive deployments essential for continuous integration and rapid iteration.

---

*This document defines the mandatory SSH access standard for all AUREN infrastructure.* 