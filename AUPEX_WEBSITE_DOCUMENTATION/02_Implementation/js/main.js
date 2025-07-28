// Hero 3D Background Animation
function initHeroBackground() {
    const container = document.getElementById('hero-3d');
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    container.appendChild(renderer.domElement);
    
    // Create particle system
    const particlesGeometry = new THREE.BufferGeometry();
    const particlesCount = 5000;
    const posArray = new Float32Array(particlesCount * 3);
    
    for (let i = 0; i < particlesCount * 3; i++) {
        posArray[i] = (Math.random() - 0.5) * 10;
    }
    
    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    
    // Create material
    const particlesMaterial = new THREE.PointsMaterial({
        size: 0.005,
        color: '#00D9FF',
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending
    });
    
    const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
    scene.add(particlesMesh);
    
    // Add lines connecting particles
    const linesGeometry = new THREE.BufferGeometry();
    const linesMaterial = new THREE.LineBasicMaterial({
        color: '#00D9FF',
        transparent: true,
        opacity: 0.2
    });
    
    camera.position.z = 3;
    
    // Mouse movement effect
    let mouseX = 0;
    let mouseY = 0;
    
    document.addEventListener('mousemove', (event) => {
        mouseX = (event.clientX / window.innerWidth) * 2 - 1;
        mouseY = -(event.clientY / window.innerHeight) * 2 + 1;
    });
    
    // Animation loop
    function animate() {
        requestAnimationFrame(animate);
        
        particlesMesh.rotation.x += 0.0005;
        particlesMesh.rotation.y += 0.001;
        
        // Mouse interaction
        particlesMesh.rotation.x += mouseY * 0.001;
        particlesMesh.rotation.y += mouseX * 0.001;
        
        renderer.render(scene, camera);
    }
    
    animate();
    
    // Handle resize
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
}

// Technology Canvas Animation
function initTechCanvas() {
    const canvas = document.getElementById('tech-canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    
    // Neural network visualization
    const nodes = [];
    const connections = [];
    
    // Create nodes
    for (let layer = 0; layer < 4; layer++) {
        const nodesInLayer = layer === 0 || layer === 3 ? 3 : 5;
        for (let i = 0; i < nodesInLayer; i++) {
            nodes.push({
                x: (layer + 1) * (canvas.width / 5),
                y: (i + 1) * (canvas.height / (nodesInLayer + 1)),
                layer: layer,
                activation: Math.random()
            });
        }
    }
    
    // Create connections
    for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
            if (nodes[j].layer === nodes[i].layer + 1) {
                connections.push({
                    from: nodes[i],
                    to: nodes[j],
                    strength: Math.random()
                });
            }
        }
    }
    
    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw connections
        connections.forEach(conn => {
            ctx.beginPath();
            ctx.moveTo(conn.from.x, conn.from.y);
            ctx.lineTo(conn.to.x, conn.to.y);
            ctx.strokeStyle = `rgba(0, 217, 255, ${conn.strength * 0.5})`;
            ctx.lineWidth = conn.strength * 2;
            ctx.stroke();
            
            // Animate strength
            conn.strength = Math.sin(Date.now() * 0.001 + conn.from.x) * 0.5 + 0.5;
        });
        
        // Draw nodes
        nodes.forEach(node => {
            ctx.beginPath();
            ctx.arc(node.x, node.y, 10 + node.activation * 10, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0, 217, 255, ${0.5 + node.activation * 0.5})`;
            ctx.fill();
            ctx.strokeStyle = '#00D9FF';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            // Animate activation
            node.activation = Math.sin(Date.now() * 0.002 + node.x + node.y) * 0.5 + 0.5;
        });
        
        requestAnimationFrame(draw);
    }
    
    draw();
}

// Smooth scroll for navigation
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// GSAP Animations
function initAnimations() {
    // Fade in hero content
    gsap.from('.hero-content > *', {
        y: 50,
        opacity: 0,
        duration: 1,
        stagger: 0.2,
        ease: 'power3.out'
    });
    
    // Animate feature cards on scroll
    gsap.from('.feature-card', {
        scrollTrigger: {
            trigger: '.features',
            start: 'top 80%'
        },
        y: 100,
        opacity: 0,
        duration: 1,
        stagger: 0.2,
        ease: 'power3.out'
    });
}

// Initialize everything
document.addEventListener('DOMContentLoaded', () => {
    initHeroBackground();
    initTechCanvas();
    initSmoothScroll();
    initAnimations();
}); 