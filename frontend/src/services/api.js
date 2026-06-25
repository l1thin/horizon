const BASE = import.meta.env.VITE_API_BASE_URL || '';

// Enable Demo Mode to bypass real backend calls
const DEMO_MODE = true;

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

export async function uploadResume(file) {
  if (DEMO_MODE) {
    await delay(1500); // simulate 1.5s network upload
    return { session_id: 'demo-session-123' };
  }
  
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE}/api/upload-resume`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();  // returns { session_id }
}

let pollCount = 0;
export async function getSessionStatus(sessionId) {
  if (DEMO_MODE) {
    await delay(500);
    pollCount++;
    // Simulate processing for a bit, then returning "ready" after 3 polls
    if (pollCount >= 3) {
      pollCount = 0; // reset
      return { status: "ready" };
    }
    return { status: "processing" };
  }

  const res = await fetch(`${BASE}/api/sessions/${sessionId}/status`);
  if (!res.ok) throw new Error('Status check failed');
  return res.json();  // returns { status: "processing" | "ready" | "error" }
}

export async function createSession(sessionId, preferredLanguage) {
  if (DEMO_MODE) {
    await delay(1000); // simulate 1s network request
    return { success: true };
  }

  const res = await fetch(`${BASE}/api/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, preferred_language: preferredLanguage })
  });
  if (!res.ok) throw new Error('Session creation failed');
  return res.json();
}

// Stub the rest — Dev 1 will fill these in later prompts:
export async function submitCode(sessionId, payload) { /* TODO */ }
export async function getReport(sessionId) { /* TODO */ }
