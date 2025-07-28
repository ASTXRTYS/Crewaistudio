# AUPEX.AI MONITORING SETUP GUIDE

## Comprehensive Monitoring for the AUREN Website

This guide covers how to monitor the health, performance, and usage of aupex.ai.

---

## 📊 Current Monitoring Infrastructure

### 1. **Health Checks**

#### API Health Endpoint
```bash
# Check API health
curl http://aupex.ai/api/health

# Expected response:
{
  "status": "healthy",
  "components": {
    "protocols": "operational",
    "analyzer": "operational",
    "crew": "operational",
    "rag": "operational"
  }
}
```

#### Nginx Status
```bash
# SSH into server
ssh root@144.126.215.218

# Check nginx status
systemctl status nginx

# View nginx access logs
tail -f /var/log/nginx/access.log

# View nginx error logs
tail -f /var/log/nginx/error.log
```

#### Docker Container Health
```bash
# Check all containers
docker ps

# Check specific container logs
docker logs auren-api -f
docker logs auren-nginx -f

# Container health status
docker inspect auren-api | grep -A 5 "Health"
```

---

### 2. **Performance Monitoring**

#### Real-time Resource Usage
```bash
# CPU and Memory usage
docker stats

# Disk usage
df -h

# Network connections
netstat -tulpn | grep LISTEN
```

#### Database Performance
```bash
# PostgreSQL connections
docker exec postgres psql -U auren_user -d auren_db -c "SELECT count(*) FROM pg_stat_activity;"

# Redis memory usage
docker exec redis redis-cli INFO memory

# ChromaDB status
curl http://localhost:8001/api/v1/heartbeat
```

---

### 3. **Application Logs**

#### Centralized Log Viewing
```bash
# View all logs from docker-compose
cd /root/auren-production
docker-compose logs -f

# Filter by service
docker-compose logs -f auren-api
docker-compose logs -f nginx
```

#### Log Rotation Status
```bash
# Check log rotation config
cat /etc/logrotate.d/auren

# Manual log rotation
logrotate -f /etc/logrotate.d/auren
```

---

## 🎯 Setting Up Monitoring Tools

### 1. **Uptime Monitoring (UptimeRobot)**

Free external monitoring service setup:

1. Visit https://uptimerobot.com
2. Create free account
3. Add monitors:
   - **Main Website**: http://aupex.ai
   - **API Health**: http://aupex.ai/api/health
   - **WebSocket**: ws://aupex.ai/ws (custom)

Settings:
- Check interval: 5 minutes
- Alert contacts: Your email/SMS
- Keywords to check: "operational"

### 2. **Browser-Based Monitoring**

#### Chrome DevTools Monitoring
```javascript
// Paste in console to monitor WebSocket
const ws = new WebSocket('ws://aupex.ai/ws/dashboard/monitor');
ws.onmessage = (e) => console.log('WS Update:', JSON.parse(e.data));
ws.onerror = (e) => console.error('WS Error:', e);
ws.onclose = () => console.warn('WS Closed');

// Monitor API performance
setInterval(async () => {
  const start = Date.now();
  const res = await fetch('http://aupex.ai/api/health');
  const time = Date.now() - start;
  console.log(`API Response: ${time}ms`);
}, 60000);
```

### 3. **Server Monitoring Script**

Create `/root/monitor_auren.sh`:
```bash
#!/bin/bash

LOG="/var/log/auren-monitor.log"

# Function to check service
check_service() {
    if curl -s -f "$1" > /dev/null; then
        echo "$(date): $2 - OK" >> $LOG
    else
        echo "$(date): $2 - FAILED" >> $LOG
        # Send alert (configure your method)
        # mail -s "AUREN Alert: $2 Failed" admin@example.com
    fi
}

# Check services
check_service "http://localhost/api/health" "API"
check_service "http://localhost/" "Website"

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): Disk usage high: $DISK_USAGE%" >> $LOG
fi

# Check memory
MEM_FREE=$(free -m | awk 'NR==2 {print $4}')
if [ $MEM_FREE -lt 500 ]; then
    echo "$(date): Low memory: ${MEM_FREE}MB free" >> $LOG
fi
```

Make executable and add to cron:
```bash
chmod +x /root/monitor_auren.sh

# Add to crontab (every 5 minutes)
crontab -e
*/5 * * * * /root/monitor_auren.sh
```

---

## 📈 Metrics to Monitor

### 1. **Website Performance**
- Page load time (target: <2s)
- Time to first byte (TTFB)
- 3D animation FPS
- JavaScript errors

### 2. **API Performance**
- Response time per endpoint
- Error rate
- Request volume
- WebSocket connection count

### 3. **Infrastructure Metrics**
- CPU usage (alert >80%)
- Memory usage (alert >80%)
- Disk space (alert >80%)
- Network bandwidth

### 4. **Business Metrics**
- Daily active users
- API calls per hour
- Error rates by type
- Feature usage stats

---

## 🔔 Alert Configuration

### Email Alerts Setup
```bash
# Install mail utilities
apt-get install mailutils

# Configure email
echo "auren-alert@aupex.ai" > /root/.forward

# Test email
echo "Test alert" | mail -s "AUREN Test" your-email@example.com
```

