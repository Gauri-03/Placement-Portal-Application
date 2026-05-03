<template>
  <div class="container py-4">
    <h4 class="fw-bold mb-4">Placement Drives</h4>

    <div class="row g-2 mb-3">
      <div class="col-md-3">
        <select
          v-model="statusFilter"
          class="form-select"
          @change="fetchDrives"
        >
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="closed">Closed</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border"></div>
    </div>

    <div v-else-if="drives.length === 0" class="text-muted">
      No drives found.
    </div>

    <div v-else class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-dark">
          <tr>
            <th>Job Title</th>
            <th>Company</th>
            <th>Deadline</th>
            <th>Applicants</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in drives" :key="d.id">
            <td>
              <div class="fw-semibold">{{ d.job_title }}</div>
              <div
                class="text-muted small"
                v-if="d.eligible_branches && d.eligible_branches.length"
              >
                Branches: {{ d.eligible_branches.join(", ") }}
              </div>
            </td>
            <td>{{ d.company_name }}</td>
            <td>{{ formatDate(d.application_deadline) }}</td>
            <td>{{ d.applicant_count }}</td>
            <td>
              <span :class="statusBadge(d.status)">{{ d.status }}</span>
            </td>
            <td>
              <div class="d-flex gap-1 flex-wrap">
                <button
                  v-if="d.status === 'pending'"
                  class="btn btn-success btn-sm"
                  @click="openModal(d, 'approve')"
                >
                  Approve
                </button>
                <button
                  v-if="d.status === 'pending'"
                  class="btn btn-danger btn-sm"
                  @click="openModal(d, 'reject')"
                >
                  Reject
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      class="modal fade"
      id="driveConfirmModal"
      tabindex="-1"
      ref="confirmModal"
      aria-labelledby="driveConfirmModalLabel"
      aria-hidden="true"
    >
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div
            class="modal-header"
            :class="pendingAction === 'approve' ? 'bg-success' : 'bg-danger'"
          >
            <h5 class="modal-title text-white" id="driveConfirmModalLabel">
              <i
                :class="
                  pendingAction === 'approve'
                    ? 'bi bi-check-circle-fill'
                    : 'bi bi-x-circle-fill'
                "
                class="me-2"
              ></i>
              {{
                pendingAction === "approve" ? "Approve Drive" : "Reject Drive"
              }}
            </h5>
            <button
              type="button"
              class="btn-close btn-close-white"
              @click="closeModal"
            ></button>
          </div>
          <div class="modal-body">
            <p class="mb-1">
              {{
                pendingAction === "approve"
                  ? "Are you sure you want to approve:"
                  : "Are you sure you want to reject:"
              }}
            </p>
            <p class="fw-semibold mb-0">{{ selectedDrive?.job_title }}</p>
            <p class="text-muted small mb-0" v-if="selectedDrive">
              by {{ selectedDrive.company_name }}
            </p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeModal">
              Cancel
            </button>
            <button
              type="button"
              :class="
                pendingAction === 'approve'
                  ? 'btn btn-success'
                  : 'btn btn-danger'
              "
              @click="confirmAction"
              :disabled="actionLoading"
            >
              <span
                v-if="actionLoading"
                class="spinner-border spinner-border-sm me-1"
              ></span>
              {{ pendingAction === "approve" ? "Approve" : "Reject" }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  adminListDrives,
  adminApproveDrive,
  adminRejectDrive,
} from "../../api/index.js";

export default {
  name: "AdminDrives",
  data() {
    return {
      drives: [],
      statusFilter: "",
      loading: true,
      selectedDrive: null,
      pendingAction: null,
      actionLoading: false,
      bsModal: null,
    };
  },
  created() {
    if (this.$route.query.status) this.statusFilter = this.$route.query.status;
    this.fetchDrives();
  },
  mounted() {
    const modalEl = this.$refs.confirmModal;
    if (window.bootstrap) {
      this.bsModal = new window.bootstrap.Modal(modalEl);
    }
  },
  methods: {
    async fetchDrives() {
      this.loading = true;
      try {
        const qs = this.statusFilter ? `?status=${this.statusFilter}` : "";
        this.drives = await adminListDrives(qs);
      } catch (err) {
        console.error(err);
      } finally {
        this.loading = false;
      }
    },
    openModal(drive, action) {
      this.selectedDrive = drive;
      this.pendingAction = action;
      if (this.bsModal) this.bsModal.show();
    },
    closeModal() {
      if (this.bsModal) this.bsModal.hide();
      this.selectedDrive = null;
      this.pendingAction = null;
    },
    async confirmAction() {
      if (!this.selectedDrive || !this.pendingAction) return;
      this.actionLoading = true;
      try {
        const d = this.selectedDrive;
        if (this.pendingAction === "approve") {
          await adminApproveDrive(d.id);
          d.status = "approved";
        } else if (this.pendingAction === "reject") {
          await adminRejectDrive(d.id);
          d.status = "rejected";
        }
        this.closeModal();
      } catch (err) {
        console.error(err);
      } finally {
        this.actionLoading = false;
      }
    },
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
