<template>
  <div class="container py-4">
    <div class="d-flex align-items-center mb-4">
      <router-link
        to="/admin/students"
        class="btn btn-outline-secondary btn-sm me-3"
      >
        <i class="bi bi-arrow-left"></i>
      </router-link>
      <div>
        <h4 class="fw-bold mb-0">Student Applications</h4>
        <p class="text-muted small mb-0" v-if="student">
          {{ student.full_name }} &mdash; {{ student.email }} &mdash;
          {{ student.branch }}, Year {{ student.year }}, CGPA {{ student.cgpa }}
        </p>
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border"></div>
    </div>
    <div v-else-if="applications.length === 0" class="text-muted">
      This student has no applications yet.
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
import { adminGetStudentApplications } from "../../api/index.js";

export default {
  name: "AdminStudentApplications",
  data() {
    return {
      student: null,
      applications: [],
      loading: true,
    };
  },
  async created() {
    const id = this.$route.params.id;
    try {
      const res = await adminGetStudentApplications(id);
      this.student = res.student;
      this.applications = res.applications;
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
