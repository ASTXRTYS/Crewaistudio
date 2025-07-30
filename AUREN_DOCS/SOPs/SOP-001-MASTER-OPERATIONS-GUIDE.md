# SOP-001: AUREN MASTER OPERATIONS GUIDE

**Version**: 1.0  
**Last Updated**: January 30, 2025  
**Status**: ✅ LOCKED CONFIGURATION - PRODUCTION READY
**Critical**: This is the definitive operations guide for the AUREN system.

---

## 🎯 PRIMARY REFERENCE

**TECHNICAL SPECIFICATION**: See `SOP-003-AUREN-MASTER-TECHNICAL-SPECIFICATION.md` for all architecture, configuration, and data flow details.

---

## 1. Daily Operations & Monitoring

### Morning Health Check
1.  **SSH to Server**:
    ```bash
    sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218
    ```
2.  **Run Comprehensive Health Script**:
    ```bash
    /root/monitor-auren.sh
    ```
3.  **Expected Output**:
    - All containers `Up`
    - NEUROS and Biometric health endpoints return success.
    - Disk usage below 90%.

### Quick Status Verification
1.  **Verify PWA Accessibility**:
    ```bash
    curl https://auren-omacln1ad-jason-madrugas-projects.vercel.app/
    # Should return HTML, not an authentication page.
    ```
2.  **Verify NEUROS via Proxy**:
    ```bash
    curl https://auren-omacln1ad-jason-madrugas-projects.vercel.app/api/neuros/health
    # Should return: {"status":"healthy","service":"neuros-advanced"}
    ```

## 2. Deployment Runbook

### Frontend Deployment Process (PWA)

#### Step-by-Step Deployment
1.  **Prepare Code**:
    ```bash
    cd auren-pwa
    git pull origin main # Or your feature branch
    npm install
    npm run build  # Test build locally before deploying
    ```
2.  **Deploy to Production**:
    ```bash
    vercel --prod --public
    ```
3.  **Verify Deployment**:
    - Check the new deployment URL in the Vercel CLI output.
    - Run the "Quick Status Verification" checks above.
    - Send a test message through the PWA interface.

#### Rollback Procedure
1.  **List Recent Deployments**:
    ```bash
    vercel ls
    ```
2.  **Rollback to a Previous Working Deployment**:
    ```bash
    vercel rollback [deployment-url-from-list]
    ```

### Backend Deployment Process

#### Container Updates
1.  **Build New Image** (if required):
    ```bash
    # On the server, in the relevant directory
    docker build -t neuros-advanced:new-version .
    ```
2.  **Stop and Remove the Old Container**:
    ```bash
    docker stop neuros-advanced
    docker rm neuros-advanced
    ```
3.  **Start the New Container**:
    ```bash
    docker run -d --name neuros-advanced \
      --network auren-network \
      -p 8000:8000 \
      -e REDIS_URL=redis://auren-redis:6379 \
      -e POSTGRES_URL=postgresql://auren_user:[PASSWORD]@auren-postgres:5432/auren_production \
      -e KAFKA_BOOTSTRAP_SERVERS=auren-kafka:9092 \
      neuros-advanced:new-version
    ```
4.  **Verify Health**:
    ```bash
    docker logs neuros-advanced --tail 20
    curl http://localhost:8000/health
    ```

#### Database Updates
1.  **Backup the Database First**:
    ```bash
    docker exec auren-postgres pg_dump -U auren_user auren_production > backup_$(date +%Y%m%d).sql
    ```
2.  **Apply Migrations**:
    ```bash
    docker exec -i auren-postgres psql -U auren_user auren_production < migration.sql
    ```

## 3. Emergency & Troubleshooting

### Issue: PWA Can't Connect or Shows Errors
1.  **Check Browser Console**: Look for network errors (404, 502, CORS).
2.  **Verify Vercel Proxy**: Test the proxy health endpoints directly (see "Quick Status Verification"). A 502 error means the backend is down.
3.  **Check Backend Health**: Use `/root/monitor-auren.sh` on the server.

### Issue: NEUROS Not Responding
1.  **Check Container**: `docker ps | grep neuros-advanced`
2.  **Check Logs**: `docker logs neuros-advanced --tail 50`
3.  **Restart**: `docker restart neuros-advanced`

### Issue: Disk Full
1.  **Check Usage**: `df -h`
2.  **Clean Docker Resources**: `docker system prune -a`
3.  **Remove Old Logs**: `find /var/log -type f -mtime +30 -delete`

### Complete System Recovery
Refer to the emergency restoration commands in `SOP-003-AUREN-MASTER-TECHNICAL-SPECIFICATION.md`.

---

**END OF SOP-001** 