### Slack Webhook Alerts
```bash
# Add to monitoring script
send_slack_alert() {
    curl -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"$1\"}" \
    YOUR_SLACK_WEBHOOK_URL
}
```

### Discord Webhook Alerts
```bash
send_discord_alert() {
    curl -X POST -H "Content-Type: application/json" \
    -d "{\"content\": \"$1\"}" \
    YOUR_DISCORD_WEBHOOK_URL
}
```

---

## 📊 Dashboard Creation

### Simple HTML Dashboard
Create `/usr/share/nginx/html/monitor.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <title>AUREN Monitor</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        .metric { display: inline-block; margin: 20px; padding: 20px; border: 1px solid #ddd; }
        .ok { background: #90EE90; }
        .error { background: #FFB6C1; }
    </style>
</head>
<body>
    <h1>AUREN System Monitor</h1>
    <div id="metrics"></div>
    
    <script>
    async function checkHealth() {
        const metrics = document.getElementById('metrics');
        metrics.innerHTML = '';
        
        // Check API
        try {
            const res = await fetch('/api/health');
            const data = await res.json();
            metrics.innerHTML += `<div class="metric ok">API: ${data.status}</div>`;
        } catch (e) {
            metrics.innerHTML += `<div class="metric error">API: Error</div>`;
        }
        
        // Check WebSocket
        const ws = new WebSocket('ws://aupex.ai/ws/dashboard/monitor');
        ws.onopen = () => {
            metrics.innerHTML += `<div class="metric ok">WebSocket: Connected</div>`;
            ws.close();
        };
        ws.onerror = () => {
            metrics.innerHTML += `<div class="metric error">WebSocket: Error</div>`;
        };
    }
    
    checkHealth();
    setInterval(checkHealth, 30000);
    </script>
</body>
</html>
```

---

## 🕒 Historical Data Collection

### Setup Basic Metrics Collection
```bash
# Create metrics collection script
cat > /root/collect_metrics.sh << 'EOF'
#!/bin/bash

TIMESTAMP=$(date +%Y-%m-%d_%H:%M:%S)
METRICS_FILE="/var/log/auren-metrics.csv"

# Collect metrics
CPU=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
MEM=$(free -m | awk 'NR==2{printf "%.2f", $3*100/$2 }')
DISK=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
CONNECTIONS=$(netstat -an | grep :80 | wc -l)

# API response time
API_TIME=$(curl -o /dev/null -s -w %{time_total} http://localhost/api/health)

# Write to CSV
echo "$TIMESTAMP,$CPU,$MEM,$DISK,$CONNECTIONS,$API_TIME" >> $METRICS_FILE
EOF

chmod +x /root/collect_metrics.sh

# Add to cron (every minute)
echo "* * * * * /root/collect_metrics.sh" | crontab -
```

---

## 🚨 Incident Response

### Quick Diagnostics Commands
```bash
# Full system check
/root/auren-production/scripts/check_deployment.sh

# Service restart
docker-compose restart auren-api

# Emergency nginx restart
systemctl restart nginx

# Clear disk space
docker system prune -af
truncate -s 0 /var/log/nginx/*.log
```

### Monitoring Checklist
- [ ] API responding (http://aupex.ai/api/health)
- [ ] Website loading (http://aupex.ai)
- [ ] WebSocket connecting
- [ ] Database accessible
- [ ] Disk space available (>20%)
- [ ] Memory available (>500MB)
- [ ] No critical errors in logs

---

## 📱 Mobile Monitoring

### Android/iOS Shortcuts
Create shortcuts to quickly check:
- http://aupex.ai/api/health
- http://aupex.ai/monitor.html

### Telegram Bot (Optional)
```python
# Simple monitoring bot
import requests
import telebot

bot = telebot.TeleBot("YOUR_BOT_TOKEN")

@bot.message_handler(commands=['status'])
def check_status(message):
    try:
        r = requests.get('http://aupex.ai/api/health')
        if r.status_code == 200:
            bot.reply_to(message, "✅ AUREN is operational")
        else:
            bot.reply_to(message, "⚠️ Issue detected")
    except:
        bot.reply_to(message, "❌ AUREN is down")

bot.polling()
```

---

## 📊 Weekly Reports

### Generate Report Script
```bash
#!/bin/bash
# /root/weekly_report.sh

echo "AUREN Weekly Report - $(date)"
echo "========================"
echo ""
echo "Uptime:"
uptime
echo ""
echo "Disk Usage:"
df -h
echo ""
echo "Docker Status:"
docker ps
echo ""
echo "Error Count:"
grep -c ERROR /var/log/nginx/error.log
echo ""
echo "API Calls This Week:"
grep -c "GET /api" /var/log/nginx/access.log
```

---

## 🔧 Troubleshooting Monitoring Issues

### Common Issues:

1. **Monitoring script not running**
   - Check cron: `crontab -l`
   - Check script permissions: `ls -la /root/monitor_auren.sh`

2. **Alerts not sending**
   - Test mail: `echo "test" | mail -s "test" your@email.com`
   - Check webhook URLs

3. **Metrics not collecting**
   - Check disk space for logs
   - Verify script paths

---

*Remember: Good monitoring prevents downtime. Set it up once, check it regularly!*

*Last Updated: January 20, 2025* 