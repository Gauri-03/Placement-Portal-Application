<template>
  <NavBar v-if="isLoggedIn" :key="navKey" />
  <router-view />
</template>

<script>
import NavBar from "./components/NavBar.vue";

export default {
  name: "App",
  components: { NavBar },
  data() {
    return {
      isLoggedIn: !!localStorage.getItem("token"),
      navKey: 0,
    };
  },
  watch: {
    $route() {
      this.isLoggedIn = !!localStorage.getItem("token");
      this.navKey++;
    },
  },
};
</script>
