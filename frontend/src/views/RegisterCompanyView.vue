<template>
  <div class="min-vh-100 d-flex align-items-center justify-content-center bg-light py-4">
    <div class="card shadow" style="width: 100%; max-width: 480px">
      <div class="card-body p-4">
        <h4 class="card-title text-center fw-bold mb-1">Company Registration</h4>
        <p class="text-center text-muted mb-4 small">Register your company — pending admin approval</p>

        <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
        <div v-if="success" class="alert alert-success py-2">{{ success }}</div>

        <form @submit.prevent="handleRegister">
          <div class="mb-3">
            <label class="form-label">Company Name</label>
            <input v-model="form.company_name" type="text" class="form-control" required />
          </div>
          <div class="mb-3">
            <label class="form-label">Email</label>
            <input v-model="form.email" type="email" class="form-control" required />
          </div>
          <div class="mb-3">
            <label class="form-label">Password</label>
            <input v-model="form.password" type="password" class="form-control" minlength="6" required />
          </div>
          <div class="mb-3">
            <label class="form-label">HR Contact Email <span class="text-muted">(optional)</span></label>
            <input v-model="form.hr_contact_email" type="email" class="form-control" />
          </div>
          <div class="mb-3">
            <label class="form-label">Website <span class="text-muted">(optional)</span></label>
            <input v-model="form.website" type="url" class="form-control" placeholder="https://..." />
          </div>
          <div class="mb-3">
            <label class="form-label">Description <span class="text-muted">(optional)</span></label>
            <textarea v-model="form.description" class="form-control" rows="3"></textarea>
          </div>
          <button type="submit" class="btn btn-dark w-100" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            Register Company
          </button>
        </form>

        <p class="text-center mt-3 mb-0 small">
          Already have an account?
          <router-link to="/login">Sign in</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { registerCompany } from "../api/index.js";

export default {
  name: "RegisterCompanyView",
  data() {
    return {
      form: {
        company_name: "",
        email: "",
        password: "",
        hr_contact_email: "",
        website: "",
        description: "",
      },
      error: "",
      success: "",
      loading: false,
    };
  },
  methods: {
    async handleRegister() {
      this.error = "";
      this.success = "";
      this.loading = true;
      try {
        const res = await registerCompany(this.form);
        this.success = res.message;
        setTimeout(() => this.$router.push("/login"), 1500);
      } catch (err) {
        this.error = err.message || "Registration failed";
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>
