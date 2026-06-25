
import * as THREE from 'three';

const states = {
    idle: {
        layers: [
            { 
                color: 0x434FCF,  // Light purple
                opacity: 0.2,
                scale: 1.0,
                rotationSpeed: { x: 0.001, y: 0.002, z: 0 }
            },
            { 
                color: 0x434FCF,  // Medium purple
                opacity: 0.2,
                scale: 0.85,
                rotationSpeed: { x: -0.002, y: 0.003, z: 0.001 }
            },
            { 
                color: 0x434FCF,  // Light purple
                opacity: 0.4,
                scale: 0.70,
                rotationSpeed: { x: 0.003, y: -0.002, z: -0.001 }
            }
        ],
        audioLevel: 0.15,
        audioFrequency: 0.2,
        timeSpeed: 0.015,
        pulsate: false,
        chromaticAberration: 0.8,
        description: 'Calm and ready'
    },
    listening: {
        layers: [
            { 
                color: 0x434FCF,  // Soft blue
                opacity: 0.2,
                scale: 1.0,
                rotationSpeed: { x: 0.002, y: 0.004, z: 0 }
            },
            { 
                color: 0x434FCF,  // Medium blue
                opacity: 0.2,
                scale: 0.85,
                rotationSpeed: { x: -0.003, y: 0.005, z: 0.002 }
            },
            { 
                color: 0x434FCF,  // Light blue
                opacity: 0.4,
                scale: 0.70,
                rotationSpeed: { x: 0.004, y: -0.003, z: -0.001 }
            }
        ],
        audioLevel: 0.6,
        audioFrequency: 0.7,
        timeSpeed: 0.022,
        pulsate: true,
        pulsateMode: 'audio-reactive',
        pulsateMin: 0.02,
        pulsateMax: 0.25,
        chromaticAberration: 1.2,
        description: 'Actively listening'
    },
    thinking: {
        layers: [
            { 
                color: 0x8747F7,  // Soft purple
                opacity: 0.2,
                scale: 0.85,
                rotationSpeed: { x: 0.003, y: 0.003, z: 0 }
            },
            { 
                color: 0x8747F7,  // Medium purple
                opacity: 0.2,
                scale: 0.72,
                rotationSpeed: { x: -0.004, y: 0.004, z: 0.002 }
            },
            { 
                color: 0x8747F7,  // Light purple
                opacity: 0.4,
                scale: 0.60,
                rotationSpeed: { x: 0.005, y: -0.004, z: -0.002 }
            }
        ],
        audioLevel: 0.45,
        audioFrequency: 0.5,
        timeSpeed: 0.02,
        pulsate: true,
        pulsateMode: 'thinking',
        pulsateMin: 0.0,
        pulsateMax: 0.15,
        chromaticAberration: 0.8,
        description: 'Processing...'
    },
    speaking: {
        layers: [
            { 
                color: 0xFF1893,  // Soft pink
                opacity: 0.2,
                scale: 1.0,
                rotationSpeed: { x: 0.004, y: 0.005, z: 0 }
            },
            { 
                color: 0xFF1893,  // Medium pink-red
                opacity: 0.2,
                scale: 0.85,
                rotationSpeed: { x: -0.005, y: 0.006, z: 0.003 }
            },
            { 
                color: 0xFF1893,  // Bright pink
                opacity: 0.4,
                scale: 0.70,
                rotationSpeed: { x: 0.006, y: -0.005, z: -0.002 }
            }
        ],
        audioLevel: 0.8,
        audioFrequency: 0.9,
        timeSpeed: 0.027,
        pulsate: true,
        pulsateMode: 'cadence',
        pulsateMin: 0.05,
        pulsateMax: 0.22,
        chromaticAberration: 1.5,
        description: 'Speaking...'
    }
};

