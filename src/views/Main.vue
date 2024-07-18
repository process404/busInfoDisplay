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
      <div class="departures-list">
        <div v-for="departure in this.realTimeDepartures.slice(0,3)" class="departure">
          <h2 :class="departure.displayOperator" class="route">{{ departure.route }}</h2>
          <div class="center">
            <h4 class="destination">{{ departure.destination }}</h4>
            <div class="scrolling-section">
              <h5 class="operator" :class="{active : scrollingSection1 == 0}">{{ departure.operator }}</h5>
            </div>
          </div>
          <div class="times">
            <h5 class="minutes" :class="{active : scrollingSection2 == 0}">{{ departure.minutesTo }} min</h5>
            <h5 class="departure_time" :class="{active : scrollingSection2 == 1}">{{ departure.departureTime.slice(0,5) }}</h5>
          </div>
        </div>
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
      displayName: "Edge Hill (Forest Court)",
      onwardConnectionsStopsName: "Bus Station",
      onwardConnectionsStopsDisplay: "Ormskirk Bus Station",
      filteredDestination: "Ormskirk", // Exclude buses with destination as this
      currentTime: "00:00",
      currentDate: null,
      thisStopRoutes: [],
      thisStopDepartures:[],
      realTimeDepartures: [],
      realTimeOnwardConnections:[], 
      onwardConnectionDepartures: [],
      apiData: null,
      intervalId: null,
      trainStationCRS: "OMS",
      trainData: null,

      timeToggle: true,
      currentTimeTogglePg: 0,
      loadingDepartures: true,



      scrollingSection1: 0,
      scrollingSection2: 0,
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
      const now = new Date();
      const today = new Date();
      // Check if the current time is before 3am
      if (now.getHours() < 3) {
        // Subtract one day from today
        today.setDate(today.getDate() - 1);
      }
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
            let operator = this.apiData['routes'][route]['operator']
            if(operator.includes(" ")){
                operator = this.apiData['routes'][route]['operator'].split(" ")[0] + " " + this.apiData['routes'][route]['operator'].split(" ").slice(1).join("-")
            }

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

          // console.log('Checking journey:', journeyData);
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
                    const routeNumber = route;
                    const operator = this.apiData['routes'][route]['operator'];
                    this.thisStopDepartures.push({
                      route: routeNumber,
                      operator: operator,
                      destination: journeyData['destination'],
                      departure_time: stopTime['departure_time'].replace(/^24:/, '00:').replace(/^25:/, '01:').replace(/^26:/, '02:').replace(/^27:/, '03:')
                    });
                  }
                }else{
                  console.log('Adding departure:', stopTime);
                  const routeNumber = route;
                  const operator = this.apiData['routes'][route]['operator'];
                  this.thisStopDepartures.push({
                    route: routeNumber,
                    operator: operator,
                    destination: journeyData['destination'],
                    departure_time: stopTime['departure_time'].replace(/^24:/, '00:').replace(/^25:/, '01:').replace(/^26:/, '02:').replace(/^27:/, '03:')
                  });
                }
              }
            }
          }
        }
      }
      console.log('Final departures:', this.thisStopDepartures);

      console.log("Starting to process stops");
      this.onwardConnectionDepartures = [];

      for (const stop of this.apiData['allStops']) {
        if (stop.stop_name.includes(this.onwardConnectionsStopsName)){
          console.log(`Stop ${stop.stop_name} matches criteria`);
          for (const route in this.apiData['routes']) {
            for (const journey in this.apiData['routes'][route]['journeys']) {
              const journeyData = this.apiData['routes'][route]['journeys'][journey];
              const runningDays = journeyData['running_days'];
              const noServiceDates = journeyData['no_service_dates'];

              if (!noServiceDates.includes(today.toISOString().split('T')[0]) && runningDays[currentDayOfWeek] === 1) {
                const stopTimes = journeyData['stop_times'];
                for (const stopTime of stopTimes) {
                  if (stopTime['stop_name'] === stop.stop_name) {
                    const stopOverride = overrides.stop_override.find(stop => stop.stop_name === this.thisStop);
                    if (stopOverride) {
                      const overrideTimes = stopOverride.min_ph_override; // Assuming this is an array of numbers
                      const departureTime = stopTime['departure_time'].split(':');
                      const minute = parseInt(departureTime[1], 10); // Convert minute to number
                      if (!overrideTimes.includes(minute)) { // Now both are numbers
                        console.log('Adding departure:', stopTime);
                        const routeNumber = route;
                        const operator = this.apiData['routes'][route]['operator'];
                        this.onwardConnectionDepartures.push({
                          route: routeNumber,
                          operator: operator,
                          destination: journeyData['destination'],
                          departure_time: stopTime['departure_time'].replace(/^24:/, '00:').replace(/^25:/, '01:').replace(/^26:/, '02:').replace(/^27:/, '03:')
                        });
                      }
                    }else{
                      console.log('Adding departure:', stopTime);
                      const routeNumber = route;
                      const operator = this.apiData['routes'][route]['operator'];
                      this.onwardConnectionDepartures.push({
                        route: routeNumber,
                        operator: operator,
                        destination: journeyData['destination'],
                        departure_time: stopTime['departure_time'].replace(/^24:/, '00:').replace(/^25:/, '01:').replace(/^26:/, '02:').replace(/^27:/, '03:')
                      });
                    }
                  }
                }
              }else{
                console.log("No service today", route);
              }
            }
          }
        } else {
          console.log(`Stop ${stop.stop_name} does not match criteria`);
        }
      }

      if (this.onwardConnectionDepartures.length === 0) {
        console.log("No onward connections found. Check if journey data, dates, and stop names are correct.");
}else{
  console.log("onward connections: ", this.onwardConnectionDepartures);
}


      this.loadingDepartures = false;
      this.updateBoard();
    },
    updateLogic(){
      this.realTimeDepartures = [];
      this.realTimeOnwardConnections = [];
      const currentTime = new Date();
      console.log('Current Time:', currentTime);

      this.thisStopDepartures.forEach((departure) => {
        if (typeof departure['departure_time'] === 'string') {
          const departureTime = new Date(currentTime);
          const timeParts = departure['departure_time'].split(':');
          departureTime.setHours(parseInt(timeParts[0], 10), parseInt(timeParts[1], 10), 0, 0);

          const minutesTo = Math.floor((departureTime - currentTime) / 60000);
          let displayOperator = departure['operator'];

          if(displayOperator.includes(" ")){
                displayOperator = departure['operator'].split(" ")[0] + " " + departure['operator'].split(" ").slice(1).join("-")
            }

          if (departureTime >= currentTime) {
            if (!departure['destination'].includes(this.filteredDestination)){
              this.realTimeDepartures.push({
                route: departure['route'],
                departureTime: departure['departure_time'].replace(/^24:/, '00:').replace(/^25:/, '01:').replace(/^26:/, '02:').replace(/^27:/, '03:'),
                minutesTo: minutesTo,
                displayOperator: displayOperator,
                operator: departure['operator'],
                destination: departure['destination'] 
              });
              this.realTimeDepartures.sort((a, b) => a.departureTime.localeCompare(b.departureTime));
            }
            console.log('Adding real-time departure:', departure);
          }
        } else {
          console.log('Skipping departure due to undefined departure_time:', departure);
        }
      });

      console.log("real time departures", this.realTimeDepartures);

      this.onwardConnectionDepartures.forEach((departure) => {
        if (typeof departure['departure_time'] === 'string') {
          const departureTime = new Date(currentTime);
          const timeParts = departure['departure_time'].split(':');
          departureTime.setHours(parseInt(timeParts[0], 10), parseInt(timeParts[1], 10), 0, 0);
          
          const minutesTo = Math.floor((departureTime - currentTime) / 60000);
          let displayOperator = departure['operator'];

          if(displayOperator.includes(" ")){
            displayOperator = departure['operator'].split(" ")[0] + " " + departure['operator'].split(" ").slice(1).join("-")
          }

          if (departureTime >= currentTime) {
            if (!departure['destination'].includes(this.filteredDestination)) {
                this.realTimeOnwardConnections.push({
                  route: departure['route'],
                  departureTime: departure['departure_time'].replace(/^24:/, '00:').replace(/^25:/, '01:').replace(/^26:/, '02:').replace(/^27:/, '03:'),
                  minutesTo: minutesTo,
                  displayOperator: displayOperator,
                  operator: departure['operator'],
                  destination: departure['destination'] 
                });
                this.realTimeDepartures.sort((a, b) => a.departureTime.localeCompare(b.departureTime));
            }
            console.log('Adding real-time onward departure:', departure);
          }
        } else {
          console.log('Skipping departure due to undefined departure_time:', departure);
        }
      });

      console.log("real time onward connections", this.realTimeOnwardConnections);




    },
    updateBoard(){
      this.updateLogic();
      setInterval(() => {
        this.updateLogic();
      }, 60000)
    },
    currentTimeLoop(){
      setInterval(() => {
      let date = new Date();
      let hours = date.getHours();
      let minutes = date.getMinutes();
      let day = date.getDate();
      let month = date.getMonth() + 1;
      this.currentTime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
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
    },
    scrollingSections(){
      setInterval(() => {
        this.sleep(5000)
        .then(() => {
          this.scrollingSection1 = 0;
          this.scrollingSection2 = 1;
          this.sleep(5000)
          .then(() => {
            this.scrollingSection1 = 0;
            this.scrollingSection2 = 0;
          })
        });
      }, 10000);
    }
  },
  mounted() {
      this.fetchData();  // Fetch data immediately on mount
      this.currentTimeLoop();
      this.timeToggler();
      this.scrollingSections();
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
  padding-top: 2rem;
  padding-left: 1.5rem;
  padding-right: 1.5rem;
  padding-bottom: 1.5rem;
}

.departures-list{
  display: flex;
  gap: 1rem;
  flex-direction: column;
}

.departure{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1.5rem;
  border-bottom: 1px solid rgb(30,30,30);
  padding-bottom: 1.5rem;
}

.departure .center{
  width: 100%;
  display: flex;
  flex-direction: column;
}

.departure .center .scrolling-section-1 h5{
  font-size: 0.85rem;
}

.departure .center .destination{
  font-size: 2em;
  text-align: left;
  font-weight: 600;
}

.departure .times h5{
  font-size: 1.5em;
  text-align: right;
}

.departure .times{
  width: 20%;
  height: 100%;
}


.departure h2, .departure h4{
  color: white;
}

.departure h2{
  font-size: 3em;
  padding: 0.3rem;
  padding-left: 0.5rem;
  padding-right: 0.5rem;
  border-radius: 0.3rem;
  display: inline-block;
}

.departure .route{
  font-size: 2.5em;
}

.departure .operator{
  font-style: italic;
  color: rgb(150,150,150);
}

.departure h5{
  color: white;
  opacity: 0;
  transition: 0.5s;
}

.departure .active{
  opacity: 1;
}

.times h5{
  position: absolute;
  top: 0%;
  right: 0%;
}

.times .minutes{
  position: relative;
}

.times{
  position: relative;
}

.scrolling-section{
  position: relative;
}

</style>
