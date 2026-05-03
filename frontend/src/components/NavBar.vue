<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3">
    <a class="navbar-brand fw-bold" href="#">
      <i class="bi bi-rocket-takeoff-fill me-2"></i>LaunchPad
    </a>
    <button
      class="navbar-toggler"
      type="button"
      data-bs-toggle="collapse"
      data-bs-target="#navMenu"
    >
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navMenu">
      <ul class="navbar-nav me-auto">
        <!-- admin -->

        <template v-if="role === 'admin'">
          <li class="nav-item">
            <router-link class="nav-link" to="/admin/dashboard"
              >Dashboard</router-link
            >
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/admin/companies"
              >Companies</router-link
            >
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/admin/students"
              >Students</router-link
            >
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/admin/drives"
              >Drives</router-link
            >
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/admin/applications"
              >Applications</router-link
            >
          </li>
        </template>

        <!-- comapnies -->
        <template v-if="role === 'company'">
          <li class="nav-item">
            <router-link class="nav-link" to="/company/dashboard"
              >Dashboard</router-link
            >
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/company/drives"
              >My Drives</router-link
            >
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/company/drives/create"
              >Post Drive</router-link
            >
          </li>
        </template>

        <!-- student-->
        <template v-if="role === 'student'">
          <li class="nav-item">
            <router-link class="nav-link" to="/student/dashboard"
              >Drives</router-link
            >
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/student/applications"
              >My Applications</router-link
            >
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/student/profile"
              >Profile</router-link
            >
          </li>
        </template>
      </ul>

      <!--user info and logout -->
      <div class="d-flex align-items-center gap-3 ms-auto">
        <span class="text-white-50 small">
          <i class="bi bi-person-circle me-1"></i>{{ email }}
          <span class="badge bg-secondary ms-1">{{ role }}</span>
        </span>
        <button class="btn btn-outline-danger btn-sm" @click="logout">
          <i class="bi bi-box-arrow-right me-1"></i>Logout
        </button>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: "NavBar",
  data() {
    return {
      role: localStorage.getItem("role") || "",
      email: localStorage.getItem("email") || "User",
    };
  },
  watch: {
    $route() {
      this.role = localStorage.getItem("role") || "";
      this.email = localStorage.getItem("email") || "User";
    },
  },
  methods: {
    logout() {
      localStorage.removeItem("token");
      localStorage.removeItem("role");
      localStorage.removeItem("email");
      this.$router.push("/login");
    },
  },
};
</script>
