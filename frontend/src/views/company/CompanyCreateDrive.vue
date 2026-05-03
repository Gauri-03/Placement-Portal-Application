<template>
  <div class="container py-4" style="max-width: 640px">
    <div class="d-flex align-items-center mb-4">
      <router-link
        to="/company/dashboard"
        class="btn btn-outline-secondary btn-sm me-3"
      >
        <i class="bi bi-arrow-left"></i>
      </router-link>
      <h4 class="fw-bold mb-0">Post a New Drive</h4>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <form @submit.prevent="handleSubmit">
      <div class="mb-3">
        <label class="form-label fw-semibold"
          >Job Title <span class="text-danger">*</span></label
        >
        <input
          v-model="form.job_title"
          type="text"
          class="form-control"
          required
        />
      </div>

      <div class="mb-3">
        <label class="form-label fw-semibold">Job Description <span class="text-danger">*</span></label>
        <textarea
          v-model="form.job_description"
          class="form-control"
          rows="4"
          required
        ></textarea>
      </div>

      <div class="mb-3">
        <label class="form-label fw-semibold"
          >Application Deadline <span class="text-danger">*</span></label
        >
        <input
          v-model="form.application_deadline"
          type="datetime-local"
          class="form-control"
          required
        />
      </div>

      <hr />
      <h6 class="fw-semibold mb-3">
        Eligibility Criteria
        <span class="text-muted fw-normal">(leave blank = no restriction)</span>
      </h6>

      <div class="mb-3">
        <label class="form-label">Eligible Branches</label>
        <input
          v-model="branchInput"
          type="text"
          class="form-control"
          placeholder="e.g. CS, ECE, ME (comma-separated)"
        />
        <div class="form-text">Separate multiple branches with commas.</div>
      </div>

      <div class="row">
        <div class="col mb-3">
          <label class="form-label">Minimum CGPA</label>
          <input
            v-model="form.min_cgpa"
            type="number"
            step="0.1"
            min="0"
            max="10"
            class="form-control"
            placeholder="e.g. 7.0"
          />
        </div>
        <div class="col mb-3">
          <label class="form-label">Eligible Years</label>
          <input
            v-model="yearInput"
            type="text"
            class="form-control"
            placeholder="e.g. 3, 4"
          />
        </div>
      </div>

      <button type="submit" class="btn btn-dark w-100" :disabled="loading">
        <span
          v-if="loading"
          class="spinner-border spinner-border-sm me-2"
        ></span>
        Submit for Approval
      </button>
    </form>
  </div>
</template>

<script>
import { companyCreateDrive } from "../../api/index.js";

export default {
  name: "CompanyCreateDrive",
  data() {
    return {
      form: {
        job_title: "",
        job_description: "",
        application_deadline: "",
        min_cgpa: "",
      },
      branchInput: "",
      yearInput: "",
      error: "",
      success: "",
      loading: false,
    };
  },
  methods: {
    async handleSubmit() {
      this.error = "";
      this.success = "";
      this.loading = true;
      try {
        const payload = {
          job_title: this.form.job_title,
          job_description: this.form.job_description || null,
          application_deadline: this.form.application_deadline,
          min_cgpa: this.form.min_cgpa ? parseFloat(this.form.min_cgpa) : null,
          eligible_branches: this.branchInput
            ? this.branchInput
                .split(",")
                .map((b) => b.trim())
                .filter(Boolean)
            : null,
          eligible_years: this.yearInput
            ? this.yearInput
                .split(",")
                .map((y) => parseInt(y.trim()))
                .filter((y) => !isNaN(y))
            : null,
        };
        const res = await companyCreateDrive(payload);
        this.success = res.message;
        setTimeout(() => this.$router.push("/company/dashboard"), 1500);
      } catch (err) {
        this.error = err.message || "Failed to create drive";
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>
