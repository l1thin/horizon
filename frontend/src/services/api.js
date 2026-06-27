const BASE = 'https://34.46.31.15:8000/';

// Disable Demo Mode to make real backend calls
const DEMO_MODE = false;

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

export async function submitCode(sessionId, payload) {
  if (DEMO_MODE) {
    await delay(1500); // Simulate processing
    return { status: 'Accepted', stdout: 'Test cases passed: 5/5', stderr: '' };
  }

  // Real implementation stub
  const res = await fetch(`${BASE}/api/sessions/${sessionId}/submit-code`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Submission failed');
  return res.json();
}
export async function getReport(sessionId) {
  if (DEMO_MODE) {
    await delay(2000);
    return {
      overall_score: 85,
      questions: [
        {
          question_id: 'q1',
          question_text: 'Tell me about a time you had a conflict with a coworker.',
          question_type: 'behavioral',
          score: 8,
          feedback: {
            what_was_good: 'You clearly explained the situation and the resolution.',
            what_was_missing: 'You didn\'t emphasize your active listening skills.',
            suggestions: ['Use the STAR method more explicitly', 'Highlight emotional intelligence']
          },
          depth_rating: 'adequate'
        },
        {
          question_id: 'q2',
          question_text: 'Reverse a linked list.',
          question_type: 'coding',
          score: 9,
          feedback: {
            what_was_good: 'Optimal O(N) time and O(1) space complexity.',
            what_was_missing: 'Edge cases for empty list could be mentioned earlier.',
            suggestions: ['Always state edge cases before writing code']
          },
          depth_rating: 'deep'
        }
      ],
      skill_gaps: [
        { skill: 'System Design', gap_score: 7 },
        { skill: 'Concurrency', gap_score: 5 },
        { skill: 'Testing', gap_score: 3 }
      ],
      integrity: {
        tab_switches: 1,
        fast_answer_questions: ['q1'],
        verdict: 'clean'
      }
    };
  }

  const res = await fetch(`${BASE}/api/sessions/${sessionId}/report`);
  if (!res.ok) throw new Error('Report fetch failed');
  return res.json();
}
