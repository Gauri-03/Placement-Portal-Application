<template>
  <div class="container py-4">
    <h4 class="fw-bold mb-4">Companies</h4>

    <div class="row g-2 mb-3">
      <div class="col-md-4">
        <input
          v-model="search"
          type="text"
          class="form-control"
          placeholder="Search by name or email..."
          @input="fetchCompanies"
        />
      </div>
      <div class="col-md-3">
        <select
          v-model="statusFilter"
          class="form-select"
          @change="fetchCompanies"
        >
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="blacklisted">Blacklisted</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border"></div>
    </div>

    <div v-else-if="companies.length === 0" class="text-muted">
      No companies found.
    </div>

    <div v-else class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-dark">
          <tr>
            <th>Company</th>
            <th>Email</th>
            <th>HR Email</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in companies" :key="c.id">
            <td>
              <div class="fw-semibold">{{ c.company_name }}</div>
              <div class="text-muted small" v-if="c.website">
                <a :href="c.website" target="_blank">{{ c.website }}</a>
              </div>
            </td>
            <td>{{ c.email }}</td>
            <td>{{ c.hr_contact_email || "—" }}</td>
            <td>
              <span :class="statusBadge(c.approval_status)">{{
                c.approval_status
              }}</span>
              <span v-if="c.is_blacklisted" class="badge bg-danger ms-1"
                >Blacklisted</span
              >
            </td>
            <td>
              <div class="d-flex gap-1 flex-wrap">
                <button
                  v-if="c.approval_status === 'pending'"
                  class="btn btn-success btn-sm"
                  @click="openModal(c, 'approve')"
                >
                  Approve
                </button>
                <button
                  v-if="c.approval_status === 'pending'"
                  class="btn btn-danger btn-sm"
                  @click="openModal(c, 'reject')"
                >
                  Reject
                </button>
                <button
                  class="btn btn-outline-danger btn-sm"
                  @click="openModal(c, 'blacklist')"
                >
                  {{ c.is_blacklisted ? "Unblacklist" : "Blacklist" }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      class="modal fade"
      id="confirmModal"
      tabindex="-1"
      ref="confirmModal"
      aria-labelledby="confirmModalLabel"
      aria-hidden="true"
    >
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header" :class="modalHeaderClass">
            <h5 class="modal-title text-white" id="confirmModalLabel">
              <i :class="modalIcon" class="me-2"></i>{{ modalTitle }}
            </h5>
            <button
              type="button"
              class="btn-close btn-close-white"
              @click="closeModal"
            ></button>
          </div>
          <div class="modal-body">
            <p class="mb-1">{{ modalMessage }}</p>
            <p class="fw-semibold mb-0">{{ selectedCompany?.company_name }}</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeModal">
              Cancel
            </button>
            <button
              type="button"
              :class="modalConfirmBtnClass"
              @click="confirmAction"
              :disabled="actionLoading"
            >
              <span
                v-if="actionLoading"
                class="spinner-border spinner-border-sm me-1"
              ></span>
              {{ modalConfirmLabel }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  adminListCompanies,
  adminApproveCompany,
  adminRejectCompany,
  adminBlacklistCompany,
} from "../../api/index.js";

export default {
  name: "AdminCompanies",
  data() {
    return {
      companies: [],
      search: "",
      statusFilter: "",
      loading: true,
      selectedCompany: null,
      pendingAction: null,
      actionLoading: false,
      bsModal: null,
    };
  },
  computed: {
    modalTitle() {
      if (this.pendingAction === "approve") return "Approve Company";
      if (this.pendingAction === "reject") return "Reject Company";
      if (this.pendingAction === "blacklist")
        return this.selectedCompany?.is_blacklisted
          ? "Unblacklist Company"
          : "Blacklist Company";
      return "";
    },
    modalMessage() {
      if (this.pendingAction === "approve")
        return "Are you sure you want to approve:";
      if (this.pendingAction === "reject")
        return "Are you sure you want to reject:";
      if (this.pendingAction === "blacklist")
        return this.selectedCompany?.is_blacklisted
          ? "Are you sure you want to unblacklist:"
          : "Are you sure you want to blacklist:";
      return "";
    },
    modalHeaderClass() {
      if (this.pendingAction === "approve") return "bg-success";
      if (this.pendingAction === "reject") return "bg-danger";
      if (this.pendingAction === "blacklist")
        return this.selectedCompany?.is_blacklisted
          ? "bg-secondary"
          : "bg-danger";
      return "bg-secondary";
    },
    modalIcon() {
      if (this.pendingAction === "approve") return "bi bi-check-circle-fill";
      if (this.pendingAction === "reject") return "bi bi-x-circle-fill";
      if (this.pendingAction === "blacklist")
        return this.selectedCompany?.is_blacklisted
          ? "bi bi-unlock-fill"
          : "bi bi-slash-circle-fill";
      return "";
    },
    modalConfirmLabel() {
      if (this.pendingAction === "approve") return "Approve";
      if (this.pendingAction === "reject") return "Reject";
      if (this.pendingAction === "blacklist")
        return this.selectedCompany?.is_blacklisted
          ? "Unblacklist"
          : "Blacklist";
      return "Confirm";
    },
    modalConfirmBtnClass() {
      if (this.pendingAction === "approve") return "btn btn-success";
      if (this.pendingAction === "reject") return "btn btn-danger";
      if (this.pendingAction === "blacklist")
        return this.selectedCompany?.is_blacklisted
          ? "btn btn-secondary"
          : "btn btn-danger";
      return "btn btn-primary";
    },
  },
  created() {
    if (this.$route.query.status) this.statusFilter = this.$route.query.status;
    this.fetchCompanies();
  },
  mounted() {
    const modalEl = this.$refs.confirmModal;
    if (window.bootstrap) {
      this.bsModal = new window.bootstrap.Modal(modalEl);
    }
  },
  methods: {
    async fetchCompanies() {
      this.loading = true;
      try {
        const params = new URLSearchParams();
        if (this.search) params.set("search", this.search);
        if (this.statusFilter) params.set("status", this.statusFilter);
        const qs = params.toString() ? `?${params.toString()}` : "";
        this.companies = await adminListCompanies(qs);
      } catch (err) {
        console.error(err);
      } finally {
        this.loading = false;
      }
    },
    openModal(company, action) {
      this.selectedCompany = company;
      this.pendingAction = action;
      if (this.bsModal) {
        this.bsModal.show();
      }
    },
    closeModal() {
      if (this.bsModal) {
        this.bsModal.hide();
      }
      this.selectedCompany = null;
      this.pendingAction = null;
    },
    async confirmAction() {
      if (!this.selectedCompany || !this.pendingAction) return;
      this.actionLoading = true;
      try {
        const c = this.selectedCompany;
        if (this.pendingAction === "approve") {
          await adminApproveCompany(c.id);
          c.approval_status = "approved";
        } else if (this.pendingAction === "reject") {
          await adminRejectCompany(c.id);
          c.approval_status = "rejected";
        } else if (this.pendingAction === "blacklist") {
          const res = await adminBlacklistCompany(c.id);
          c.is_blacklisted = res.is_blacklisted;
          if (res.approval_status) c.approval_status = res.approval_status;
        }
        this.closeModal();
      } catch (err) {
        console.error(err);
      } finally {
        this.actionLoading = false;
      }
    },
    statusBadge(status) {
      return (
        {
          pending: "badge bg-warning text-dark",
          approved: "badge bg-success",
          rejected: "badge bg-danger",
        }[status] || "badge bg-secondary"
      );
    },
  },
};
</script>
