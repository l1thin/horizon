const fs = require('fs');
const path = require('path');

const appJsPath = path.join(__dirname, 'voiceorb', 'app.js');
const outputPath = path.join(__dirname, '..', 'frontend', 'src', 'components', 'orb', 'OrbRenderer.js');

const appJs = fs.readFileSync(appJsPath, 'utf8');

// Extract states
const statesStart = appJs.indexOf('const states = {');
const statesEnd = appJs.indexOf('};', statesStart) + 2;
const statesBlock = appJs.slice(statesStart, statesEnd);

// Extract vertexShader
const vsStart = appJs.indexOf('const vertexShader = `');
const vsEnd = appJs.indexOf('`;', vsStart) + 2;
const vsBlock = appJs.slice(vsStart, vsEnd);

// Extract fragmentShader
const fsStart = appJs.indexOf('const fragmentShader = `');
const fsEnd = appJs.indexOf('`;', fsStart) + 2;
const fsBlock = appJs.slice(fsStart, fsEnd);

const rendererTemplate = `
import * as THREE from 'three';

${statesBlock}

${vsBlock}

${fsBlock}

export function initOrb(canvas) {
    let scene = new THREE.Scene();
    let camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    camera.position.z = 5;
    
    let renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setSize(canvas.clientWidth || 360, canvas.clientHeight || 360, false);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    let orbLayers = [];
    let currentState = 'idle';
    let currentScale = 1.0;
    let targetScale = 1.0;

    let listeningDemo = { nextChange: 0, intensity: 0 };
    let speakingCadence = { nextChange: 0, intensity: 0 };

    const initialState = states.idle;
    initialState.layers.forEach((layerConfig, index) => {
        const geometry = new THREE.SphereGeometry(layerConfig.scale, 80, 80);
        const material = new THREE.ShaderMaterial({
            vertexShader,
            fragmentShader,
            uniforms: {
                time: { value: 0 },
                audioLevel: { value: 0 },
                layerOffset: { value: index * 2.0 },
                sphereColor: { value: new THREE.Color(layerConfig.color) },
                opacity: { value: layerConfig.opacity },
                chromaticAberration: { value: initialState.chromaticAberration || 0.1 },
                cameraPosition: { value: camera.position }
            },
            transparent: true,
            side: THREE.DoubleSide,
            blending: THREE.NormalBlending,
            depthWrite: false
        });
        
        const sphere = new THREE.Mesh(geometry, material);
        sphere.userData = {
            baseScale: layerConfig.scale,
            rotationSpeed: layerConfig.rotationSpeed,
            layerIndex: index
        };
        
        scene.add(sphere);
        orbLayers.push(sphere);
    });

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
    scene.add(ambientLight);
    
    const pointLight1 = new THREE.PointLight(0x667eea, 0.6, 100);
    pointLight1.position.set(5, 5, 5);
    scene.add(pointLight1);
    
    const pointLight2 = new THREE.PointLight(0x764ba2, 0.4, 100);
    pointLight2.position.set(-5, -5, 5);
    scene.add(pointLight2);

    let animationId;

    function animate() {
        animationId = requestAnimationFrame(animate);
        
        const state = states[currentState];
        if (!state) return;

        let audioLevel = state.audioLevel;
        let audioFrequency = state.audioFrequency;

        if (state.pulsate) {
            if (state.pulsateMode === 'audio-reactive') {
                const now = Date.now() * 0.001;
                if (now >= listeningDemo.nextChange) {
                    const patternType = Math.random();
                    if (patternType < 0.25) {
                        listeningDemo.intensity = 0.5 + Math.random() * 0.3;
                        listeningDemo.nextChange = now + 0.1 + Math.random() * 0.1;
                    } else if (patternType < 0.5) {
                        listeningDemo.intensity = 0.6 + Math.random() * 0.3;
                        listeningDemo.nextChange = now + 0.2 + Math.random() * 0.2;
                    } else if (patternType < 0.75) {
                        listeningDemo.intensity = 0.7 + Math.random() * 0.3;
                        listeningDemo.nextChange = now + 0.15 + Math.random() * 0.25;
                    } else if (patternType < 0.9) {
                        listeningDemo.intensity = 0.4 + Math.random() * 0.4;
                        listeningDemo.nextChange = now + 0.3 + Math.random() * 0.3;
                    } else {
                        listeningDemo.intensity = 0.05 + Math.random() * 0.1;
                        listeningDemo.nextChange = now + 0.1 + Math.random() * 0.15;
                    }
                }
                const fluctuation = Math.sin(now * 8.0) * 0.1;
                let volumeScale = Math.max(0, listeningDemo.intensity + fluctuation);
                targetScale = 1.0 + state.pulsateMin + (volumeScale * (state.pulsateMax - state.pulsateMin));
            } else if (state.pulsateMode === 'thinking') {
                const time = Date.now() * 0.001;
                const thinkingPulse = (Math.sin(time * 1.5) + 1.0) / 2.0;
                targetScale = 1.0 + state.pulsateMin + (thinkingPulse * (state.pulsateMax - state.pulsateMin));
            } else if (state.pulsateMode === 'cadence') {
                const now = Date.now() * 0.001;
                if (now >= speakingCadence.nextChange) {
                    const patternType = Math.random();
                    if (patternType < 0.3) {
                        speakingCadence.intensity = 0.7 + Math.random() * 0.3;
                        speakingCadence.nextChange = now + 0.15 + Math.random() * 0.15;
                    } else if (patternType < 0.6) {
                        speakingCadence.intensity = 0.5 + Math.random() * 0.4;
                        speakingCadence.nextChange = now + 0.3 + Math.random() * 0.3;
                    } else if (patternType < 0.85) {
                        speakingCadence.intensity = 0.6 + Math.random() * 0.4;
                        speakingCadence.nextChange = now + 0.5 + Math.random() * 0.4;
                    } else {
                        speakingCadence.intensity = 0.1 + Math.random() * 0.2;
                        speakingCadence.nextChange = now + 0.2 + Math.random() * 0.3;
                    }
                }
                const fluctuation = Math.sin(now * 10.0) * 0.08;
                let cadenceIntensity = Math.max(0, speakingCadence.intensity + fluctuation);
                targetScale = 1.0 + state.pulsateMin + (cadenceIntensity * (state.pulsateMax - state.pulsateMin));
            }
            const smoothing = 0.15;
            currentScale += (targetScale - currentScale) * smoothing;
        } else {
            targetScale = 1.0;
            currentScale += (targetScale - currentScale) * 0.1;
        }

        orbLayers.forEach((layer, index) => {
            const layerConfig = state.layers[index];
            if (layerConfig) {
                layer.material.uniforms.time.value += state.timeSpeed;
                layer.material.uniforms.audioLevel.value = audioLevel;
                layer.material.uniforms.chromaticAberration.value = state.chromaticAberration || 0.1;
                
                layer.rotation.x += layer.userData.rotationSpeed.x;
                layer.rotation.y += layer.userData.rotationSpeed.y;
                layer.rotation.z += layer.userData.rotationSpeed.z;
                
                const layerScale = layer.userData.baseScale * currentScale;
                layer.scale.set(layerScale, layerScale, layerScale);
            }
        });
        
        renderer.render(scene, camera);
    }

    animate();

    return {
        setState: (newState) => {
            if (states[newState]) {
                currentState = newState;
                const state = states[newState];
                orbLayers.forEach((layer, index) => {
                    const layerConfig = state.layers[index];
                    if (layerConfig) {
                        layer.material.uniforms.sphereColor.value.setHex(layerConfig.color);
                        layer.material.uniforms.opacity.value = layerConfig.opacity;
                        layer.userData.rotationSpeed = layerConfig.rotationSpeed;
                        layer.userData.baseScale = layerConfig.scale;
                    }
                });
            }
        },
        dispose: () => {
            cancelAnimationFrame(animationId);
            renderer.dispose();
            scene.clear();
        }
    };
}
`;

fs.writeFileSync(outputPath, rendererTemplate);
console.log('OrbRenderer.js generated successfully!');
