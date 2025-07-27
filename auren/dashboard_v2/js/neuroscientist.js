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

// Initialize everything
document.addEventListener('DOMContentLoaded', () => {
    init3DAvatar();
    init3DKnowledgeGraph();
    initBiometricCharts();
    initWebSocket();
}); 