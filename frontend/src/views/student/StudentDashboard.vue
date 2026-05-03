<template>
  <div class="container py-4">
    <h4 class="fw-bold mb-4">Available Placement Drives</h4>

    <div class="row g-2 mb-4">
      <div class="col-md-4">
        <input
          v-model="search"
          type="text"
          class="form-control"
          placeholder="Search by job title..."
          @input="fetchDrives"
        />
      </div>
      <div class="col-md-2">
        <input
          v-model="branchFilter"
          type="text"
          class="form-control"
          placeholder="Branch (e.g. CS)"
          @input="fetchDrives"
        />
      </div>
      <div class="col-md-2">
        <select v-model="yearFilter" class="form-select" @change="fetchDrives">
          <option value="">Any Year</option>
          <option value="1">1st Year</option>
          <option value="2">2nd Year</option>
          <option value="3">3rd Year</option>
          <option value="4">4th Year</option>
        </select>
      </div>
      <div class="col-md-2">
        <div class="form-check mt-2">
          <input
            v-model="eligibleOnly"
            class="form-check-input"
            type="checkbox"
            id="eligibleOnly"
            @change="fetchDrives"
          />
          <label class="form-check-label" for="eligibleOnly"
            >Eligible only</label
          >
        </div>
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border"></div>
    </div>
    <div v-else-if="filteredDrives.length === 0" class="text-muted">
      No drives found.
    </div>

    <div v-else class="row g-3">
      <div class="col-md-6 col-lg-4" v-for="d in filteredDrives" :key="d.id">
        <div
          class="card h-100"
          :class="{
            'border-success': d.is_eligible === true,
            'border-danger': d.is_eligible === false,
          }"
        >
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <h6 class="fw-bold mb-0">{{ d.job_title }}</h6>
              <span v-if="d.is_eligible === true" class="badge bg-success"
                >Eligible</span
              >
              <span v-else-if="d.is_eligible === false" class="badge bg-danger"
                >Ineligible</span
              >
            </div>
            <p class="text-muted small mb-1">
              <i class="bi bi-building me-1"></i>{{ d.company_name }}
            </p>
            <p class="text-muted small mb-2">
              <i class="bi bi-calendar me-1"></i>Deadline:
              {{ formatDate(d.application_deadline) }}
            </p>
            <div class="d-flex flex-wrap gap-1 mb-2">
              <span class="badge bg-light text-dark border" v-if="d.min_cgpa"
                >CGPA ≥ {{ d.min_cgpa }}</span
              >
              <span
                class="badge bg-light text-dark border"
                v-if="d.eligible_branches && d.eligible_branches.length"
              >
                {{ d.eligible_branches.join(", ") }}
              </span>
              <span
                class="badge bg-light text-dark border"
                v-if="d.eligible_years && d.eligible_years.length"
              >
                Year {{ d.eligible_years.join("/") }}
              </span>
            </div>
            <p class="text-muted small mb-0" v-if="d.eligibility_reason">
              <i class="bi bi-exclamation-circle me-1"></i
              >{{ d.eligibility_reason }}
            </p>
          </div>
          <div class="card-footer bg-transparent">
            <button
              class="btn btn-dark btn-sm w-100"
              :disabled="
                d.is_eligible === false ||
                appliedIds.has(d.id) ||
                applying === d.id
              "
              @click="apply(d)"
            >
              <span
                v-if="applying === d.id"
                class="spinner-border spinner-border-sm me-1"
              ></span>
              <span v-if="appliedIds.has(d.id)">
                <i class="bi bi-check-circle me-1"></i>Applied
              </span>
              <span v-else>Apply</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  listDrives,
  applyToDrive,
  studentMyApplications,
} from "../../api/index.js";

export default {
  name: "StudentDashboard",
  data() {
    return {
      drives: [],
      appliedIds: new Set(),
      search: "",
      branchFilter: "",
      yearFilter: "",
      eligibleOnly: false,
      loading: true,
      applying: null,
    };
  },
  computed: {
    filteredDrives() {
      let list = this.drives;
      if (this.eligibleOnly) list = list.filter((d) => d.is_eligible === true);
      return list;
    },
  },
  async created() {
    await Promise.all([this.fetchDrives(), this.fetchMyApplications()]);
  },
  methods: {
    async fetchDrives() {
      this.loading = true;
      try {
        const params = new URLSearchParams();
        if (this.search) params.set("search", this.search);
        if (this.branchFilter) params.set("branch", this.branchFilter);
        if (this.yearFilter) params.set("year", this.yearFilter);
        const qs = params.toString() ? `?${params.toString()}` : "";
        this.drives = await listDrives(qs);
      } catch (err) {
        console.error(err);
      } finally {
        this.loading = false;
      }
    },
    async fetchMyApplications() {
      try {
        const apps = await studentMyApplications();
        this.appliedIds = new Set(apps.map((a) => a.drive_id));
      } catch (err) {
        console.error(err);
      }
    },
    async apply(drive) {
      this.applying = drive.id;
      try {
        await applyToDrive(drive.id);
        this.appliedIds = new Set([...this.appliedIds, drive.id]);
      } catch (err) {
        alert(err.message || "Failed to apply");
      } finally {
        this.applying = null;
      }
    },
    formatDate(iso) {
      if (!iso) return "—";
      return new Date(iso).toLocaleDateString();
    },
  },
};
</script>
