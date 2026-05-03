import { createRouter, createWebHashHistory } from "vue-router";

const routes = [
  // logina nd register
  {
    path: "/",
    redirect: () => {
      const token = localStorage.getItem("token");
      const role = localStorage.getItem("role");
      if (token && role === "admin") return "/admin/dashboard";
      if (token && role === "company") return "/company/dashboard";
      if (token && role === "student") return "/student/dashboard";
      return "/login";
    },
  },
  {
    path: "/login",
    name: "Login",
    component: () => import("../views/LoginView.vue"),
    meta: { guest: true },
  },
  {
    path: "/register/student",
    name: "RegisterStudent",
    component: () => import("../views/RegisterStudentView.vue"),
    meta: { guest: true },
  },
  {
    path: "/register/company",
    name: "RegisterCompany",
    component: () => import("../views/RegisterCompanyView.vue"),
    meta: { guest: true },
  },

  // admin
  {
    path: "/admin/dashboard",
    name: "AdminDashboard",
    component: () => import("../views/admin/AdminDashboard.vue"),
    meta: { requiresAuth: true, role: "admin" },
  },
  {
    path: "/admin/companies",
    name: "AdminCompanies",
    component: () => import("../views/admin/AdminCompanies.vue"),
    meta: { requiresAuth: true, role: "admin" },
  },
  {
    path: "/admin/students",
    name: "AdminStudents",
    component: () => import("../views/admin/AdminStudents.vue"),
    meta: { requiresAuth: true, role: "admin" },
  },
  {
    path: "/admin/drives",
    name: "AdminDrives",
    component: () => import("../views/admin/AdminDrives.vue"),
    meta: { requiresAuth: true, role: "admin" },
  },
  {
    path: "/admin/applications",
    name: "AdminApplications",
    component: () => import("../views/admin/AdminApplications.vue"),
    meta: { requiresAuth: true, role: "admin" },
  },
  {
    path: "/admin/students/:id/applications",
    name: "AdminStudentApplications",
    component: () => import("../views/admin/AdminStudentApplications.vue"),
    meta: { requiresAuth: true, role: "admin" },
  },

  // company
  {
    path: "/company/dashboard",
    name: "CompanyDashboard",
    component: () => import("../views/company/CompanyDashboard.vue"),
    meta: { requiresAuth: true, role: "company" },
  },
  {
    path: "/company/drives",
    name: "CompanyDrives",
    component: () => import("../views/company/CompanyDrives.vue"),
    meta: { requiresAuth: true, role: "company" },
  },
  {
    path: "/company/drives/create",
    name: "CompanyCreateDrive",
    component: () => import("../views/company/CompanyCreateDrive.vue"),
    meta: { requiresAuth: true, role: "company" },
  },
  {
    path: "/company/drives/:id",
    name: "CompanyDriveDetail",
    component: () => import("../views/company/CompanyDriveDetail.vue"),
    meta: { requiresAuth: true, role: "company" },
  },

  // student
  {
    path: "/student/dashboard",
    name: "StudentDashboard",
    component: () => import("../views/student/StudentDashboard.vue"),
    meta: { requiresAuth: true, role: "student" },
  },
  {
    path: "/student/profile",
    name: "StudentProfile",
    component: () => import("../views/student/StudentProfile.vue"),
    meta: { requiresAuth: true, role: "student" },
  },
  {
    path: "/student/applications",
    name: "StudentApplications",
    component: () => import("../views/student/StudentApplications.vue"),
    meta: { requiresAuth: true, role: "student" },
  },

  { path: "/:pathMatch(.*)*", redirect: "/" },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("token");
  const role = localStorage.getItem("role");

  if (to.meta.requiresAuth) {
    if (!token) return next("/login");
    if (to.meta.role && to.meta.role !== role) {
      if (role === "admin") return next("/admin/dashboard");
      if (role === "company") return next("/company/dashboard");
      if (role === "student") return next("/student/dashboard");
      return next("/login");
    }
  }

  if (to.meta.guest && token) {
    if (role === "admin") return next("/admin/dashboard");
    if (role === "company") return next("/company/dashboard");
    if (role === "student") return next("/student/dashboard");
  }

  next();
});

export default router;
