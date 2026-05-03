<template>
  <div class="min-vh-100 d-flex align-items-center justify-content-center bg-light py-4">
    <div class="card shadow" style="width: 100%; max-width: 480px">
      <div class="card-body p-4">
        <h4 class="card-title text-center fw-bold mb-1">Student Registration</h4>
        <p class="text-center text-muted mb-4 small">Create your student account</p>

        <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
        <div v-if="success" class="alert alert-success py-2">{{ success }}</div>

        <form @submit.prevent="handleRegister">
          <div class="mb-3">
            <label class="form-label">Full Name</label>
            <input v-model="form.full_name" type="text" class="form-control" required />
          </div>
          <div class="mb-3">
            <label class="form-label">Email</label>
            <input v-model="form.email" type="email" class="form-control" required />
          </div>
          <div class="mb-3">
            <label class="form-label">Password</label>
            <input v-model="form.password" type="password" class="form-control" minlength="6" required />
          </div>
          <div class="row">
            <div class="col mb-3">
              <label class="form-label">Branch</label>
              <input v-model="form.branch" type="text" class="form-control" placeholder="e.g. CS" required />
            </div>
            <div class="col mb-3">
              <label class="form-label">Year</label>
              <select v-model="form.year" class="form-select" required>
                <option value="">Select</option>
                <option value="1">1st Year</option>
                <option value="2">2nd Year</option>
                <option value="3">3rd Year</option>
                <option value="4">4th Year</option>
              </select>
            </div>
          </div>
          <div class="mb-3">
            <label class="form-label">CGPA</label>
            <input
              v-model="form.cgpa"
              type="number"
              step="0.01"
              min="0"
              max="10"
              class="form-control"
              placeholder="e.g. 8.5"
              required
            />
          </div>
          <button type="submit" class="btn btn-dark w-100" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            Register
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
import { registerStudent } from "../api/index.js";

export default {
  name: "RegisterStudentView",
  data() {
    return {
      form: { full_name: "", email: "", password: "", branch: "", year: "", cgpa: "" },
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
        const payload = {
          ...this.form,
          year: parseInt(this.form.year),
          cgpa: parseFloat(this.form.cgpa),
        };
        const res = await registerStudent(payload);
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
