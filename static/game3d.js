import * as THREE from 'three';
import { OrbitControls } from 'https://unpkg.com/three@0.128.0/examples/jsm/controls/OrbitControls.js';

// --- Scene Setup ---
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x050b1a);
scene.fog = new THREE.FogExp2(0x050b1a, 0.02);

// Camera (dynamic, but we'll use OrbitControls for demo)
const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(6, 4, 8);
camera.lookAt(0, 1, 0);

// Renderer
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

// Controls (can be disabled for cinematic feel)
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.autoRotate = false;
controls.enableZoom = true;
controls.target.set(0, 1, 0);

// --- Lighting (Cel-shaded style) ---
const ambientLight = new THREE.AmbientLight(0x404060);
scene.add(ambientLight);

const mainLight = new THREE.DirectionalLight(0xffeedd, 1.2);
mainLight.position.set(5, 10, 4);
mainLight.castShadow = true;
mainLight.receiveShadow = false;
mainLight.shadow.mapSize.width = 1024;
mainLight.shadow.mapSize.height = 1024;
scene.add(mainLight);

const fillLight = new THREE.PointLight(0x88aaff, 0.4);
fillLight.position.set(-2, 3, 3);
scene.add(fillLight);

const backLight = new THREE.PointLight(0xffaa66, 0.5);
backLight.position.set(0, 2, -5);
scene.add(backLight);

// Rim light (from below)
const rimLight = new THREE.PointLight(0xff8844, 0.3);
rimLight.position.set(0, -1, 0);
scene.add(rimLight);

// --- Arena (FighterZ style ground) ---
const groundMat = new THREE.MeshStandardMaterial({ color: 0x2266aa, roughness: 0.4, metalness: 0.7, emissive: 0x112233 });
const groundPlane = new THREE.Mesh(new THREE.PlaneGeometry(14, 12), groundMat);
groundPlane.rotation.x = -Math.PI / 2;
groundPlane.position.y = -0.5;
groundPlane.receiveShadow = true;
scene.add(groundPlane);

// Decorative circle (glowing)
const circleRing = new THREE.Mesh(
    new THREE.TorusGeometry(4, 0.2, 64, 200),
    new THREE.MeshStandardMaterial({ color: 0xffaa44, emissive: 0x442200 })
);
circleRing.rotation.x = Math.PI / 2;
circleRing.position.y = -0.4;
scene.add(circleRing);

const outerRing = new THREE.Mesh(
    new THREE.TorusGeometry(5.5, 0.15, 64, 200),
    new THREE.MeshStandardMaterial({ color: 0x88aaff, emissive: 0x224466 })
);
outerRing.rotation.x = Math.PI / 2;
outerRing.position.y = -0.45;
scene.add(outerRing);

// Particle system (energy orbs)
const particleCount = 500;
const particleGeo = new THREE.BufferGeometry();
const particlePositions = new Float32Array(particleCount * 3);
for (let i = 0; i < particleCount; i++) {
    particlePositions[i*3] = (Math.random() - 0.5) * 20;
    particlePositions[i*3+1] = Math.random() * 5;
    particlePositions[i*3+2] = (Math.random() - 0.5) * 16;
}
particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
const particleMat = new THREE.PointsMaterial({ color: 0x88aaff, size: 0.05 });
const particles = new THREE.Points(particleGeo, particleMat);
scene.add(particles);

// --- Character Models (simple but stylized with cel-shading look) ---
// Player (Monkey King) – red with gold accents
const playerGroup = new THREE.Group();
const playerBody = new THREE.Mesh(
    new THREE.BoxGeometry(0.9, 1.3, 0.9),
    new THREE.MeshStandardMaterial({ color: 0xdd5533, emissive: 0x331100, roughness: 0.3, metalness: 0.2 })
);
playerBody.castShadow = true;
playerBody.receiveShadow = true;
playerBody.position.y = 0.65;
playerGroup.add(playerBody);

// Head
const playerHead = new THREE.Mesh(
    new THREE.SphereGeometry(0.55, 32, 32),
    new THREE.MeshStandardMaterial({ color: 0xffaa77, emissive: 0x442200 })
);
playerHead.position.y = 1.3;
playerGroup.add(playerHead);

// Outline (wireframe) for cel-shading effect
const playerOutline = new THREE.Mesh(
    new THREE.BoxGeometry(0.95, 1.35, 0.95),
    new THREE.MeshBasicMaterial({ color: 0xffaa44, wireframe: true, transparent: true, opacity: 0.3 })
);
playerOutline.position.y = 0.65;
playerGroup.add(playerOutline);

// Floating health bar above character
const playerHealthPlane = new THREE.Mesh(
    new THREE.PlaneGeometry(1.4, 0.2),
    new THREE.MeshBasicMaterial({ color: 0x33ff33, side: THREE.DoubleSide, transparent: true, opacity: 0.9 })
);
playerHealthPlane.position.y = 1.9;
playerGroup.add(playerHealthPlane);
const playerHealthBg = new THREE.Mesh(
    new THREE.PlaneGeometry(1.4, 0.2),
    new THREE.MeshBasicMaterial({ color: 0xcc3333, side: THREE.DoubleSide, transparent: true, opacity: 0.7 })
);
playerHealthBg.position.y = 1.9;
playerHealthBg.position.z = -0.02;
playerGroup.add(playerHealthBg);

