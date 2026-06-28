const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function evaluateCases(file) {
  const formData = new FormData();
  if (file) {
    formData.append("file", file);
  }

  const response = await fetch(`${API_BASE}/evaluate`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Evaluation failed");
  }

  return response.json();
}

export async function fetchReport() {
  const response = await fetch(`${API_BASE}/report`);
  if (!response.ok) {
    throw new Error("Failed to load report");
  }
  return response.text();
}
