<template>
  <div class="container py-4">
    <h4 class="fw-bold mb-4">Students</h4>

    <div class="row g-2 mb-3">
      <div class="col-md-4">
        <input
          v-model="search"
          type="text"
          class="form-control"
          placeholder="Search by name, email, or branch..."
          @input="fetchStudents"
        />
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border"></div>
    </div>

    <div v-else-if="students.length === 0" class="text-muted">
      No students found.
    </div>

    <div v-else class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-dark">
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Branch</th>
            <th>Year</th>
            <th>CGPA</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in students" :key="s.id">
            <td class="fw-semibold">{{ s.full_name }}</td>
            <td>{{ s.email }}</td>
            <td>{{ s.branch }}</td>
            <td>{{ s.year }}</td>
            <td>{{ s.cgpa }}</td>
            <td>
              <span v-if="s.is_blacklisted" class="badge bg-danger"
                >Blacklisted</span
              >
              <span v-else class="badge bg-success">Active</span>
            </td>
            <td>
              <div class="d-flex gap-1 flex-wrap">
                <router-link
                  :to="`/admin/students/${s.id}/applications`"
                  class="btn btn-outline-primary btn-sm"
                >
                  <i class="bi bi-list-check me-1"></i>Applications
                </router-link>
                <button
                  class="btn btn-outline-danger btn-sm"
                  @click="openBlacklistModal(s)"
                >
                  {{ s.is_blacklisted ? "Unblacklist" : "Blacklist" }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      class="modal fade"
      id="blacklistStudentModal"
      tabindex="-1"
      ref="blacklistModal"
      aria-labelledby="blacklistStudentModalLabel"
      aria-hidden="true"
    >
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div
            class="modal-header"
            :class="
              selectedStudent?.is_blacklisted ? 'bg-secondary' : 'bg-danger'
            "
          >
            <h5 class="modal-title text-white" id="blacklistStudentModalLabel">
              <i
                :class="
                  selectedStudent?.is_blacklisted
                    ? 'bi bi-unlock-fill'
                    : 'bi bi-slash-circle-fill'
                "
                class="me-2"
              ></i>
              {{
                selectedStudent?.is_blacklisted
                  ? "Unblacklist Student"
                  : "Blacklist Student"
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
                selectedStudent?.is_blacklisted
                  ? "Are you sure you want to unblacklist:"
                  : "Are you sure you want to blacklist:"
              }}
            </p>
            <p class="fw-semibold mb-0">{{ selectedStudent?.full_name }}</p>
            <p class="text-muted small mb-0">{{ selectedStudent?.email }}</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeModal">
              Cancel
            </button>
            <button
              type="button"
              :class="
                selectedStudent?.is_blacklisted
                  ? 'btn btn-secondary'
                  : 'btn btn-danger'
              "
              @click="confirmBlacklist"
              :disabled="actionLoading"
            >
              <span
                v-if="actionLoading"
                class="spinner-border spinner-border-sm me-1"
              ></span>
              {{
                selectedStudent?.is_blacklisted ? "Unblacklist" : "Blacklist"
              }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { adminListStudents, adminBlacklistStudent } from "../../api/index.js";

export default {
  name: "AdminStudents",
  data() {
    return {
      students: [],
      search: "",
      loading: true,
      selectedStudent: null,
      actionLoading: false,
      bsModal: null,
    };
  },
  created() {
    this.fetchStudents();
  },
  mounted() {
    const modalEl = this.$refs.blacklistModal;
    if (window.bootstrap) {
      this.bsModal = new window.bootstrap.Modal(modalEl);
    }
  },
  methods: {
    async fetchStudents() {
      this.loading = true;
      try {
        const qs = this.search
          ? `?search=${encodeURIComponent(this.search)}`
          : "";
        this.students = await adminListStudents(qs);
      } catch (err) {
        console.error(err);
      } finally {
        this.loading = false;
      }
    },
    openBlacklistModal(student) {
      this.selectedStudent = student;
      if (this.bsModal) this.bsModal.show();
    },
    closeModal() {
      if (this.bsModal) this.bsModal.hide();
      this.selectedStudent = null;
    },
    async confirmBlacklist() {
      if (!this.selectedStudent) return;
      this.actionLoading = true;
      try {
        const res = await adminBlacklistStudent(this.selectedStudent.id);
        this.selectedStudent.is_blacklisted = res.is_blacklisted;
        this.closeModal();
      } catch (err) {
        alert(err.message || "Failed to update blacklist status.");
      } finally {
        this.actionLoading = false;
      }
    },
  },
};
</script>
