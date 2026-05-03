<template>
  <div class="container py-4">
    <h4 class="fw-bold mb-4">Admin Dashboard</h4>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border"></div>
    </div>

    <div v-else>
      <div class="row g-3 mb-4">
        <div class="col-md-4">
          <div class="card text-bg-dark h-100">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-center">
                <div>
                  <p class="card-text text-white-50 mb-1">Total Students</p>
                  <h2 class="fw-bold mb-0">{{ stats.total_students }}</h2>
                </div>
                <i class="bi bi-people-fill fs-1 opacity-50"></i>
              </div>
            </div>
            <div class="card-footer border-0 bg-transparent">
              <router-link
                to="/admin/students"
                class="text-white-50 small text-decoration-none"
              >
                View all <i class="bi bi-arrow-right"></i>
              </router-link>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card text-bg-primary h-100">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-center">
                <div>
                  <p class="card-text text-white-50 mb-1">Total Companies</p>
                  <h2 class="fw-bold mb-0">{{ stats.total_companies }}</h2>
                </div>
                <i class="bi bi-building-fill fs-1 opacity-50"></i>
              </div>
            </div>
            <div class="card-footer border-0 bg-transparent">
              <router-link
                to="/admin/companies"
                class="text-white-50 small text-decoration-none"
              >
                View all <i class="bi bi-arrow-right"></i>
              </router-link>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card text-bg-success h-100">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-center">
                <div>
                  <p class="card-text text-white-50 mb-1">Total Drives</p>
                  <h2 class="fw-bold mb-0">{{ stats.total_drives }}</h2>
                </div>
                <i class="bi bi-briefcase-fill fs-1 opacity-50"></i>
              </div>
            </div>
            <div class="card-footer border-0 bg-transparent">
              <router-link
                to="/admin/drives"
                class="text-white-50 small text-decoration-none"
              >
                View all <i class="bi bi-arrow-right"></i>
              </router-link>
            </div>
          </div>
        </div>
      </div>

      <div class="row g-3">
        <div class="col-md-6">
          <div class="card">
            <div class="card-header fw-semibold">Quick Actions</div>
            <div class="card-body d-flex flex-column gap-2">
              <router-link
                :to="{ path: '/admin/companies', query: { status: 'pending' } }"
                class="btn btn-outline-warning btn-sm"
              >
                <i class="bi bi-hourglass-split me-1"></i> Review Pending
                Companies
              </router-link>
              <router-link
                :to="{ path: '/admin/drives', query: { status: 'pending' } }"
                class="btn btn-outline-info btn-sm"
              >
                <i class="bi bi-hourglass-split me-1"></i> Review Pending Drives
              </router-link>
              <router-link
                to="/admin/applications"
                class="btn btn-outline-secondary btn-sm"
              >
                <i class="bi bi-list-check me-1"></i> View All Applications
              </router-link>
              <hr class="my-1" />
              <p class="text-muted small mb-1 fw-semibold">Demo Tools</p>
              <button
                class="btn btn-outline-primary btn-sm"
                @click="triggerDailyReminders"
                :disabled="triggerLoading.daily"
              >
                <span
                  v-if="triggerLoading.daily"
                  class="spinner-border spinner-border-sm me-1"
                ></span>
                <i v-else class="bi bi-envelope-fill me-1"></i> Send Daily
                Reminders
              </button>
              <button
                class="btn btn-outline-dark btn-sm"
                @click="triggerMonthlyReport"
                :disabled="triggerLoading.monthly"
              >
                <span
                  v-if="triggerLoading.monthly"
                  class="spinner-border spinner-border-sm me-1"
                ></span>
                <i v-else class="bi bi-bar-chart-fill me-1"></i> Send Monthly
                Report
              </button>
              <div
                v-if="triggerMessage"
                class="alert alert-success py-1 px-2 small mb-0"
              >
                {{ triggerMessage }}
              </div>
              <div
                v-if="triggerError"
                class="alert alert-danger py-1 px-2 small mb-0"
              >
                {{ triggerError }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  adminDashboard,
  adminTriggerDailyReminders,
  adminTriggerMonthlyReport,
} from "../../api/index.js";

export default {
  name: "AdminDashboard",
  data() {
    return {
      stats: { total_students: 0, total_companies: 0, total_drives: 0 },
      loading: true,
      triggerLoading: { daily: false, monthly: false },
      triggerMessage: "",
      triggerError: "",
    };
  },
  async created() {
    try {
      this.stats = await adminDashboard();
    } catch (err) {
      console.error(err);
    } finally {
      this.loading = false;
    }
  },
  methods: {
    async triggerDailyReminders() {
      this.triggerMessage = "";
      this.triggerError = "";
      this.triggerLoading.daily = true;
      try {
        const res = await adminTriggerDailyReminders();
        this.triggerMessage = res.message || "Daily reminders queued!";
      } catch (err) {
        this.triggerError = err.message || "Failed to trigger daily reminders.";
      } finally {
        this.triggerLoading.daily = false;
      }
    },
    async triggerMonthlyReport() {
      this.triggerMessage = "";
      this.triggerError = "";
      this.triggerLoading.monthly = true;
      try {
        const res = await adminTriggerMonthlyReport();
        this.triggerMessage = res.message || "Monthly report queued!";
      } catch (err) {
        this.triggerError = err.message || "Failed to trigger monthly report.";
      } finally {
        this.triggerLoading.monthly = false;
      }
    },
  },
};
</script>
