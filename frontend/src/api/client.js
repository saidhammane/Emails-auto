import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
  timeout: 30000,
});

export function getApiErrorMessage(error, fallbackMessage) {
  const responseMessage = error?.response?.data?.message;
  const detailMessage = error?.response?.data?.detail;

  if (typeof responseMessage === "string" && responseMessage.trim()) {
    return responseMessage;
  }

  if (typeof detailMessage === "string" && detailMessage.trim()) {
    return detailMessage;
  }

  return fallbackMessage;
}

export default apiClient;
