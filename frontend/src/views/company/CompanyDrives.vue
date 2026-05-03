<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h4 class="fw-bold mb-0">My Drives</h4>
      <router-link to="/company/drives/create" class="btn btn-dark btn-sm">
        <i class="bi bi-plus-lg me-1"></i> Post Drive
      </router-link>
    </div>

    <div v-if="loading" class="text-center py-5"><div class="spinner-border"></div></div>
    <div v-else-if="drives.length === 0" class="text-muted">No drives yet.</div>

    <div v-else class="row g-3">
      <div class="col-md-6" v-for="d in drives" :key="d.id">
        <div class="card h-100">
          <div class="card-body">
            <div class="d-flex justify-content-between">
              <h6 class="fw-bold mb-1">{{ d.job_title }}</h6>
              <span :class="statusBadge(d.status)">{{ d.status }}</span>
            </div>
            <p class="text-muted small mb-2">Deadline: {{ formatDate(d.application_deadline) }}</p>
            <p class="mb-2">
              <i class="bi bi-people me-1"></i>{{ d.applicant_count }} applicant(s)
            </p>
            <div class="d-flex flex-wrap gap-1 mb-2">
              <span class="badge bg-light text-dark border" v-if="d.min_cgpa">CGPA ≥ {{ d.min_cgpa }}</span>
              <span
                class="badge bg-light text-dark border"
                v-if="d.eligible_branches && d.eligible_branches.length"
              >{{ d.eligible_branches.join(", ") }}</span>
            </div>
          </div>
          <div class="card-footer bg-transparent">
            <router-link :to="`/company/drives/${d.id}`" class="btn btn-outline-dark btn-sm w-100">
              View Applicants
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { companyListDrives } from "../../api/index.js";

export default {
  name: "CompanyDrives",
  data() {
    return { drives: [], loading: true };
  },
  async created() {
    try {
      this.drives = await companyListDrives();
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
      return {
        pending: "badge bg-warning text-dark",
        approved: "badge bg-success",
        rejected: "badge bg-danger",
        closed: "badge bg-secondary",
      }[status] || "badge bg-secondary";
    },
  },
};
</script>
