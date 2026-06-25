import React from 'react';
import './CountdownTimer.css';

export default function CountdownTimer({ secondsLeft, isExpired }) {
  if (isExpired) {
    return <div style={{ color: '#ef4444', fontWeight: 'bold' }}>Time's up!</div>;
  }

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;
  const formatted = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

  let color = '#111827';
  let className = 'countdown-timer';

  if (secondsLeft < 30) {
    color = '#ef4444';
    className += ' pulse';
  } else if (secondsLeft < 60) {
    color = '#f59e0b';
  }

  return (
    <div className={className} style={{ color, fontWeight: 'bold', fontFamily: 'monospace', fontSize: '18px' }}>
      {formatted}
    </div>
  );
}
