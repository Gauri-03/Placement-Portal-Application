const BASE_URL = "http://localhost:5000";

function getToken() {
  return localStorage.getItem("token");
}

async function request(method, path, body = null, isFormData = false) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!isFormData && body) headers["Content-Type"] = "application/json";

  const options = { method, headers };
  if (body) options.body = isFormData ? body : JSON.stringify(body);

  const res = await fetch(`${BASE_URL}${path}`, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw { status: res.status, message: data.error || "Request failed" };
  return data;
}

const get = (path) => request("GET", path);
const post = (path, body) => request("POST", path, body);
const put = (path, body) => request("PUT", path, body);
const patch = (path, body = null) => request("PATCH", path, body);
const postForm = (path, formData) => request("POST", path, formData, true);

// ── Auth ──────────────────────────────────────────────
export const registerStudent = (data) => post("/api/auth/register/student", data);
export const registerCompany = (data) => post("/api/auth/register/company", data);
export const login = (data) => post("/api/auth/login", data);
export const getMe = () => get("/api/auth/me");

// ── Admin ─────────────────────────────────────────────
export const adminDashboard = () => get("/api/admin/dashboard");
export const adminListCompanies = (params = "") => get(`/api/admin/companies${params}`);
export const adminGetCompany = (id) => get(`/api/admin/companies/${id}`);
export const adminApproveCompany = (id) => patch(`/api/admin/companies/${id}/approve`);
export const adminRejectCompany = (id) => patch(`/api/admin/companies/${id}/reject`);
export const adminBlacklistCompany = (id) => patch(`/api/admin/companies/${id}/blacklist`);
export const adminListStudents = (params = "") => get(`/api/admin/students${params}`);
export const adminGetStudent = (id) => get(`/api/admin/students/${id}`);
export const adminBlacklistStudent = (id) => patch(`/api/admin/students/${id}/blacklist`);
export const adminGetStudentApplications = (id) => get(`/api/admin/students/${id}/applications`);
export const adminListDrives = (params = "") => get(`/api/admin/drives${params}`);
export const adminApproveDrive = (id) => patch(`/api/admin/drives/${id}/approve`);
export const adminRejectDrive = (id) => patch(`/api/admin/drives/${id}/reject`);
export const adminListApplications = () => get("/api/admin/applications");
export const adminTriggerDailyReminders = () => post("/api/admin/trigger/daily-reminders", {});
export const adminTriggerMonthlyReport = () => post("/api/admin/trigger/monthly-report", {});

// ── Company ───────────────────────────────────────────
export const companyDashboard = () => get("/api/company/dashboard");
export const companyGetProfile = () => get("/api/company/profile");
export const companyUpdateProfile = (data) => put("/api/company/profile", data);
export const companyListDrives = () => get("/api/company/drives");
export const companyCreateDrive = (data) => post("/api/company/drives", data);
export const companyGetDrive = (id) => get(`/api/company/drives/${id}`);
export const companyUpdateDrive = (id, data) => put(`/api/company/drives/${id}`, data);
export const companyCloseDrive = (id) => patch(`/api/company/drives/${id}/close`);
export const companyDriveApplications = (id) => get(`/api/company/drives/${id}/applications`);
export const companyUpdateAppStatus = (appId, status) =>
  patch(`/api/company/applications/${appId}/status`, { status });

// ── Student ───────────────────────────────────────────
export const studentGetProfile = () => get("/api/student/profile");
export const studentUpdateProfile = (data) => put("/api/student/profile", data);
export const studentUploadResume = (formData) => postForm("/api/student/profile/resume", formData);
export const studentDeleteResume = () => request("DELETE", "/api/student/profile/resume");
export const studentMyApplications = () => get("/api/student/applications");

// ── Drives ────────────────────────────────────────────
export const listDrives = (params = "") => get(`/api/drives${params}`);
export const getDrive = (id) => get(`/api/drives/${id}`);

// ── Applications ──────────────────────────────────────
export const applyToDrive = (driveId) => post("/api/applications", { drive_id: driveId });
export const getApplication = (id) => get(`/api/applications/${id}`);
export const exportApplications = () => post("/api/applications/export", {});

// Direct CSV download — fetches the file and triggers a browser download
export async function downloadApplicationsCSV() {
  const token = getToken();
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}/api/student/applications/export`, { method: "GET", headers });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw { status: res.status, message: data.error || "Export failed" };
  }

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  // Try to get filename from Content-Disposition header
  const disposition = res.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  a.download = match ? match[1] : "placement_history.csv";
  a.href = url;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