const vertexShader = `
    varying vec3 vNormal;
    varying vec3 vPosition;
    varying vec2 vUv;
    
    uniform float time;
    uniform float audioLevel;
    uniform float layerOffset;
    
    // Simple noise function for organic distortion
    vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
    vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
    vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
    vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }
    
    float snoise(vec3 v) {
        const vec2 C = vec2(1.0/6.0, 1.0/3.0);
        const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
        
        vec3 i  = floor(v + dot(v, C.yyy));
        vec3 x0 = v - i + dot(i, C.xxx);
        
        vec3 g = step(x0.yzx, x0.xyz);
        vec3 l = 1.0 - g;
        vec3 i1 = min(g.xyz, l.zxy);
        vec3 i2 = max(g.xyz, l.zxy);
        
        vec3 x1 = x0 - i1 + C.xxx;
        vec3 x2 = x0 - i2 + C.yyy;
        vec3 x3 = x0 - D.yyy;
        
        i = mod289(i);
        vec4 p = permute(permute(permute(
            i.z + vec4(0.0, i1.z, i2.z, 1.0))
            + i.y + vec4(0.0, i1.y, i2.y, 1.0))
            + i.x + vec4(0.0, i1.x, i2.x, 1.0));
        
        float n_ = 0.142857142857;
        vec3 ns = n_ * D.wyz - D.xzx;
        
        vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
        
        vec4 x_ = floor(j * ns.z);
        vec4 y_ = floor(j - 7.0 * x_);
        
        vec4 x = x_ *ns.x + ns.yyyy;
        vec4 y = y_ *ns.x + ns.yyyy;
        vec4 h = 1.0 - abs(x) - abs(y);
        
        vec4 b0 = vec4(x.xy, y.xy);
        vec4 b1 = vec4(x.zw, y.zw);
        
        vec4 s0 = floor(b0)*2.0 + 1.0;
        vec4 s1 = floor(b1)*2.0 + 1.0;
        vec4 sh = -step(h, vec4(0.0));
        
        vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
        vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
        
        vec3 p0 = vec3(a0.xy, h.x);
        vec3 p1 = vec3(a0.zw, h.y);
        vec3 p2 = vec3(a1.xy, h.z);
        vec3 p3 = vec3(a1.zw, h.w);
        
        vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
        p0 *= norm.x;
        p1 *= norm.y;
        p2 *= norm.z;
        p3 *= norm.w;
        
        vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
        m = m * m;
        return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
    }
    
    void main() {
        vUv = uv;
        vNormal = normalize(normalMatrix * normal);
        
        vec3 pos = position;
        
        // Wave distortion - flowing patterns
        float wave1 = sin(pos.y * 2.5 + time * 1.5 + layerOffset) * cos(pos.x * 2.0 - time * 1.2);
        float wave2 = sin(pos.x * 3.0 - time * 1.8 + layerOffset) * cos(pos.z * 2.5 + time * 1.5);
        float wave3 = sin(pos.z * 2.8 + time * 1.6 + layerOffset) * cos(pos.y * 2.3 - time * 1.3);
        
        // Noise-based organic distortion
        float noise1 = snoise(pos * 1.2 + time * 0.3 + layerOffset);
        float noise2 = snoise(pos * 2.0 - time * 0.2 + layerOffset * 0.5);
        
        // Combine distortions - reduced intensity
        float distortion = (wave1 + wave2 + wave3) * 0.008;
        distortion += (noise1 * 0.008 + noise2 * 0.007);
        
        // Audio reactivity
        distortion *= (0.3 + audioLevel * 0.6);
        
        // Apply distortion along normal
        pos = pos + normal * distortion;
        
        vPosition = pos;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
    }
`;

const fragmentShader = `
    varying vec3 vNormal;
    varying vec3 vPosition;
    varying vec2 vUv;
    
    uniform vec3 sphereColor;
    uniform float opacity;
    uniform float time;
    uniform float chromaticAberration;
    
    // RGB to HSV conversion
    vec3 rgb2hsv(vec3 c) {
        vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
        vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
        vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
        float d = q.x - min(q.w, q.y);
        float e = 1.0e-10;
        return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
    }
    
    // HSV to RGB conversion
    vec3 hsv2rgb(vec3 c) {
        vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
        vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
        return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
    }
    
    void main() {
        // Calculate fresnel-like effect based on view angle
        vec3 viewDirection = normalize(cameraPosition - vPosition);
        float fresnel = pow(1.0 - abs(dot(viewDirection, normalize(vNormal))), 2.0);
        
        // Holographic rainbow effect based on surface normal and view angle
        vec3 normalWorld = normalize(vNormal);
        
        // Create rainbow gradient based on normal direction and position
        float rainbowShift = normalWorld.x * 0.5 + normalWorld.y * 0.2 + normalWorld.z * 0.1;
        rainbowShift += sin(vPosition.x * 5.0 + time * 0.5) * 0.01;
        rainbowShift += cos(vPosition.y * 4.0 - time * 0.3) * 0.01;
        rainbowShift = fract(rainbowShift);
        
        // Generate holographic rainbow colors
        vec3 rainbow = hsv2rgb(vec3(rainbowShift, 0.8, 1.0));
        
        // Convert base color to HSV
        vec3 hsv = rgb2hsv(sphereColor);
        
        // Create chromatic aberration by shifting hue based on position
        float aberrationAmount = chromaticAberration * fresnel;
        
        // Shift red channel
        vec3 hsvR = hsv;
        hsvR.x = fract(hsv.x + aberrationAmount * 0.15);
        vec3 colorR = hsv2rgb(hsvR);
        
        // Keep green as base
        vec3 colorG = sphereColor;
        
        // Shift blue channel opposite direction
        vec3 hsvB = hsv;
        hsvB.x = fract(hsv.x - aberrationAmount * 0.15);
        vec3 colorB = hsv2rgb(hsvB);
        
        // Mix channels for chromatic aberration effect
        vec3 color = vec3(colorR.r, colorG.g, colorB.b);
        
        // Blend in holographic rainbow effect, stronger at edges (fresnel)
        float holographicIntensity = fresnel * 0.6 + 0.2; // 0.2 to 0.8 range
        color = mix(color, rainbow, holographicIntensity * 0.6);
        
        // Add edge emphasis where aberration is strongest
        color += fresnel * chromaticAberration * 0.15;
        
        // Add subtle brightness variation based on position
        float brightness = 1.0 + sin(vPosition.x * 3.0 + time) * 0.1;
        brightness += sin(vPosition.y * 2.5 - time * 0.8) * 0.1;
        
        // Add extra shimmer for holographic effect
        float shimmer = sin(vPosition.x * 8.0 + vPosition.y * 6.0 + time * 2.0) * 0.04 + 0.96;
        brightness *= shimmer;
        
        color *= brightness;
        
        gl_FragColor = vec4(color, opacity);
    }
`;

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
