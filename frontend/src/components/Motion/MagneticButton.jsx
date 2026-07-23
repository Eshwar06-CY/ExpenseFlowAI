import React, { useRef, useState } from 'react';

const MagneticButton = ({ children, onClick, className = '', icon }) => {
  const buttonRef = useRef(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e) => {
    if (!buttonRef.current) return;
    const rect = buttonRef.current.getBoundingClientRect();
    const x = (e.clientX - (rect.left + rect.width / 2)) * 0.25;
    const y = (e.clientY - (rect.top + rect.height / 2)) * 0.25;
    setPosition({ x, y });
  };

  const handleMouseLeave = () => {
    setPosition({ x: 0, y: 0 });
  };

  return (
    <button
      ref={buttonRef}
      onClick={onClick}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        transform: `translate3d(${position.x}px, ${position.y}px, 0px)`,
        transition: position.x === 0 ? 'transform 0.4s ease-out' : 'transform 0.1s ease-out'
      }}
      className={`relative group px-6 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-lg hover:shadow-indigo-500/30 flex items-center justify-center space-x-2 border border-indigo-400/30 ${className}`}
    >
      <span className="relative z-10 flex items-center space-x-2">
        {icon}
        <span>{children}</span>
      </span>
      {/* Electric Glow Pulse */}
      <span className="absolute inset-0 rounded-2xl bg-indigo-500/20 blur-md group-hover:blur-lg transition-all opacity-0 group-hover:opacity-100" />
    </button>
  );
};

export default MagneticButton;
