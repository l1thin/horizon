import React from 'react';
import './Orb.css';
import { ORB_STATE } from './OrbStates';

export default function Orb({ state = ORB_STATE.IDLE, onClick }) {
  return (
    <div className="orb-container" onClick={onClick}>
      <div className={`orb ${state}`}>
        {state === ORB_STATE.THINKING && <div className="orb-inner-thinking"></div>}
      </div>
    </div>
  );
}