// Enemy (Percy) – blue with silver
const enemyGroup = new THREE.Group();
const enemyBody = new THREE.Mesh(
    new THREE.BoxGeometry(0.9, 1.3, 0.9),
    new THREE.MeshStandardMaterial({ color: 0x3399ff, emissive: 0x002244, roughness: 0.3, metalness: 0.2 })
);
enemyBody.castShadow = true;
enemyBody.receiveShadow = true;
enemyBody.position.y = 0.65;
enemyGroup.add(enemyBody);

const enemyHead = new THREE.Mesh(
    new THREE.SphereGeometry(0.55, 32, 32),
    new THREE.MeshStandardMaterial({ color: 0xaaccff, emissive: 0x224466 })
);
enemyHead.position.y = 1.3;
enemyGroup.add(enemyHead);

const enemyOutline = new THREE.Mesh(
    new THREE.BoxGeometry(0.95, 1.35, 0.95),
    new THREE.MeshBasicMaterial({ color: 0x88aaff, wireframe: true, transparent: true, opacity: 0.3 })
);
enemyOutline.position.y = 0.65;
enemyGroup.add(enemyOutline);

const enemyHealthPlane = new THREE.Mesh(
    new THREE.PlaneGeometry(1.4, 0.2),
    new THREE.MeshBasicMaterial({ color: 0x33ff33, side: THREE.DoubleSide, transparent: true, opacity: 0.9 })
);
enemyHealthPlane.position.y = 1.9;
enemyGroup.add(enemyHealthPlane);
const enemyHealthBg = new THREE.Mesh(
    new THREE.PlaneGeometry(1.4, 0.2),
    new THREE.MeshBasicMaterial({ color: 0xcc3333, side: THREE.DoubleSide, transparent: true, opacity: 0.7 })
);
enemyHealthBg.position.y = 1.9;
enemyHealthBg.position.z = -0.02;
enemyGroup.add(enemyHealthBg);

// Position characters on the arena
playerGroup.position.set(-2.2, 0, 0);
enemyGroup.position.set(2.2, 0, 0);
scene.add(playerGroup);
scene.add(enemyGroup);

// Simple idle animation (bobbing)
let time = 0;

// --- UI Elements ---
const playerHealthFill = document.getElementById('playerHealthFill');
const enemyHealthFill = document.getElementById('enemyHealthFill');
const playerMeterFill = document.getElementById('playerMeterFill');
const enemyMeterFill = document.getElementById('enemyMeterFill');
const playerNameSpan = document.getElementById('playerName');
const enemyNameSpan = document.getElementById('enemyName');
const vsText = document.getElementById('vsText');
const comboText = document.getElementById('comboText');
const rageText = document.getElementById('rageText');

// --- Game State Polling ---
let currentState = null;
let lastCombo = 0;
let lastRage = false;

async function fetchGameState() {
    try {
        const res = await fetch('/state');
        if (!res.ok) throw new Error('Network error');
        const data = await res.json();
        currentState = data;
        updateUI();
        update3DBars();
        handleVisualEffects();
    } catch (err) {
        console.error('State fetch error:', err);
    }
}

function updateUI() {
    if (!currentState) return;

    // Health bars (2D)
    const playerPercent = (currentState.player_health / currentState.player_max_health) * 100;
    const enemyPercent = (currentState.enemy_health / currentState.enemy_max_health) * 100;
    playerHealthFill.style.width = `${playerPercent}%`;
    enemyHealthFill.style.width = `${enemyPercent}%`;

    playerMeterFill.style.width = `${currentState.player_super_meter}%`;
    enemyMeterFill.style.width = `${currentState.enemy_super_meter}%`;

    playerNameSpan.textContent = currentState.player_name;
    enemyNameSpan.textContent = currentState.enemy_name;

    // Combo display
    if (currentState.player_combo !== lastCombo && currentState.player_combo > 1) {
        comboText.style.display = 'block';
        comboText.textContent = `🔥 x${currentState.player_combo} COMBO! 🔥`;
        setTimeout(() => comboText.style.display = 'none', 800);
        lastCombo = currentState.player_combo;
    } else if (currentState.player_combo <= 1) {
        comboText.style.display = 'none';
    }

    // Rage mode
    if (currentState.player_rage !== lastRage && currentState.player_rage) {
        rageText.style.display = 'block';
        setTimeout(() => rageText.style.display = 'none', 2000);
        lastRage = currentState.player_rage;
    }

    // VS screen on round start
    if (currentState.message && currentState.message.includes('ROUND') && !vsText.style.display) {
        vsText.style.display = 'block';
        setTimeout(() => vsText.style.display = 'none', 1500);
    }
}

