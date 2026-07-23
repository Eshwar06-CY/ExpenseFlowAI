import React, { useEffect, useRef } from 'react';

const AIOrb = ({ size = 260, className = '' }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = size;
    canvas.height = size;

    let animId;
    let time = 0;

    let mouseX = size / 2;
    let mouseY = size / 2;

    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      mouseX = e.clientX - rect.left;
      mouseY = e.clientY - rect.top;
    };
    window.addEventListener('mousemove', handleMouseMove);

    const render = () => {
      time += 0.03;
      ctx.clearRect(0, 0, size, size);

      const cx = size / 2 + (mouseX - size / 2) * 0.08;
      const cy = size / 2 + (mouseY - size / 2) * 0.08;

      // Outer Energy Glow Ring
      const outerGlow = ctx.createRadialGradient(cx, cy, 20, cx, cy, size / 2);
      outerGlow.addColorStop(0, 'rgba(99, 102, 241, 0.4)');
      outerGlow.addColorStop(0.5, 'rgba(6, 182, 212, 0.2)');
      outerGlow.addColorStop(1, 'rgba(15, 23, 42, 0)');

      ctx.fillStyle = outerGlow;
      ctx.beginPath();
      ctx.arc(cx, cy, size / 2, 0, Math.PI * 2);
      ctx.fill();

      // Pulsing Core Glass Spheres
      const pulseSize = (size / 3.5) + Math.sin(time * 2) * 6;
      const coreGrad = ctx.createRadialGradient(cx - 10, cy - 10, 5, cx, cy, pulseSize);
      coreGrad.addColorStop(0, '#ffffff');
      coreGrad.addColorStop(0.3, '#818cf8');
      coreGrad.addColorStop(0.7, '#4f46e5');
      coreGrad.addColorStop(1, '#06b6d4');

      ctx.fillStyle = coreGrad;
      ctx.shadowColor = '#6366f1';
      ctx.shadowBlur = 25;
      ctx.beginPath();
      ctx.arc(cx, cy, pulseSize, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;

      // Orbiting Particle Waves
      for (let i = 0; i < 3; i++) {
        const angle = time + (i * Math.PI * 2) / 3;
        const orbitRadius = pulseSize + 25 + Math.sin(time + i) * 8;
        const px = cx + Math.cos(angle) * orbitRadius;
        const py = cy + Math.sin(angle) * orbitRadius;

        ctx.fillStyle = i % 2 === 0 ? '#10b981' : '#38bdf8';
        ctx.beginPath();
        ctx.arc(px, py, 4, 0, Math.PI * 2);
        ctx.fill();
      }

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animId);
    };
  }, [size]);

  return (
    <div className={`relative inline-block ${className}`}>
      <canvas ref={canvasRef} className="pointer-events-auto cursor-pointer" />
    </div>
  );
};

export default AIOrb;
