import React, { useState } from 'react';
import Orb from './components/orb/Orb';
import { ORB_STATE } from './components/orb/OrbStates';

function App() {
  const [orbState, setOrbState] = useState(ORB_STATE.IDLE);

  const states = Object.values(ORB_STATE);

  const cycleState = () => {
    const currentIndex = states.indexOf(orbState);
    const nextIndex = (currentIndex + 1) % states.length;
    setOrbState(states[nextIndex]);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', gap: '2rem' }}>
      <h1>AntiGravity Orb Demo</h1>
      <p>Current State: <strong>{orbState.toUpperCase()}</strong></p>
      
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Orb state={orbState} onClick={cycleState} />
      </div>

      <button 
        onClick={cycleState}
        style={{ padding: '10px 20px', fontSize: '16px', borderRadius: '8px', cursor: 'pointer', backgroundColor: '#333', color: 'white', border: '1px solid #555' }}
      >
        Click me or the Orb to cycle state
      </button>
    </div>
  );
}

export default App;
