<template>
  <router-view/>
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
  }
}
</script>

<style>
#app {
  height: 100vh;
  background: black;
  overflow: hidden
}

</style>
