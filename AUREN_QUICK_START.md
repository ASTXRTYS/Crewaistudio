# AUREN Quick Start Guide 🚀

**Run AUREN in 3 Simple Commands!**

## Prerequisites
- Docker Desktop installed and running
- Python 3.11+ with virtual environment activated
- 4GB+ free RAM, 10GB+ free disk space

## Step 1: Start Infrastructure (1 command)
```bash
docker-compose -f docker-compose.dev.yml up -d
```
This starts:
- Redis (event streaming)
- PostgreSQL (memory & learning)
- LocalStack (S3 for archival)
- Grafana (optional metrics)

## Step 2: Start AUREN Services (1 command)
In separate terminal windows:

**Terminal 1 - Dashboard API:**
```bash
python auren/api/dashboard_api.py
```

**Terminal 2 - WebSocket Server:**
```bash
python auren/realtime/enhanced_websocket_streamer.py
```

## Step 3: See AUREN Think! (1 command)
```bash
python auren/demo/demo_neuroscientist.py --duration 2
```

## View the Magic ✨
Open your browser to: http://localhost:8000/dashboard

You'll see:
- 🧠 Real-time agent thinking process
- 💰 Live cost tracking
- 📈 Learning progress visualization
- 🫀 Biometric analysis in action

## Health Check
To verify everything is working:
```bash
python auren/utils/check_system_health.py
```

## Troubleshooting

**Docker not running?**
```bash
# Check Docker status
docker ps

# If not running, start Docker Desktop
```

**Port conflicts?**
```bash
# Check what's using ports
lsof -i :6379  # Redis
lsof -i :5432  # PostgreSQL
lsof -i :8000  # Dashboard API
lsof -i :8765  # WebSocket
```

**Missing dependencies?**
```bash
pip install -r auren/requirements.txt
```

## What You're Seeing

The demo simulates a stressed professional discovering they have low HRV (heart rate variability) and poor recovery. Watch as AUREN:

1. **Analyzes** their biometric patterns
2. **Forms hypotheses** about stress causes
3. **Designs interventions** personalized to their patterns
4. **Tracks progress** showing 40% HRV improvement
5. **Learns** from their unique responses

All in real-time on your dashboard!

## Next Steps

- Adjust demo duration: `--duration 5` for longer journey
- Check event streams in Redis: `redis-cli XLEN auren:events:critical`
- View Grafana metrics: http://localhost:3000 (admin/admin)
- Explore the API: http://localhost:8000/docs

---

**Welcome to AUREN** - Your AI health optimization companion that remembers everything and gets smarter over time! 🧠✨ 