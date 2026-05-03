<template>
  <div class="container py-4">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border"></div>
    </div>

    <div v-else>
      <div class="d-flex justify-content-between align-items-start mb-4">
        <div>
          <h4 class="fw-bold mb-0">{{ company.company_name }}</h4>
          <p class="text-muted mb-0">{{ company.email }}</p>
          <p class="text-muted small" v-if="company.website">
            <a :href="company.website" target="_blank">{{ company.website }}</a>
          </p>
        </div>
        <router-link to="/company/drives/create" class="btn btn-dark">
          <i class="bi bi-plus-lg me-1"></i> Post New Drive
        </router-link>
      </div>

      <div class="row g-3 mb-4">
        <div class="col-md-3" v-for="stat in driveStats" :key="stat.label">
          <div class="card text-center h-100">
            <div class="card-body">
              <h3 class="fw-bold">{{ stat.count }}</h3>
              <p class="text-muted mb-0 small">{{ stat.label }}</p>
            </div>
          </div>
        </div>
      </div>

      <h5 class="fw-semibold mb-3">My Placement Drives</h5>
      <div v-if="drives.length === 0" class="text-muted">
        No drives yet. Post your first drive!
      </div>
      <div v-else class="table-responsive">
        <table class="table table-hover align-middle">
          <thead class="table-dark">
            <tr>
              <th>Job Title</th>
              <th>Deadline</th>
              <th>Applicants</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in drives" :key="d.id">
              <td class="fw-semibold">{{ d.job_title }}</td>
              <td>{{ formatDate(d.application_deadline) }}</td>
              <td>{{ d.applicant_count }}</td>
              <td>
                <span :class="statusBadge(d.status)">{{ d.status }}</span>
              </td>
              <td>
                <router-link
                  :to="`/company/drives/${d.id}`"
                  class="btn btn-outline-dark btn-sm"
                >
                  View
                </router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { companyDashboard } from "../../api/index.js";

export default {
  name: "CompanyDashboard",
  data() {
    return { company: {}, drives: [], loading: true };
  },
  computed: {
    driveStats() {
      const counts = { pending: 0, approved: 0, closed: 0, rejected: 0 };
      this.drives.forEach((d) => counts[d.status]++);
      return [
        { label: "Pending Approval", count: counts.pending },
        { label: "Active Drives", count: counts.approved },
        { label: "Closed Drives", count: counts.closed },
        {
          label: "Total Applicants",
          count: this.drives.reduce((s, d) => s + d.applicant_count, 0),
        },
      ];
    },
  },
  async created() {
    try {
      const res = await companyDashboard();
      this.company = res.company;
      this.drives = res.drives;
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
  },
};
</script>
