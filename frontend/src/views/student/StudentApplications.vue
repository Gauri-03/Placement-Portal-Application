<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h4 class="fw-bold mb-0">My Applications</h4>
      <button
        class="btn btn-outline-dark btn-sm"
        @click="exportCSV"
        :disabled="exportLoading"
      >
        <span v-if="exportLoading" class="spinner-border spinner-border-sm me-1"></span>
        <i v-else class="bi bi-download me-1"></i> Export History
      </button>
    </div>

    <div v-if="exportMessage" class="alert alert-success py-2 small">{{ exportMessage }}</div>
    <div v-if="exportError" class="alert alert-danger py-2 small">{{ exportError }}</div>

    <div v-if="loading" class="text-center py-5"><div class="spinner-border"></div></div>
    <div v-else-if="applications.length === 0" class="text-muted">
      You haven't applied to any drives yet.
      <router-link to="/student/dashboard">Browse drives</router-link>
    </div>

    <div v-else class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-dark">
          <tr>
            <th>Job Title</th>
            <th>Company</th>
            <th>Applied On</th>
            <th>Application Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="app in applications" :key="app.id">
            <td class="fw-semibold">{{ app.job_title }}</td>
            <td>{{ app.company_name }}</td>
            <td>{{ formatDate(app.applied_at) }}</td>
            <td>
              <span :class="appStatusBadge(app.status)">{{ app.status }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { studentMyApplications, downloadApplicationsCSV } from "../../api/index.js";

export default {
  name: "StudentApplications",
  data() {
    return {
      applications: [],
      loading: true,
      exportLoading: false,
      exportMessage: "",
      exportError: "",
    };
  },
  async created() {
    try {
      this.applications = await studentMyApplications();
    } catch (err) {
      console.error(err);
    } finally {
      this.loading = false;
    }
  },
  methods: {
    async exportCSV() {
      this.exportMessage = "";
      this.exportError = "";
      this.exportLoading = true;
      try {
        await downloadApplicationsCSV();
        this.exportMessage = "CSV downloaded successfully!";
      } catch (err) {
        this.exportError = err.message || "Failed to download CSV.";
      } finally {
        this.exportLoading = false;
      }
    },
    formatDate(iso) {
      if (!iso) return "—";
      return new Date(iso).toLocaleDateString();
    },
    appStatusBadge(status) {
      return {
        applied: "badge bg-info text-dark",
        shortlisted: "badge bg-warning text-dark",
        selected: "badge bg-success",
        rejected: "badge bg-danger",
      }[status] || "badge bg-secondary";
    },
  },
};
</script>
