<template>
  <div class="container py-4">
    <h4 class="fw-bold mb-4">All Applications</h4>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border"></div>
    </div>
    <div v-else-if="applications.length === 0" class="text-muted">
      No applications found.
    </div>

    <div v-else class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-dark">
          <tr>
            <th>Student</th>
            <th>Email</th>
            <th>Branch</th>
            <th>CGPA</th>
            <th>Job Title</th>
            <th>Company</th>
            <th>Applied On</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="app in applications" :key="app.id">
            <td class="fw-semibold">{{ app.student_name }}</td>
            <td>{{ app.student_email }}</td>
            <td>{{ app.student_branch }}</td>
            <td>{{ app.student_cgpa }}</td>
            <td>{{ app.job_title }}</td>
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
import { adminListApplications } from "../../api/index.js";

export default {
  name: "AdminApplications",
  data() {
    return { applications: [], loading: true };
  },
  async created() {
    try {
      this.applications = await adminListApplications();
    } catch (err) {
      console.error(err);
    } finally {
      this.loading = false;
    }
  },
  methods: {
    formatDate(iso) {
      if (!iso) return "—";
      return new Date(iso).toLocaleDateString();
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
