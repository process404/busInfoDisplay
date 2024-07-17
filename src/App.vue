<template>
  <p>API Data: {{ apiData }}</p>
  <!-- <router-view/> -->
</template>

<script>
import { data } from 'autoprefixer';
import axios from 'axios';


export default{
  data(){
    return{
      apiData: null,
      intervalId: null,
    }
  },
  methods: {
    async fetchData() {
      axios.get('http://localhost:5000/gtfs-data')
        .then(response => {
          this.apiData = response.data;
        })
        .catch(error => {
          console.error('There was an error fetching the GTFS data:', error);
        });
    }

  },
  mounted() {
      this.fetchData();  // Fetch data immediately on mount
      // Set up any other necessary intervals or events...
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  height: 100vh;
}

nav {
  padding: 30px;
}

nav a {
  font-weight: bold;
  color: #2c3e50;
}

nav a.router-link-exact-active {
  color: #42b983;
}
</style>
