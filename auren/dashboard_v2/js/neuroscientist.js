// Observability Integration - Real Metrics from AUREN
const METRICS_API = 'http://144.126.215.218:8002/api/metrics';
let metricsUpdateInterval;
let metricsWebSocket;

// Function to update real-time metrics
async function updateRealTimeMetrics(userId = 'demo') {
    try {
        // Fetch all metrics in one batch request
        const response = await fetch(`${METRICS_API}/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                metrics: [
                    'auren_hrv_rmssd_ms',
                    'auren_recovery_score',
                    'auren_sleep_debt_hours'
                ],
                user_id: userId,
                time_range: '1h'
            })
        });

        if (!response.ok) throw new Error('Failed to fetch metrics');
        
        const data = await response.json();
        
        // Update HRV
        const hrvData = data.results.find(r => r.metric === 'auren_hrv_rmssd_ms');
        if (hrvData && hrvData.data.length > 0) {
            const latestHRV = hrvData.data[hrvData.data.length - 1].value;
            document.getElementById('hrv-value').textContent = `${Math.round(latestHRV)}ms`;
            
            // Update HRV status
            const hrvStatus = document.getElementById('hrv-status');
            if (latestHRV < 20) {
                hrvStatus.textContent = '⚠️ Critical';
                hrvStatus.className = 'metric-status critical';
            } else if (latestHRV < 30) {
                hrvStatus.textContent = '⚡ Low';
                hrvStatus.className = 'metric-status warning';
            } else if (latestHRV > 100) {
                hrvStatus.textContent = '❓ Check';
                hrvStatus.className = 'metric-status elevated';
            } else {
                hrvStatus.textContent = '✅ Good';
                hrvStatus.className = 'metric-status good';
            }
            
            // Update HRV chart if exists
            updateHRVChart(hrvData.data);
        }
        
        // Update Recovery Score
        const recoveryData = data.results.find(r => r.metric === 'auren_recovery_score');
        if (recoveryData && recoveryData.data.length > 0) {
            const latestRecovery = recoveryData.data[recoveryData.data.length - 1].value;
            document.getElementById('recovery-value').textContent = `${Math.round(latestRecovery)}%`;
            
            // Update recovery status
            const recoveryStatus = document.getElementById('recovery-status');
            if (latestRecovery < 40) {
                recoveryStatus.textContent = '❌ Rest';
                recoveryStatus.className = 'metric-status critical';
            } else if (latestRecovery < 60) {
                recoveryStatus.textContent = '⚡ Low';
                recoveryStatus.className = 'metric-status warning';
            } else {
                recoveryStatus.textContent = '✅ Good';
                recoveryStatus.className = 'metric-status good';
            }
            
            // Update recovery chart
            updateRecoveryChart(recoveryData.data);
        }
        
        // Update Sleep Debt
        const sleepDebtData = data.results.find(r => r.metric === 'auren_sleep_debt_hours');
        if (sleepDebtData && sleepDebtData.data.length > 0) {
            const latestSleepDebt = sleepDebtData.data[sleepDebtData.data.length - 1].value;
            document.getElementById('sleep-debt-value').textContent = `${latestSleepDebt.toFixed(1)}h`;
            
            // Update sleep debt status
            const sleepDebtStatus = document.getElementById('sleep-debt-status');
            if (latestSleepDebt > 8) {
                sleepDebtStatus.textContent = '❌ Critical';
                sleepDebtStatus.className = 'metric-status critical';
            } else if (latestSleepDebt > 4) {
                sleepDebtStatus.textContent = '⚡ High';
                sleepDebtStatus.className = 'metric-status warning';
            } else {
                sleepDebtStatus.textContent = '✅ Good';
                sleepDebtStatus.className = 'metric-status good';
            }
            
            // Update sleep debt chart
            updateSleepDebtChart(sleepDebtData.data);
        }
        
    } catch (error) {
        console.error('Failed to update metrics:', error);
        // Show error state
        document.querySelectorAll('.metric-value').forEach(el => {
            if (el.id.includes('value')) el.textContent = '--';
        });
    }
}

// WebSocket for real-time updates
function connectMetricsWebSocket(userId = 'demo') {
    try {
        metricsWebSocket = new WebSocket('ws://144.126.215.218:8002/api/metrics/stream');
        
        metricsWebSocket.onopen = () => {
            console.log('Connected to metrics stream');
            // Subscribe to metrics
            metricsWebSocket.send(JSON.stringify({
                metrics: ['auren_hrv_rmssd_ms', 'auren_recovery_score', 'auren_sleep_debt_hours'],
                user_id: userId
            }));
        };
        
        metricsWebSocket.onmessage = (event) => {
            const update = JSON.parse(event.data);
            if (update.type === 'metric_update') {
                // Update specific metric in real-time
                switch(update.metric) {
                    case 'auren_hrv_rmssd_ms':
                        document.getElementById('hrv-value').textContent = `${Math.round(update.value)}ms`;
                        break;
                    case 'auren_recovery_score':
                        document.getElementById('recovery-value').textContent = `${Math.round(update.value)}%`;
                        break;
                    case 'auren_sleep_debt_hours':
                        document.getElementById('sleep-debt-value').textContent = `${update.value.toFixed(1)}h`;
                        break;
                }
            }
        };
        
        metricsWebSocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        metricsWebSocket.onclose = () => {
            console.log('WebSocket connection closed, reconnecting in 5s...');
            setTimeout(() => connectMetricsWebSocket(userId), 5000);
        };
        
    } catch (error) {
        console.error('Failed to connect WebSocket:', error);
    }
}

// 3D Avatar Animation
function init3DAvatar() {
    const container = document.getElementById('avatar-3d');
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    
    renderer.setSize(300, 300);
    container.appendChild(renderer.domElement);
    
    // Create brain-like structure
    const geometry = new THREE.IcosahedronGeometry(1, 4);
    const material = new THREE.MeshPhongMaterial({
        color: 0x00D9FF,
        wireframe: true,
        emissive: 0x00D9FF,
        emissiveIntensity: 0.2
    });
    
    const brain = new THREE.Mesh(geometry, material);
    scene.add(brain);
    
    // Add inner glow sphere
    const glowGeometry = new THREE.SphereGeometry(0.8, 32, 32);
    const glowMaterial = new THREE.MeshBasicMaterial({
        color: 0x9945FF,
        transparent: true,
        opacity: 0.3
    });
    const glow = new THREE.Mesh(glowGeometry, glowMaterial);
    scene.add(glow);
    
    // Lighting
    const light = new THREE.PointLight(0xffffff, 1, 100);
    light.position.set(5, 5, 5);
    scene.add(light);
    
    const ambientLight = new THREE.AmbientLight(0x404040);
    scene.add(ambientLight);
    
    camera.position.z = 3;
    
    // Animation
    function animate() {
        requestAnimationFrame(animate);
        brain.rotation.x += 0.005;
        brain.rotation.y += 0.01;
        glow.rotation.x -= 0.01;
        glow.rotation.y -= 0.005;
        renderer.render(scene, camera);
    }
    
    animate();
}

// 3D Knowledge Graph
function init3DKnowledgeGraph() {
    const container = document.getElementById('knowledge-graph');
    const width = container.clientWidth;
    const height = 400;
    
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);
    
    // Generate nodes
    const nodes = [];
    const nodeGeometry = new THREE.SphereGeometry(0.05, 16, 16);
    const nodeMaterial = new THREE.MeshPhongMaterial({ 
        color: 0x00D9FF,
        emissive: 0x00D9FF,
        emissiveIntensity: 0.5
    });
    
    for (let i = 0; i < 100; i++) {
        const node = new THREE.Mesh(nodeGeometry, nodeMaterial.clone());
        node.position.x = (Math.random() - 0.5) * 10;
        node.position.y = (Math.random() - 0.5) * 10;
        node.position.z = (Math.random() - 0.5) * 10;
        scene.add(node);
        nodes.push(node);
    }
    
    // Create connections
    const lineMaterial = new THREE.LineBasicMaterial({ 
        color: 0x00D9FF,
        transparent: true,
        opacity: 0.3
    });
    
    for (let i = 0; i < 200; i++) {
        const points = [];
        const node1 = nodes[Math.floor(Math.random() * nodes.length)];
        const node2 = nodes[Math.floor(Math.random() * nodes.length)];
        
        points.push(node1.position);
        points.push(node2.position);
        
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const line = new THREE.Line(geometry, lineMaterial);
        scene.add(line);
    }
    
    // Lighting
    const light = new THREE.PointLight(0xffffff, 1, 100);
    light.position.set(10, 10, 10);
    scene.add(light);
    
    const ambientLight = new THREE.AmbientLight(0x404040);
    scene.add(ambientLight);
    
    camera.position.z = 15;
    
    // Mouse controls
    let mouseX = 0;
    let mouseY = 0;
    
    container.addEventListener('mousemove', (event) => {
        const rect = container.getBoundingClientRect();
        mouseX = ((event.clientX - rect.left) / width) * 2 - 1;
        mouseY = -((event.clientY - rect.top) / height) * 2 + 1;
    });
    
    // Animation
    function animate() {
        requestAnimationFrame(animate);
        
        // Rotate based on mouse
        scene.rotation.y += (mouseX * 0.05 - scene.rotation.y) * 0.1;
        scene.rotation.x += (mouseY * 0.05 - scene.rotation.x) * 0.1;
        
        // Animate nodes
        nodes.forEach((node, i) => {
            node.material.emissiveIntensity = 0.3 + Math.sin(Date.now() * 0.001 + i) * 0.2;
        });
        
        renderer.render(scene, camera);
    }
    
    animate();
    
    // Update stats
    document.getElementById('node-count').textContent = nodes.length;
    document.getElementById('link-count').textContent = '200';
}

// Real-time Chart Updates
function initBiometricCharts() {
    // HRV Chart
    const hrvCanvas = document.getElementById('hrv-chart');
    const hrvCtx = hrvCanvas.getContext('2d');
    hrvCanvas.width = hrvCanvas.offsetWidth;
    hrvCanvas.height = 120;
    
    const hrvData = [];
    for (let i = 0; i < 50; i++) {
        hrvData.push(60 + Math.random() * 10);
    }
    
    function drawHRV() {
        hrvCtx.clearRect(0, 0, hrvCanvas.width, hrvCanvas.height);
        
        // Draw grid
        hrvCtx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        hrvCtx.lineWidth = 1;
        for (let i = 0; i < 5; i++) {
            hrvCtx.beginPath();
            hrvCtx.moveTo(0, i * 30);
            hrvCtx.lineTo(hrvCanvas.width, i * 30);
            hrvCtx.stroke();
        }
        
        // Draw line
        hrvCtx.strokeStyle = '#00D9FF';
        hrvCtx.lineWidth = 2;
        hrvCtx.beginPath();
        
        hrvData.forEach((value, i) => {
            const x = (i / hrvData.length) * hrvCanvas.width;
            const y = hrvCanvas.height - ((value - 50) / 30) * hrvCanvas.height;
            
            if (i === 0) {
                hrvCtx.moveTo(x, y);
            } else {
                hrvCtx.lineTo(x, y);
            }
        });
        
        hrvCtx.stroke();
        
        // Update data
        hrvData.shift();
        hrvData.push(60 + Math.random() * 10);
        
        // Update value
        document.querySelector('.metrics-grid .metric:first-child .metric-value').textContent = 
            Math.round(hrvData[hrvData.length - 1]) + 'ms';
    }
    
    setInterval(drawHRV, 100);
    
    // Similar setup for stress and fatigue charts...
}

// WebSocket connection for real-time updates
function initWebSocket() {
    // Simulate WebSocket updates
    setInterval(() => {
        // Update status
        const status = document.getElementById('status');
        const states = ['ACTIVE', 'PROCESSING', 'ANALYZING'];
        status.textContent = states[Math.floor(Math.random() * states.length)];
        
        // Update task count
        const taskCount = document.querySelector('.stat-item:nth-child(3) .stat-value');
        taskCount.textContent = Math.floor(Math.random() * 100);
    }, 5000);
}

// Chart update functions for real data
function updateHRVChart(data) {
    // Update the HRV chart with real data
    if (window.hrvChart && data.length > 0) {
        const chartData = data.slice(-20).map(d => d.value);
        window.hrvChart.data.datasets[0].data = chartData;
        window.hrvChart.update();
    }
}

function updateRecoveryChart(data) {
    // Update the recovery chart with real data
    if (window.recoveryChart && data.length > 0) {
        const chartData = data.slice(-20).map(d => d.value);
        window.recoveryChart.data.datasets[0].data = chartData;
        window.recoveryChart.update();
    }
}

function updateSleepDebtChart(data) {
    // Update the sleep debt chart with real data
    if (window.sleepDebtChart && data.length > 0) {
        const chartData = data.slice(-20).map(d => d.value);
        window.sleepDebtChart.data.datasets[0].data = chartData;
        window.sleepDebtChart.update();
    }
}

// Initialize everything
document.addEventListener('DOMContentLoaded', () => {
    init3DAvatar();
    init3DKnowledgeGraph();
    initBiometricCharts();
    initWebSocket();
    
    // Initialize real-time metrics
    updateRealTimeMetrics();
    
    // Connect WebSocket for live updates
    connectMetricsWebSocket();
    
    // Update metrics every 30 seconds as fallback
    metricsUpdateInterval = setInterval(() => {
        updateRealTimeMetrics();
    }, 30000);
}); 