import React, { useEffect, useState } from 'react';

const ConfettiBurst = ({ active = false, onComplete }) => {
  const [particles, setParticles] = useState([]);

  useEffect(() => {
    if (!active) return;

    const colors = ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#3b82f6'];
    const newParticles = Array.from({ length: 40 }, (_, i) => ({
      id: i,
      x: 50,
      y: 50,
      angle: Math.random() * Math.PI * 2,
      speed: Math.random() * 8 + 4,
      size: Math.random() * 6 + 4,
      color: colors[Math.floor(Math.random() * colors.length)],
      opacity: 1
    }));

    setParticles(newParticles);

    const timer = setTimeout(() => {
      setParticles([]);
      if (onComplete) onComplete();
    }, 2000);

    return () => clearTimeout(timer);
  }, [active, onComplete]);

  if (!active || particles.length === 0) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
      {particles.map((p) => (
        <span
          key={p.id}
          className="absolute rounded-full animate-ping"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: `${p.size}px`,
            height: `${p.size}px`,
            backgroundColor: p.color,
            transform: `translate(${Math.cos(p.angle) * p.speed * 20}px, ${Math.sin(p.angle) * p.speed * 20}px)`
          }}
        />
      ))}
    </div>
  );
};

export default ConfettiBurst;
