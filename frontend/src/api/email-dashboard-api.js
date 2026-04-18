import apiClient from "./client";

function buildMultipartPayload(fields) {
  const formData = new FormData();

  Object.entries(fields).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      formData.append(key, value);
    }
  });

  return formData;
}

export async function getAnalyticsSummary() {
  const response = await apiClient.get("/analytics/summary");
  return response.data;
}

export async function getAnalyticsDaily() {
  const response = await apiClient.get("/analytics/daily");
  return response.data;
}

export async function getAnalyticsErrors() {
  const response = await apiClient.get("/analytics/errors");
  return response.data;
}

export async function getEmailLogs() {
  const response = await apiClient.get("/email-logs");
  return response.data;
}

export async function sendTestEmail(payload) {
  const response = await apiClient.post("/send-test-email", payload);
  return response.data;
}

export async function sendBulkEmail(payload) {
  const response = await apiClient.post(
    "/send-bulk-email",
    buildMultipartPayload(payload),
  );
  return response.data;
}

export async function scheduleEmail(payload) {
  const response = await apiClient.post("/schedule-email", payload);
  return response.data;
}

export async function scheduleBulkEmail(payload) {
  const response = await apiClient.post(
    "/schedule-bulk-email",
    buildMultipartPayload(payload),
  );
  return response.data;
}
