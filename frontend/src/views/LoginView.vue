<template>
  <div class="min-vh-100 d-flex align-items-center justify-content-center bg-light">
    <div class="card shadow" style="width: 100%; max-width: 420px">
      <div class="card-body p-4">
        <h3 class="card-title text-center mb-1 fw-bold">
          <i class="bi bi-rocket-takeoff-fill text-dark me-2"></i>LaunchPad
        </h3>
        <p class="text-center text-muted mb-4">Sign in to your account</p>

        <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>

        <form @submit.prevent="handleLogin">
          <div class="mb-3">
            <label class="form-label">Email</label>
            <input
              v-model="form.email"
              type="email"
              class="form-control"
              placeholder="you@example.com"
              required
            />
          </div>
          <div class="mb-3">
            <label class="form-label">Password</label>
            <input
              v-model="form.password"
              type="password"
              class="form-control"
              placeholder="••••••••"
              required
            />
          </div>
          <button type="submit" class="btn btn-dark w-100" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            Sign In
          </button>
        </form>

        <hr />
        <p class="text-center text-muted small mb-1">New here?</p>
        <div class="d-flex gap-2">
          <router-link to="/register/student" class="btn btn-outline-secondary btn-sm w-50">
            Register as Student
          </router-link>
          <router-link to="/register/company" class="btn btn-outline-secondary btn-sm w-50">
            Register as Company
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { login } from "../api/index.js";

export default {
  name: "LoginView",
  data() {
    return {
      form: { email: "", password: "" },
      error: "",
      loading: false,
    };
  },
  methods: {
    async handleLogin() {
      this.error = "";
      this.loading = true;
      try {
        const res = await login(this.form);
        localStorage.setItem("token", res.access_token);
        localStorage.setItem("role", res.user.role);
        localStorage.setItem("email", res.user.email);

        const role = res.user.role;
        if (role === "admin") this.$router.push("/admin/dashboard");
        else if (role === "company") this.$router.push("/company/dashboard");
        else this.$router.push("/student/dashboard");
      } catch (err) {
        this.error = err.message || "Login failed";
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>
