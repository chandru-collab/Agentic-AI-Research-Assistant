const API_BASE_URL = 'http://127.0.0.1:8000';

/**
 * Handle fetch response and parse as JSON, throwing standard errors for status codes.
 */
async function handleResponse(response) {
  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
    } catch (_) {
      // Ignore JSON parse errors for non-JSON error pages
    }
    throw new Error(errorMessage);
  }
  return response.json();
}

export const api = {
  /**
   * Check if backend is alive
   */
  async healthCheck() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      return await handleResponse(response);
    } catch (error) {
      console.error('Backend health check failed:', error);
      return { status: 'offline', error: error.message };
    }
  },

  /**
   * Run the AI research pipeline on a topic
   */
  async runResearch(query, model = null) {
    const payload = { query };
    if (model) {
      payload.model = model;
    }

    const response = await fetch(`${API_BASE_URL}/research`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    return await handleResponse(response);
  },

  /**
   * Get past research sessions
   */
  async getHistory() {
    const response = await fetch(`${API_BASE_URL}/history`);
    return await handleResponse(response);
  },

  /**
   * Get a specific report
   */
  async getReport(sessionId) {
    const response = await fetch(`${API_BASE_URL}/report/${sessionId}`);
    return await handleResponse(response);
  },

  /**
   * Export the report as PDF (returns a Blob)
   */
  async exportPDF(sessionId) {
    const response = await fetch(`${API_BASE_URL}/export/pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ session_id: sessionId }),
    });

    if (!response.ok) {
      let errorMessage = 'Failed to generate PDF';
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorMessage;
      } catch (_) {}
      throw new Error(errorMessage);
    }

    return await response.blob();
  },

  /**
   * Export the report as Markdown (returns text)
   */
  async exportMarkdown(sessionId) {
    const response = await fetch(`${API_BASE_URL}/export/markdown`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ session_id: sessionId }),
    });

    if (!response.ok) {
      let errorMessage = 'Failed to generate Markdown';
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorMessage;
      } catch (_) {}
      throw new Error(errorMessage);
    }

    return await response.text();
  },
};
