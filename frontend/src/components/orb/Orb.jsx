import React, { useEffect, useRef } from 'react';
import { ORB_STATE } from './OrbStates';
import { initOrb } from './OrbRenderer';
import './Orb.css';

export default function Orb({ state = ORB_STATE.IDLE, onClick }) {
  const canvasRef = useRef(null);
  const orbControllerRef = useRef(null);

  useEffect(() => {
    if (canvasRef.current && !orbControllerRef.current) {
      orbControllerRef.current = initOrb(canvasRef.current);
      orbControllerRef.current.setState(state);
    }
    
    return () => {
      if (orbControllerRef.current) {
        orbControllerRef.current.dispose();
        orbControllerRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (orbControllerRef.current) {
      orbControllerRef.current.setState(state);
    }
  }, [state]);

  return (
    <div className="orb-container" onClick={onClick}>
      <canvas ref={canvasRef} style={{ width: '100%', height: '100%', cursor: 'pointer', display: 'block' }} />
    </div>
  );
}
