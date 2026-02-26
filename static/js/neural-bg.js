// 3D Neural Sphere Animation — HTMX-aware, tab-recovery safe
// Colors: Electric Blue · Bio-Cyan · Deep Violet (authentic neural network palette)

(function () {
    // ── Node colors: inspired by real neuron signal types ──────────────────────
    const NODE_COLORS = [
        '64, 156, 255',   // Electric Blue  — primary synaptic signal
        '0, 230, 200',    // Bio-Cyan       — active / depolarised membrane
        '150, 80, 255',   // Deep Violet    — inhibitory neuron accent
    ];

    // ── Config ─────────────────────────────────────────────────────────────────
    const NUM_NODES = 130;
    const SPHERE_RADIUS = 200;
    const CONNECTION_DISTANCE = 82;

    // ── Module-level state ─────────────────────────────────────────────────────
    let rafId = null;
    let rotationY = 0;
    let rotationX = 0;
    let nodes = [];
    let connections = [];
    let activeCanvas = null;
    let canvasRO = null;   // ResizeObserver for the active canvas
    let roDebounce = null;   // debounce timer handle
    let launched = false;  // did we already call build+startLoop for this canvas?

    // ─────────────────────────────────────────────────────────────────────────
    // PUBLIC: called on first load + every htmx:afterSwap
    // ─────────────────────────────────────────────────────────────────────────
    function initNeuralSphere() {
        const canvas = document.getElementById('neural-sphere');

        // Tear down any running loop and observer from the previous canvas
        stopLoop();
        if (canvasRO) { canvasRO.disconnect(); canvasRO = null; }
        if (roDebounce) { clearTimeout(roDebounce); roDebounce = null; }

        if (!canvas) { activeCanvas = null; return; }

        activeCanvas = canvas;
        launched = false;
        rotationY = 0;
        rotationX = 0;

        // ── Strategy ───────────────────────────────────────────────────────────
        // Attach a ResizeObserver to the canvas. The browser fires it after
        // layout, so we always get accurate dimensions — no rAF guessing.
        //
        // The key problem: the observer fires MULTIPLE TIMES during HTMX reflow.
        // A grid re-layout causes intermediate events with wrong dimensions.
        // We debounce the callback (50 ms) so we only act on the FINAL stable
        // size once the grid has fully settled.
        // ──────────────────────────────────────────────────────────────────────
        if (typeof ResizeObserver !== 'undefined') {
            canvasRO = new ResizeObserver(function (entries) {
                // Bail if a later swap replaced our canvas
                if (activeCanvas !== canvas) {
                    canvasRO.disconnect(); canvasRO = null;
                    return;
                }

                // Read the latest entry's size
                let w = 0, h = 0;
                for (const entry of entries) {
                    if (entry.borderBoxSize && entry.borderBoxSize.length) {
                        w = Math.round(entry.borderBoxSize[0].inlineSize);
                        h = Math.round(entry.borderBoxSize[0].blockSize);
                    } else {
                        w = Math.round(entry.contentRect.width);
                        h = Math.round(entry.contentRect.height);
                    }
                }

                // Ignore zero / tiny sizes (canvas hidden or not yet in layout)
                if (w < 4 && h < 4) return;

                // DEBOUNCE: cancel any pending apply and wait for layout to settle.
                // Only the final event (after the grid stops reflowing) will apply.
                clearTimeout(roDebounce);
                const capturedW = w, capturedH = h;
                roDebounce = setTimeout(function () {
                    roDebounce = null;
                    if (activeCanvas !== canvas) return;

                    // At this point CSS layout has stabilised. The container is
                    // aspect-square so use the LARGER of the two dimensions to
                    // guarantee a square buffer regardless of which dimension
                    // the final stable layout reports first.
                    const side = Math.max(capturedW, capturedH);
                    canvas.width = side;
                    canvas.height = side;

                    if (!launched) {
                        launched = true;
                        build(canvas);
                        startLoop(canvas);
                    }
                    // Subsequent events (e.g. window resize): loop keeps running,
                    // next draw() picks up the new buffer dimensions automatically.
                }, 50); // 50 ms is enough for a grid re-layout to finish
            });

            canvasRO.observe(canvas, { box: 'border-box' });

        } else {
            // Fallback for very old browsers without ResizeObserver
            setTimeout(function () {
                if (activeCanvas !== canvas) return;
                const side = Math.max(canvas.clientWidth, canvas.clientHeight, 1);
                canvas.width = side;
                canvas.height = side;
                build(canvas);
                startLoop(canvas);
            }, 200);
        }
    }

    // Deferred version — used by visibilitychange to let layout paint first
    function initNeuralSphereDeferred() {
        requestAnimationFrame(function () {
            requestAnimationFrame(initNeuralSphere);
        });
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Helpers
    // ─────────────────────────────────────────────────────────────────────────
    function stopLoop() {
        if (rafId !== null) {
            cancelAnimationFrame(rafId);
            rafId = null;
        }
    }

    function startLoop(canvas) {
        const ctx = canvas.getContext('2d');

        function tick() {
            if (!document.body.contains(canvas)) {
                stopLoop();
                activeCanvas = null;
                return;
            }
            draw(canvas, ctx);
            rafId = requestAnimationFrame(tick);
        }

        rafId = requestAnimationFrame(tick);
    }

    function build(canvas) {
        nodes = [];
        connections = [];

        // Fibonacci lattice — even point distribution on sphere surface
        for (let i = 0; i < NUM_NODES; i++) {
            const phi = Math.acos(1 - 2 * (i + 0.5) / NUM_NODES);
            const theta = Math.PI * (1 + Math.sqrt(5)) * i;
            const color = NODE_COLORS[Math.floor(Math.random() * NODE_COLORS.length)];

            nodes.push({
                ox: SPHERE_RADIUS * Math.sin(phi) * Math.cos(theta),
                oy: SPHERE_RADIUS * Math.sin(phi) * Math.sin(theta),
                oz: SPHERE_RADIUS * Math.cos(phi),
                color,
                x: 0, y: 0, z: 0, scale: 0,
            });
        }

        // Pre-compute connections by 3-D proximity
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const dx = nodes[i].ox - nodes[j].ox;
                const dy = nodes[i].oy - nodes[j].oy;
                const dz = nodes[i].oz - nodes[j].oz;
                if (Math.sqrt(dx * dx + dy * dy + dz * dz) < CONNECTION_DISTANCE) {
                    connections.push([i, j]);
                }
            }
        }
    }

    function draw(canvas, ctx) {
        const w = canvas.width;
        const h = canvas.height;
        const cx = w / 2;
        const cy = h / 2;

        ctx.clearRect(0, 0, w, h);

        rotationY += 0.003;
        rotationX += 0.001;

        const cosY = Math.cos(rotationY), sinY = Math.sin(rotationY);
        const cosX = Math.cos(rotationX), sinX = Math.sin(rotationX);

        // ── Project 3D → 2D ───────────────────────────────────────────────
        nodes.forEach(node => {
            const rx = node.ox * cosY - node.oz * sinY;
            const rz = node.oz * cosY + node.ox * sinY;
            const ry = node.oy * cosX - rz * sinX;
            const finalZ = rz * cosX + node.oy * sinX;

            const focalLength = 600;
            const zOffset = SPHERE_RADIUS + 100;
            const scale = focalLength / (focalLength + finalZ + zOffset);

            node.x = cx + rx * scale;
            node.y = cy + ry * scale;
            node.z = finalZ;
            node.scale = scale;
        });

        // ── Connections ───────────────────────────────────────────────────
        ctx.lineWidth = 0.8;
        connections.forEach(([i, j]) => {
            const n1 = nodes[i], n2 = nodes[j];
            const avgZ = (n1.z + n2.z) / 2;
            const zNorm = (avgZ + SPHERE_RADIUS) / (SPHERE_RADIUS * 2);

            if (zNorm <= 0.18) return;

            const opacity = 0.04 + zNorm * 0.22;
            const gradient = ctx.createLinearGradient(n1.x, n1.y, n2.x, n2.y);
            gradient.addColorStop(0, `rgba(${n1.color}, ${opacity})`);
            gradient.addColorStop(1, `rgba(${n2.color}, ${opacity})`);

            ctx.beginPath();
            ctx.moveTo(n1.x, n1.y);
            ctx.lineTo(n2.x, n2.y);
            ctx.strokeStyle = gradient;
            ctx.stroke();
        });

        // ── Nodes (back → front) ──────────────────────────────────────────
        const sorted = [...nodes].sort((a, b) => b.z - a.z);

        sorted.forEach(node => {
            const zNorm = (node.z + SPHERE_RADIUS) / (SPHERE_RADIUS * 2);
            const opacity = 0.12 + zNorm * 0.88;
            const radius = Math.max(1.2, 2.2 * node.scale);

            ctx.beginPath();
            ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${node.color}, ${opacity})`;

            if (zNorm > 0.62) {
                ctx.shadowBlur = 12;
                ctx.shadowColor = `rgba(${node.color}, ${opacity * 0.8})`;
            } else {
                ctx.shadowBlur = 0;
            }

            ctx.fill();
        });

        ctx.shadowBlur = 0;
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Page Visibility API — recover when tab becomes visible again
    // ─────────────────────────────────────────────────────────────────────────
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible' && activeCanvas && rafId === null) {
            initNeuralSphereDeferred();
        }
    });

    // ─────────────────────────────────────────────────────────────────────────
    // HTMX hook — re-initialise after every content swap.
    // initNeuralSphere() is safe to call immediately — the debounced
    // ResizeObserver inside handles all layout timing automatically.
    // ─────────────────────────────────────────────────────────────────────────
    document.addEventListener('htmx:afterSwap', initNeuralSphere);

    // ─────────────────────────────────────────────────────────────────────────
    // First load
    // ─────────────────────────────────────────────────────────────────────────
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNeuralSphere);
    } else {
        initNeuralSphere();
    }
})();