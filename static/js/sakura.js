(() => {
  const canvas = document.getElementById("sakura");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  let W, H;

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  window.addEventListener("resize", resize);
  resize();

  function rand(a, b) { return a + Math.random() * (b - a); }
  function randInt(a, b) { return Math.floor(rand(a, b)); }

  // ── Petal (small oval leaf shapes in warm tones) ──
  function makePetal() {
    const hues = [90, 110, 130, 145, 80, 160]; // various greens and teals
    return {
      type: "petal",
      x: rand(-100, W),
      y: rand(-H, 0),
      r: rand(3, 7),
      s: rand(0.5, 1.4),
      vx: rand(1.5, 3.5), // wind flowing right
      vy: rand(0.8, 1.5),
      rot: rand(0, Math.PI * 2),
      vr: rand(-0.018, 0.018),
      hue: hues[randInt(0, hues.length)],
      sat: rand(65, 90),
      lit: rand(60, 80),
      alpha: rand(0.30, 0.65),
      wobble: rand(0, Math.PI * 2),
      wobbleSpeed: rand(0.02, 0.05),
    };
  }

  function drawPetal(p) {
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.rot);
    ctx.globalAlpha = p.alpha;
    ctx.beginPath();
    ctx.moveTo(0, -p.r);
    ctx.bezierCurveTo(p.r * 0.9, -p.r, p.r * 1.1, p.r * 0.3, 0, p.r);
    ctx.bezierCurveTo(-p.r * 1.1, p.r * 0.3, -p.r * 0.9, -p.r, 0, -p.r);
    ctx.closePath();
    ctx.fillStyle = `hsla(${p.hue}, ${p.sat}%, ${p.lit}%, ${p.alpha})`;
    ctx.shadowColor = `hsla(${p.hue}, 80%, 70%, 0.4)`;
    ctx.shadowBlur = 6;
    ctx.fill();
    ctx.restore();
  }

  // ── Butterfly ──
  function makeButterfly() {
    const palettes = [
      { body: "#ffe066", wing1: "#ffb700", wing2: "#fff3a0", accent: "#ff8c00" }, // golden
      { body: "#b8f5a0", wing1: "#5ecf3e", wing2: "#e0ffcc", accent: "#2a8a10" }, // forest green
      { body: "#ffd6b0", wing1: "#ff7730", wing2: "#ffe8cc", accent: "#c94400" }, // amber
      { body: "#ffffff", wing1: "#e8f8ff", wing2: "#ffffff", accent: "#a0d8ef" }, // white
      { body: "#ffc8e0", wing1: "#ff85b0", wing2: "#ffe0ee", accent: "#d63870" }, // soft pink
    ];
    const pal = palettes[randInt(0, palettes.length)];
    return {
      type: "butterfly",
      x: rand(0, W),
      y: rand(-200, H * 0.6),
      size: rand(10, 20),
      vx: rand(-0.5, 0.5),
      vy: rand(0.15, 0.45),
      flapPhase: rand(0, Math.PI * 2),
      flapSpeed: rand(0.07, 0.14),
      wobbleX: rand(0, Math.PI * 2),
      wobbleXSpeed: rand(0.015, 0.04),
      alpha: rand(0.5, 0.82),
      pal,
      driftDir: Math.random() > 0.5 ? 1 : -1,
      driftAmp: rand(0.3, 1.0),
    };
  }

  function drawButterfly(b) {
    const flap = Math.sin(b.flapPhase);       // -1..1
    const openness = Math.abs(flap);          // 0..1 (0=closed, 1=open)
    const sz = b.size;
    const p = b.pal;

    ctx.save();
    ctx.translate(b.x, b.y);
    ctx.globalAlpha = b.alpha;

    // Upper wings
    for (const side of [-1, 1]) {
      ctx.save();
      ctx.scale(side, 1);
      // skew to simulate wing fold
      ctx.transform(1, 0, (1 - openness) * 0.5 * side, 1, 0, 0);

      // upper wing
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.bezierCurveTo(sz * 0.4, -sz * 1.1, sz * 1.6, -sz * 0.9, sz * 1.5, sz * 0.1);
      ctx.bezierCurveTo(sz * 1.4, sz * 0.6, sz * 0.3, sz * 0.4, 0, 0);
      ctx.closePath();
      const gU = ctx.createLinearGradient(0, -sz, sz * 1.5, sz * 0.2);
      gU.addColorStop(0, p.wing2 + "ee");
      gU.addColorStop(0.45, p.wing1 + "cc");
      gU.addColorStop(1, p.accent + "99");
      ctx.fillStyle = gU;
      ctx.shadowColor = p.wing1;
      ctx.shadowBlur = 8;
      ctx.fill();

      // lower wing
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.bezierCurveTo(sz * 0.5, sz * 0.3, sz * 1.3, sz * 0.8, sz * 1.1, sz * 1.4);
      ctx.bezierCurveTo(sz * 0.8, sz * 1.8, sz * 0.2, sz * 1.2, 0, sz * 0.6);
      ctx.closePath();
      const gL = ctx.createLinearGradient(0, 0, sz, sz * 1.5);
      gL.addColorStop(0, p.wing1 + "bb");
      gL.addColorStop(1, p.accent + "77");
      ctx.fillStyle = gL;
      ctx.shadowBlur = 6;
      ctx.fill();

      // wing pattern dot
      ctx.beginPath();
      ctx.arc(sz * 0.75, -sz * 0.3, sz * 0.12, 0, Math.PI * 2);
      ctx.fillStyle = p.accent + "99";
      ctx.shadowBlur = 0;
      ctx.fill();

      ctx.restore();
    }

    // Body
    ctx.beginPath();
    ctx.ellipse(0, sz * 0.3, sz * 0.09, sz * 0.7, 0, 0, Math.PI * 2);
    ctx.fillStyle = p.body;
    ctx.shadowBlur = 0;
    ctx.globalAlpha = b.alpha * 0.9;
    ctx.fill();

    // Antennae
    ctx.globalAlpha = b.alpha * 0.6;
    ctx.strokeStyle = p.body;
    ctx.lineWidth = 0.8;
    for (const side of [-1, 1]) {
      ctx.beginPath();
      ctx.moveTo(0, -sz * 0.2);
      ctx.quadraticCurveTo(side * sz * 0.5, -sz * 1.1, side * sz * 0.6, -sz * 1.3);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(side * sz * 0.6, -sz * 1.3, sz * 0.06, 0, Math.PI * 2);
      ctx.fillStyle = p.accent;
      ctx.fill();
    }

    ctx.restore();
  }

  // ── Firefly (glowing dots) ──
  function makeFirefly() {
    return {
      type: "firefly",
      x: rand(0, W),
      y: rand(0, H),
      r: rand(1.5, 3),
      vx: rand(-0.3, 0.3),
      vy: rand(-0.3, 0.3),
      wobble: rand(0, Math.PI * 2),
      wobbleSpeed: rand(0.01, 0.03),
      alpha: rand(0.1, 0.8),
      pulseSpeed: rand(0.02, 0.05),
      pulsePhase: rand(0, Math.PI * 2)
    };
  }

  function drawFirefly(f) {
    const currentAlpha = f.alpha + Math.sin(f.pulsePhase) * 0.3;
    if (currentAlpha <= 0) return;
    
    ctx.save();
    ctx.translate(f.x, f.y);
    ctx.globalAlpha = Math.min(1, Math.max(0, currentAlpha));
    ctx.beginPath();
    ctx.arc(0, 0, f.r, 0, Math.PI * 2);
    ctx.fillStyle = "#ffffff";
    ctx.shadowColor = "#fcfcca";
    ctx.shadowBlur = 12;
    ctx.fill();
    ctx.restore();
  }

  // ── Spawn particles ──
  const PETALS = 120; // Added more leaves
  const FIREFLIES = 40; // Light particles
  const BUTTERFLIES = 0;
  let particles = [];
  for (let i = 0; i < PETALS; i++) particles.push(makePetal());
  for (let i = 0; i < FIREFLIES; i++) particles.push(makeFirefly());
  for (let i = 0; i < BUTTERFLIES; i++) particles.push(makeButterfly());

  // ── Tick ──
  function tick() {
    ctx.clearRect(0, 0, W, H);

    for (const p of particles) {
      if (p.type === "petal") {
        p.wobble += p.wobbleSpeed;
        p.x += p.vx * p.s + Math.sin(p.wobble) * 0.4;
        p.y += p.vy * p.s;
        p.rot += p.vr;

        if (p.y > H + 20 || p.x < -50 || p.x > W + 50) {
          Object.assign(p, makePetal(), { x: rand(0, W), y: rand(-40, -10) });
        }
        drawPetal(p);

      } else if (p.type === "firefly") {
        p.pulsePhase += p.pulseSpeed;
        p.wobble += p.wobbleSpeed;
        p.x += p.vx + Math.sin(p.wobble) * 0.5;
        p.y += p.vy - 0.2; // fireflies tend to drift upward

        if (p.y < -20 || p.x < -20 || p.x > W + 20) {
          Object.assign(p, makeFirefly(), { x: rand(0, W), y: H + 20 });
        }
        drawFirefly(p);

      } else {
        // butterfly
        p.flapPhase += p.flapSpeed;
        p.wobbleX += p.wobbleXSpeed;
        p.x += p.vx + Math.sin(p.wobbleX) * p.driftAmp * p.driftDir;
        p.y += p.vy;

        if (p.y > H + 40 || p.x < -80 || p.x > W + 80) {
          const nb = makeButterfly();
          nb.x = rand(-20, W + 20);
          nb.y = rand(-60, -20);
          Object.assign(p, nb);
        }
        drawButterfly(p);
      }
    }

    requestAnimationFrame(tick);
  }

  tick();
})();