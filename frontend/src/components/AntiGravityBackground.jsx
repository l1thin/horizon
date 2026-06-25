import React, { useMemo } from 'react';
import './AntiGravityBackground.css';

export default function AntiGravityBackground({ isActive = true }) {
  const cards = useMemo(() => {
    return Array.from({ length: 15 }).map((_, i) => {
      // Golden angle in radians
      const angle = i * 137.5 * (Math.PI / 180);
      
      // Radius expands outward. Using vmin for responsiveness.
      // Leave center relatively empty (start at 20 vmin)
      const radius = 20 + i * 3; 
      
      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius;
      
      // Chaotic static rotation
      const staticRotation = (i * 67) % 360;
      
      // Slight scale differences
      const scale = 0.7 + (i % 4) * 0.15;
      
      // Staggered animation durations (4s to 8s)
      const animDuration = 4 + (i % 5);
      
      // Staggered animation delay
      const animDelay = -(i % 7);

      return { x, y, staticRotation, scale, animDuration, animDelay };
    });
  }, []);

  return (
    <div className="anti-gravity-container">
      {cards.map((card, i) => (
        <div
          key={i}
          className="anti-gravity-card-wrapper"
          style={{
            top: `calc(50% + ${card.y}vmin)`,
            left: `calc(50% + ${card.x}vmin)`,
            transform: isActive 
              ? `translate(-50%, -50%) scale(${card.scale}) rotate(${card.staticRotation}deg)`
              : `translate(calc(-50% + ${card.x * 2}vmin), calc(-50% + ${card.y * 2}vmin)) scale(0) rotate(${card.staticRotation + 180}deg)`,
            transition: 'transform 1.2s cubic-bezier(0.4, 0, 0.2, 1), opacity 1.2s ease-in-out',
            opacity: isActive ? 1 : 0,
          }}
        >
          <div 
            className="anti-gravity-card"
            style={{
              animationDuration: `${card.animDuration}s`,
              animationDelay: `${card.animDelay}s`,
            }}
          >
            <div className="card-line" style={{ width: '80%' }}></div>
            <div className="card-line" style={{ width: '60%' }}></div>
            <div className="card-line" style={{ width: '70%' }}></div>
          </div>
        </div>
      ))}
    </div>
  );
}
