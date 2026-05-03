<template>
  <div class="container py-4" style="max-width: 600px">
    <h4 class="fw-bold mb-4">My Profile</h4>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border"></div>
    </div>

    <div v-else>
      <div v-if="error" class="alert alert-danger">{{ error }}</div>
      <div v-if="success" class="alert alert-success">{{ success }}</div>

      <form @submit.prevent="saveProfile">
        <div class="mb-3">
          <label class="form-label fw-semibold">Full Name</label>
          <input
            v-model="form.full_name"
            type="text"
            class="form-control"
            required
          />
        </div>
        <div class="mb-3">
          <label class="form-label fw-semibold">Email</label>
          <input :value="email" type="email" class="form-control" disabled />
        </div>
        <div class="row">
          <div class="col mb-3">
            <label class="form-label fw-semibold">Branch</label>
            <input
              v-model="form.branch"
              type="text"
              class="form-control"
              required
            />
          </div>
          <div class="col mb-3">
            <label class="form-label fw-semibold">Year</label>
            <select v-model="form.year" class="form-select" required>
              <option :value="1">1st Year</option>
              <option :value="2">2nd Year</option>
              <option :value="3">3rd Year</option>
              <option :value="4">4th Year</option>
            </select>
          </div>
        </div>
        <div class="mb-3">
          <label class="form-label fw-semibold">CGPA</label>
          <input
            v-model="form.cgpa"
            type="number"
            step="0.01"
            min="0"
            max="10"
            class="form-control"
            required
          />
        </div>
        <button type="submit" class="btn btn-dark w-100" :disabled="saving">
          <span
            v-if="saving"
            class="spinner-border spinner-border-sm me-2"
          ></span>
          Save Changes
        </button>
      </form>

      <hr class="my-4" />

      <h6 class="fw-semibold mb-3">Resume</h6>
      <div
        v-if="resumePath"
        class="alert alert-info py-2 small d-flex align-items-center justify-content-between"
      >
        <span
          ><i class="bi bi-file-earmark-text me-1"></i>Current:
          {{ resumePath }}</span
        >
        <button
          class="btn btn-sm btn-outline-danger ms-2"
          @click="removeResume"
          :disabled="removing"
          type="button"
        >
          <span
            v-if="removing"
            class="spinner-border spinner-border-sm me-1"
          ></span>
          <i v-else class="bi bi-trash me-1"></i>Remove
        </button>
      </div>
      <div class="input-group">
        <input
          type="file"
          class="form-control"
          accept=".pdf,.doc,.docx"
          ref="resumeFile"
        />
        <button
          class="btn btn-outline-secondary"
          @click="clearResumeFile"
          type="button"
        >
          <i class="bi bi-x-lg"></i>
        </button>
        <button
          class="btn btn-outline-dark"
          @click="uploadResume"
          :disabled="uploading"
          type="button"
        >
          <span
            v-if="uploading"
            class="spinner-border spinner-border-sm me-1"
          ></span>
          Upload
        </button>
      </div>
      <div class="form-text">Accepted: PDF, DOC, DOCX (max 5MB)</div>
    </div>
  </div>
</template>

<script>
import {
  studentGetProfile,
  studentUpdateProfile,
  studentUploadResume,
  studentDeleteResume,
} from "../../api/index.js";

export default {
  name: "StudentProfile",
  data() {
    return {
      form: { full_name: "", branch: "", year: 1, cgpa: "" },
      email: "",
      resumePath: "",
      error: "",
      success: "",
      loading: true,
      saving: false,
      uploading: false,
      removing: false,
    };
  },
  async created() {
    try {
      const profile = await studentGetProfile();
      this.form.full_name = profile.full_name;
      this.form.branch = profile.branch;
      this.form.year = profile.year;
      this.form.cgpa = profile.cgpa;
      this.email = profile.email;
      this.resumePath = profile.resume_path || "";
    } catch (err) {
      this.error = err.message || "Failed to load profile";
    } finally {
      this.loading = false;
    }
  },
  methods: {
    async saveProfile() {
      this.error = "";
      this.success = "";
      this.saving = true;
      try {
        const payload = {
          full_name: this.form.full_name,
          branch: this.form.branch,
          year: parseInt(this.form.year),
          cgpa: parseFloat(this.form.cgpa),
        };
        await studentUpdateProfile(payload);
        this.success = "Profile updated successfully.";
      } catch (err) {
        this.error = err.message || "Failed to update profile";
      } finally {
        this.saving = false;
      }
    },
    clearResumeFile() {
      this.$refs.resumeFile.value = "";
    },
    async removeResume() {
      if (!confirm("Are you sure you want to remove your uploaded resume?"))
        return;
      this.error = "";
      this.success = "";
      this.removing = true;
      try {
        await studentDeleteResume();
        this.resumePath = "";
        this.success = "Resume removed successfully.";
      } catch (err) {
        this.error = err.message || "Failed to remove resume";
      } finally {
        this.removing = false;
      }
    },
    async uploadResume() {
      const file = this.$refs.resumeFile.files[0];
      if (!file) return alert("Please select a file first.");
      this.uploading = true;
      try {
        const formData = new FormData();
        formData.append("resume", file);
        const res = await studentUploadResume(formData);
        this.resumePath = res.resume_path;
        this.success = "Resume uploaded successfully.";
        this.$refs.resumeFile.value = "";
      } catch (err) {
        this.error = err.message || "Failed to upload resume";
      } finally {
        this.uploading = false;
      }
    },
  },
};
</script>