function update3DBars() {
    if (!currentState) return;
    // Update floating health bars
    const playerHealthRatio = currentState.player_health / currentState.player_max_health;
    playerHealthPlane.scale.x = playerHealthRatio;
    playerHealthPlane.position.x = -0.7 + (playerHealthRatio * 0.7);
    const enemyHealthRatio = currentState.enemy_health / currentState.enemy_max_health;
    enemyHealthPlane.scale.x = enemyHealthRatio;
    enemyHealthPlane.position.x = -0.7 + (enemyHealthRatio * 0.7);
}

// --- Visual Effects (hit flash, super flash) ---
function hitFlash(targetGroup, intensity = 0.8) {
    const originalEmissive = targetGroup.children[0].material.emissiveIntensity;
    targetGroup.children[0].material.emissiveIntensity = intensity;
    setTimeout(() => {
        targetGroup.children[0].material.emissiveIntensity = originalEmissive;
    }, 150);
}

// Super flash (screen white)
function superFlash() {
    const flashDiv = document.createElement('div');
    flashDiv.style.position = 'fixed';
    flashDiv.style.top = 0;
    flashDiv.style.left = 0;
    flashDiv.style.width = '100%';
    flashDiv.style.height = '100%';
    flashDiv.style.backgroundColor = 'white';
    flashDiv.style.pointerEvents = 'none';
    flashDiv.style.zIndex = 1000;
    flashDiv.style.opacity = 0.8;
    document.body.appendChild(flashDiv);
    setTimeout(() => flashDiv.remove(), 150);
}

// Check for recent damage (to trigger hit flash)
let lastPlayerHealth = 100;
let lastEnemyHealth = 100;

function handleVisualEffects() {
    if (!currentState) return;
    if (currentState.player_health < lastPlayerHealth) {
        hitFlash(playerGroup);
        // If heavy damage, shake camera
        const damage = lastPlayerHealth - currentState.player_health;
        if (damage > 15) {
            document.body.style.animation = 'shake 0.2s';
            setTimeout(() => document.body.style.animation = '', 200);
        }
    }
    if (currentState.enemy_health < lastEnemyHealth) {
        hitFlash(enemyGroup);
        const damage = lastEnemyHealth - currentState.enemy_health;
        if (damage > 15) {
            document.body.style.animation = 'shake 0.2s';
            setTimeout(() => document.body.style.animation = '', 200);
        }
    }
    // Detect super move (player used super)
    if (currentState.message && currentState.message.includes('SUPER') && !currentState.message.includes('Enemy')) {
        superFlash();
        // Add particle explosion around enemy
        createExplosion(enemyGroup.position);
    }
    lastPlayerHealth = currentState.player_health;
    lastEnemyHealth = currentState.enemy_health;
}

// Simple particle explosion
function createExplosion(position) {
    const particleCount = 60;
    const particles = [];
    for (let i = 0; i < particleCount; i++) {
        const geom = new THREE.SphereGeometry(0.05, 4, 4);
        const mat = new THREE.MeshStandardMaterial({ color: 0xffaa44, emissive: 0xff4400 });
        const particle = new THREE.Mesh(geom, mat);
        particle.position.copy(position);
        particle.userData = {
            velocity: new THREE.Vector3(
                (Math.random() - 0.5) * 4,
                Math.random() * 3,
                (Math.random() - 0.5) * 4
            ),
            life: 1.0
        };
        scene.add(particle);
        particles.push(particle);
    }
    // Animate explosion
    const animateExplosion = () => {
        let anyAlive = false;
        particles.forEach(p => {
            p.userData.life -= 0.03;
            if (p.userData.life <= 0) {
                scene.remove(p);
                return;
            }
            anyAlive = true;
            p.position.x += p.userData.velocity.x * 0.1;
            p.position.y += p.userData.velocity.y * 0.1;
            p.position.z += p.userData.velocity.z * 0.1;
            p.scale.setScalar(p.userData.life);
            p.material.emissiveIntensity = p.userData.life * 2;
        });
        if (anyAlive) requestAnimationFrame(animateExplosion);
    };
    animateExplosion();
}

// Shake animation (CSS)
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0% { transform: translate(1px,1px); }
        25% { transform: translate(-1px,-2px); }
        50% { transform: translate(2px,0px); }
        75% { transform: translate(-2px,1px); }
        100% { transform: translate(0,0); }
    }
`;
document.head.appendChild(style);

// --- Animation Loop ---
function animate() {
    requestAnimationFrame(animate);
    time += 0.02;

    // Idle bobbing
    playerGroup.position.y = Math.sin(time * 2) * 0.04;
    enemyGroup.position.y = Math.sin(time * 2 + Math.PI) * 0.04;

    // Rotate rings
    circleRing.rotation.z += 0.005;
    outerRing.rotation.z -= 0.003;

    // Particle drift
    particles.rotation.y += 0.002;

    controls.update();
    renderer.render(scene, camera);
}

// Start polling and animation
setInterval(fetchGameState, 300);
fetchGameState();
animate();
