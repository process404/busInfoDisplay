<template>
  <div class="body">
    <div class="top-bar">
      <h2>{{displayName}}</h2>
      <div style="position: relative;">
        <h3 class="currentTime" :class="{active: this.timeToggle}">{{currentTime}}</h3>
        <div class="top-bar-routes" :class="{active: !this.timeToggle && this.currentTimeTogglePg == 0}">
          <h4 v-for="item in this.thisStopRoutes.slice(0,3)"  class="route-box" :class="item.opr">{{item.route}}</h4>
        </div>
        <div class="top-bar-routes" :class="{active: !this.timeToggle && this.currentTimeTogglePg == 1}" v-if="this.thisStopRoutes.length > 3">
          <h4 v-for="item in this.thisStopRoutes.slice(3,6)"  class="route-box" :class="item.opr">{{item.route}}</h4>
        </div>
        <div class="top-bar-routes" :class="{active: !this.timeToggle && this.currentTimeTogglePg == 2}" v-if="this.thisStopRoutes.length > 6">
          <h4 v-for="item in this.thisStopRoutes.slice(6,9)"  class="route-box" :class="item.opr">{{item.route}}</h4>
        </div>
        <div class="top-bar-routes" :class="{active: !this.timeToggle && this.currentTimeTogglePg == 3}" v-if="this.thisStopRoutes.length > 9">
          <h4 v-for="item in this.thisStopRoutes.slice(6,9)"  class="route-box" :class="item.opr">{{item.route}}</h4>
        </div>
      </div>
    </div>
    <h1>GTFS Data</h1>
    <p v-if="apiData">Data: {{ apiData }}</p>
    <p v-else>Loading...</p>
  </div>
</template>

<script>

import axios from 'axios';

export default {
  data() {
    return {
      thisStop: "Edge Hill University",
      displayName: "Edge Hill University",
      onwardStopsName: "Bus Station",
      onwardStopDisplay: "Ormskirk Bus Station",
      currentTime: "00:00",
      currentDate: null,
      thisStopRoutes: [{"route":"1","opr":"Stagecoach"},{"route":"2","opr":"Arriva"}],
      apiData: null,
      intervalId: null,

      timeToggle: true,
      currentTimeTogglePg: 0
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
    },
    setupBoard(){
      for (const stop in this.apiData['allStops']){
        if(stop['stop_name'] == this.thisStop){
          this.thisStopRoutes.push(stop['route_id']);
        }
      }
    },
    updateBoard(){

    },
    currentTimeLoop(){
      setInterval(() => {
        let date = new Date();
        let hours = date.getHours();
        let minutes = date.getMinutes();
        let day = date.getDate();
        let month = date.getMonth() + 1;
        this.currentTime = `${hours}:${minutes}`;
        this.currentDate = `${day}/${month}`;
      }, 1000);

    },
    sleep(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    },
    timeToggler(){
      setInterval(() => {
        if(this.timeToggle){
          this.timeToggle = false;
          if(this.thisStopRoutes.length > 3){
            if (this.thisStopRoutes.length > 6){
              if(this.thisStopRoutes.length > 9){
                this.sleep(3000).then(() => {
                    this.currentTimeTogglePg = 1;
                    this.sleep(3000).then(() => {
                      this.currentTimeTogglePg = 2;
                      this.sleep(3000).then(() => {
                        this.currentTimeTogglePg = 3;
                    })
                  });
                });
              }else{
                  this.sleep(5000).then(() => {
                    this.currentTimeTogglePg = 1;
                    this.sleep(5000).then(() => {
                      this.currentTimeTogglePg = 2;
                    })
                  });
              }
            }
            else{
              this.sleep(8000).then(() => {
                this.currentTimeTogglePg = 1;
              });
            }
          }
        }else{
          this.timeToggle = true;
          this.currentTimeTogglePg = 0;
        }
      }, 15000);
    }
  },
  mounted() {
      // this.fetchData();  // Fetch data immediately on mount
      this.currentTimeLoop();
      this.timeToggler();
      // Set up any other necessary intervals or events...
  }
}
</script>

<style>
.body{
  width: 100%;
  height: 100vh;
  overflow-x: hidden;
  overflow-y: hidden;
}

.top-bar{
  height: 8%;
  width: 100%;
  border-bottom: 2px solid white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-left: 1rem;
  padding-right: 1rem;
  position: relative;
}

.top-bar h2{
  color: white;
  font-size: 1.5em
}

.top-bar .currentTime{
  color: white;
  font-size: 1.5em;
  background: rgb(44, 44, 44);
  padding: 0.3rem; 
  border-radius: 0.3rem;
  border: 1px solid rgb(129, 129, 129);
  padding-left: 0.5rem;
  padding-right: 0.5rem;
  opacity: 0;
  transition: 1s;
}

.top-bar .currentTime.active{
  opacity: 1;
}

.route-box{
  color: white;
  font-size: 1.5em;
  background: rgb(63, 63, 63);
  padding: 0.3rem; 
  border-radius: 0.3rem;
  border: 1px solid rgb(185, 185, 185);
  text-align: center;
  padding-left: 0.5rem;
  padding-right: 0.5rem
}

.top-bar-routes{
  display: flex;
  gap: 0.3rem;
  position: absolute;
  top: 0%;
  transform: translateX(100%);
  opacity: 0;
  right: 0%;
  transition: 1s;
  max-width: 180px;
}

.top-bar-routes.active{
  transform: translateX(0%);
  opacity: 1;
}

.currentTime{
  display: inline-block;
}

.Stagecoach { background-color: #ac7500; }
.Mixture { background-color: #333333; }
.Arriva{
  background-color: #006c80
}
.HTL{
  background-color: #015532
}

</style>
