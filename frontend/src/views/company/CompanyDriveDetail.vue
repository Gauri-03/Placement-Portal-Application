<template>
  <div class="container py-4">
    <div class="d-flex align-items-center mb-4">
      <router-link
        to="/company/dashboard"
        class="btn btn-outline-secondary btn-sm me-3"
      >
        <i class="bi bi-arrow-left"></i>
      </router-link>
      <h4 class="fw-bold mb-0">Drive Detail</h4>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border"></div>
    </div>

    <div v-else>
      <div class="card mb-4">
        <div class="card-body">
          <div v-if="!editing">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <h5 class="fw-bold">{{ drive.job_title }}</h5>
                <p class="text-muted mb-2" v-if="drive.job_description">
                  {{ drive.job_description }}
                </p>
                <div class="d-flex flex-wrap gap-2 mb-2">
                  <span
                    class="badge bg-light text-dark border"
                    v-if="drive.min_cgpa"
                  >
                    Min CGPA: {{ drive.min_cgpa }}
                  </span>
                  <span
                    class="badge bg-light text-dark border"
                    v-if="
                      drive.eligible_branches && drive.eligible_branches.length
                    "
                  >
                    Branches: {{ drive.eligible_branches.join(", ") }}
                  </span>
                  <span
                    class="badge bg-light text-dark border"
                    v-if="drive.eligible_years && drive.eligible_years.length"
                  >
                    Years: {{ drive.eligible_years.join(", ") }}
                  </span>
                </div>
                <p class="text-muted small mb-0">
                  Deadline: {{ formatDate(drive.application_deadline) }}
                </p>
              </div>
              <div class="d-flex flex-column align-items-end gap-2">
                <span :class="statusBadge(drive.status)">{{
                  drive.status
                }}</span>
                <button
                  v-if="drive.status === 'pending'"
                  class="btn btn-outline-primary btn-sm"
                  @click="startEdit"
                >
                  <i class="bi bi-pencil me-1"></i> Edit Drive
                </button>
                <button
                  v-if="drive.status === 'approved'"
                  class="btn btn-outline-secondary btn-sm"
                  @click="closeDrive"
                >
                  Close Drive
                </button>
              </div>
            </div>
          </div>

          <div v-else>
            <h6 class="fw-semibold mb-3">Edit Drive</h6>
            <div v-if="editError" class="alert alert-danger py-2 small">
              {{ editError }}
            </div>
            <form @submit.prevent="saveEdit">
            <div class="mb-3">
              <label class="form-label fw-semibold"
                >Job Title <span class="text-danger">*</span></label
              >
              <input
                v-model="editForm.job_title"
                type="text"
                class="form-control"
                required
              />
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">Job Description <span class="text-danger">*</span></label>
              <textarea
                v-model="editForm.job_description"
                class="form-control"
                rows="3"
                required
              ></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold"
                >Application Deadline <span class="text-danger">*</span></label
              >
              <input
                v-model="editForm.application_deadline"
                type="datetime-local"
                class="form-control"
                required
              />
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">Eligible Branches</label>
              <input
                v-model="editForm.branchInput"
                type="text"
                class="form-control"
                placeholder="e.g. CS, ECE, ME (comma-separated)"
              />
            </div>
            <div class="row">
              <div class="col mb-3">
                <label class="form-label fw-semibold">Minimum CGPA</label>
                <input
                  v-model="editForm.min_cgpa"
                  type="number"
                  step="0.1"
                  min="0"
                  max="10"
                  class="form-control"
                />
              </div>
              <div class="col mb-3">
                <label class="form-label fw-semibold">Eligible Years</label>
                <input
                  v-model="editForm.yearInput"
                  type="text"
                  class="form-control"
                  placeholder="e.g. 3, 4"
                />
              </div>
            </div>
            <div class="d-flex gap-2">
              <button
                type="submit"
                class="btn btn-dark btn-sm"
                :disabled="editLoading"
              >
                <span
                  v-if="editLoading"
                  class="spinner-border spinner-border-sm me-1"
                ></span>
                Save Changes
              </button>
              <button
                type="button"
                class="btn btn-outline-secondary btn-sm"
                @click="cancelEdit"
              >
                Cancel
              </button>
            </div>
            </form>
          </div>
        </div>
      </div>

      <h5 class="fw-semibold mb-3">
        Applications
        <span class="badge bg-secondary ms-2">{{ applications.length }}</span>
      </h5>

      <div v-if="applications.length === 0" class="text-muted">
        No applications yet.
      </div>

      <div v-else class="table-responsive">
        <table class="table table-hover align-middle">
          <thead class="table-dark">
            <tr>
              <th>Student</th>
              <th>Email</th>
              <th>Branch</th>
              <th>CGPA</th>
              <th>Applied</th>
              <th>Status</th>
              <th>Update Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="app in applications" :key="app.id">
              <td class="fw-semibold">{{ app.student_name }}</td>
              <td>{{ app.student_email }}</td>
              <td>{{ app.student_branch }}</td>
              <td>{{ app.student_cgpa }}</td>
              <td>{{ formatDate(app.applied_at) }}</td>
              <td>
                <span :class="appStatusBadge(app.status)">{{
                  app.status
                }}</span>
              </td>
              <td>
                <select
                  class="form-select form-select-sm"
                  style="min-width: 130px"
                  :value="app.status"
                  @change="updateStatus(app, $event.target.value)"
                >
                  <option value="shortlisted">Shortlisted</option>
                  <option value="selected">Selected</option>
                  <option value="rejected">Rejected</option>
                </select>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import {
  companyGetDrive,
  companyDriveApplications,
  companyUpdateAppStatus,
  companyCloseDrive,
  companyUpdateDrive,
} from "../../api/index.js";

