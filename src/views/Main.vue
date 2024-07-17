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
    <div class="departures-section">
      <div class="loading" v-if="loadingDepartures">
        <h2>Loading...</h2>
        <span class="loader"></span>
      </div>
    </div>
  </div>
</template>

<script>

import axios from 'axios';
import overrides from '@/assets/stop_override.json';

export default {
  data() {
    return {
      thisStop: "Edge Hill University",
      displayName: "Edge Hill University",
      onwardStopsName: "Bus Station",
      onwardStopDisplay: "Ormskirk Bus Station",
      currentTime: "00:00",
      currentDate: null,
      thisStopRoutes: [],
      thisStopDepartures:[],
      realTimeDepartures: [],
      apiData: null,
      intervalId: null,

      timeToggle: true,
      currentTimeTogglePg: 0,
      loadingDepartures: true
    }
  },
  methods: {
    async fetchData() {
      axios.get('http://localhost:5000/gtfs-data')
        .then(response => {
          this.apiData = response.data;
          this.setupBoard();
        })
        .catch(error => {
          console.error('There was an error fetching the GTFS data:', error);
        });
    },
    setupBoard(){
      const today = new Date();
      const daysOfWeek = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
      const currentDayOfWeek = daysOfWeek[today.getDay()];
      console.log("day week: " + currentDayOfWeek);

      // Assuming this.apiData and this.thisStop are already defined
      this.thisStopRoutes = []; // Initialize the array to store routes and operators

      this.apiData['allStops'].forEach(stop => {
        // Check if the current stop's name matches the desired stop
        if(stop['stop_name'] === this.thisStop){
          // Iterate over the routes array for the matched stop
          stop['routes'].forEach(route => {
            // Retrieve the operator for the current route
            let operator = this.apiData['routes'][route]['operator'];

            // Check for an operator override in the stopOverrideData
            const routeOverride = overrides.route_override.find(override => override.route === route);
            if (routeOverride && routeOverride.operator) {
              // Substitute the operator with the override
              operator = routeOverride.operator;
            }

            // Push the route and operator (possibly overridden) to the array
            this.thisStopRoutes.push({ route: route, opr: operator });
          });
        }
      });

      console.log("this stop routes", this.thisStopRoutes)

      console.log('Starting loop with apiData:', this.apiData);
      for (const route in this.apiData['routes']) {
        for (const journey in this.apiData['routes'][route]['journeys']) {
          const journeyData = this.apiData['routes'][route]['journeys'][journey];
          const runningDays = journeyData['running_days'];
          const noServiceDates = journeyData['no_service_dates'];

          console.log('Checking journey:', journeyData);
          if (!noServiceDates.includes(today.toISOString().split('T')[0]) && runningDays[currentDayOfWeek] === 1) {
            const stopTimes = journeyData['stop_times'];
            for (const stopTime of stopTimes) {
              if (stopTime['stop_name'] === this.thisStop) {
                const stopOverride = overrides.stop_override.find(stop => stop.stop_name === this.thisStop);
                if (stopOverride) {
                  const overrideTimes = stopOverride.min_ph_override; // Assuming this is an array of numbers
                  const departureTime = stopTime['departure_time'].split(':');
                  const minute = parseInt(departureTime[1], 10); // Convert minute to number
                  if (!overrideTimes.includes(minute)) { // Now both are numbers
                    console.log('Adding departure:', stopTime);
                    this.thisStopDepartures.push(stopTime);
                  }
                }
              }
            }
          }
        }
      }
      console.log('Final departures:', this.thisStopDepartures);


      this.loadingDepartures = false;
      this.updateBoard();
    },
    updateBoard(){
      setInterval(() => {
        this.realTimeDepartures = [];
        this.thisStopDepartures.forEach((departure) => {
          var departureTime = new Date(departure.departure_time);
          var currentTime = new Date();
          if (departureTime > currentTime) {
            // Departure is in the future
            const timeDifference = Math.floor((departureTime - currentTime) / 1000 / 60);
            this.realTimeDepartures.push({route: departure.route, time: departureTime});
            console.log(`Next departure in ${timeDifference} minutes: ${departure.route}`);
          }
        });
      }, 60000)
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
      this.fetchData();  // Fetch data immediately on mount
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
  display: flex;
  flex-direction: column
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

.loader {
    width: 48px;
    height: 48px;
    border: 5px solid #2b2b2b;
    border-bottom-color: #ffffff;
    border-radius: 50%;
    display: inline-block;
    box-sizing: border-box;
    animation: rotation 1s linear infinite;
    }

    @keyframes rotation {
    0% {
        transform: rotate(0deg);
    }
    100% {
        transform: rotate(360deg);
    }
    } 

.loading{
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  width: 100%;
  flex-direction: column;
  gap: 1rem;
}

.loading h2{
  color: white;
  font-size: 2em;
}

.departures-section{
  height: 100%;
}
</style>