export default {
  name: "CompanyDriveDetail",
  data() {
    return {
      drive: {},
      applications: [],
      loading: true,
      editing: false,
      editLoading: false,
      editError: "",
      editForm: {
        job_title: "",
        job_description: "",
        application_deadline: "",
        branchInput: "",
        yearInput: "",
        min_cgpa: "",
      },
    };
  },
  async created() {
    const id = this.$route.params.id;
    try {
      const [drive, apps] = await Promise.all([
        companyGetDrive(id),
        companyDriveApplications(id),
      ]);
      this.drive = drive;
      this.applications = apps;
    } catch (err) {
      console.error(err);
    } finally {
      this.loading = false;
    }
  },
  methods: {
    startEdit() {
      this.editForm.job_title = this.drive.job_title || "";
      this.editForm.job_description = this.drive.job_description || "";
      if (this.drive.application_deadline) {
        const dt = new Date(this.drive.application_deadline);
        const pad = (n) => String(n).padStart(2, "0");
        this.editForm.application_deadline = `${dt.getFullYear()}-${pad(
          dt.getMonth() + 1,
        )}-${pad(dt.getDate())}T${pad(dt.getHours())}:${pad(dt.getMinutes())}`;
      } else {
        this.editForm.application_deadline = "";
      }
      this.editForm.branchInput = this.drive.eligible_branches
        ? this.drive.eligible_branches.join(", ")
        : "";
      this.editForm.yearInput = this.drive.eligible_years
        ? this.drive.eligible_years.join(", ")
        : "";
      this.editForm.min_cgpa =
        this.drive.min_cgpa != null ? this.drive.min_cgpa : "";
      this.editError = "";
      this.editing = true;
    },
    cancelEdit() {
      this.editing = false;
      this.editError = "";
    },
    async saveEdit() {
      this.editError = "";
      if (!this.editForm.job_title.trim()) {
        this.editError = "Job title is required.";
        return;
      }
      this.editLoading = true;
      try {
        const payload = {
          job_title: this.editForm.job_title.trim(),
          job_description: this.editForm.job_description.trim() || null,
          application_deadline: this.editForm.application_deadline,
          min_cgpa:
            this.editForm.min_cgpa !== ""
              ? parseFloat(this.editForm.min_cgpa)
              : null,
          eligible_branches: this.editForm.branchInput
            ? this.editForm.branchInput
                .split(",")
                .map((b) => b.trim())
                .filter(Boolean)
            : null,
          eligible_years: this.editForm.yearInput
            ? this.editForm.yearInput
                .split(",")
                .map((y) => parseInt(y.trim()))
                .filter((y) => !isNaN(y))
            : null,
        };
        const res = await companyUpdateDrive(this.drive.id, payload);
        this.drive = res.drive;
        this.editing = false;
      } catch (err) {
        this.editError = err.message || "Failed to update drive.";
      } finally {
        this.editLoading = false;
      }
    },
    async updateStatus(app, newStatus) {
      if (newStatus === app.status) return;
      try {
        await companyUpdateAppStatus(app.id, newStatus);
        app.status = newStatus;
      } catch (err) {
        alert(err.message || "Failed to update status");
      }
    },
    async closeDrive() {
      if (!confirm("Close this drive? No more applications will be accepted."))
        return;
      try {
        await companyCloseDrive(this.drive.id);
        this.drive.status = "closed";
      } catch (err) {
        alert(err.message || "Failed to close drive");
      }
    },
    formatDate(iso) {
      if (!iso) return "—";
      return new Date(iso).toLocaleDateString();
    },
    statusBadge(status) {
      return (
        {
          pending: "badge bg-warning text-dark",
          approved: "badge bg-success",
          rejected: "badge bg-danger",
          closed: "badge bg-secondary",
        }[status] || "badge bg-secondary"
      );
    },
    appStatusBadge(status) {
      return (
        {
          applied: "badge bg-info text-dark",
          shortlisted: "badge bg-warning text-dark",
          selected: "badge bg-success",
          rejected: "badge bg-danger",
        }[status] || "badge bg-secondary"
      );
    },
  },
};
</script>
