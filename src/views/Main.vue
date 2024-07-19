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
        <div v-for="(departure, index) in realTimeDepartures.slice(0, realTimeSliceAmount)" :key="index" class="departure" :class="{onwardSlice : index >= onwardConnectionsSlicer}, {onwardHide : onwardConnectionsHide == true && index >= onwardConnectionsSlicer}" >
          <div>
            <h2 :class="departure.displayOperator" class="route">{{ departure.route }}</h2>
            <h2 class="route-placeholder">{{departure.route}}</h2>
          </div>
          <div class="center">
            <h4 class="destination">{{ departure.destination }}</h4>
            <div class="scrolling-section">
              <h5 class="operator" :class="{active : departure.minutesTo > 10 || this.noTrackingData || this.realTimeTrackingUpdates.length == 0}">{{ departure.operator }}</h5>
              <h5 class="tracking-info" :class="{active : departure.minutesTo <= 10 && this.realTimeTrackingUpdates.length != 0 && !this.noTrackingData}">
                <div class="line-tracker">
                  <span class="line">
                    <span class="ball">  <h3 class="origin_time">{{ departure.origin_time.slice(0,5) }}</h3></span>
                    <span class="ball-track" :style="{ left: index === 0 ? calculateLeftPosition(departure) : '' }"></span>
                    <span class="ball-end">  <h3 class="arrival_time">{{ departure.departureTime.slice(0,5) }}</h3></span>
                  </span>
                </div>
                <!-- {{this.realTimeTrackingUpdates.find(tracking => tracking.dep_time === departure.departureTime) ? this.realTimeTrackingUpdates.find(tracking => tracking.dep_time === departure.departureTime).distance : ''}} -->
              </h5>
            </div>
          </div>
          <div></div>
          <div class="times">
            <h5 class="minutes" :class="{active : scrollingSection2 == 0}">{{ departure.minutesTo }} min</h5>
            <h5 class="departure_time" :class="{active : scrollingSection2 == 1}">{{ departure.departureTime.slice(0,5) }}</h5>
          </div>
        </div>
      </div>
      <div v-if="this.realTimeDepartures.length == 0 && !loadingDepartures" class="no-departures">
        <h2>No departures found</h2>
      </div>
    </div>
    <div>
    <div class="connections-list" :class="{ connectionsDisplay: this.onwardConnectionsDisplay}, { connectionsActive : this.onwardConnectionsActive}">
      <div class="header">
        <h2>Onward Connections</h2>
        <h3>{{this.onwardConnectionsStopsDisplay}}</h3>
      </div>
    </div>
    </div>
  </div>
</template>

<script>

import axios from 'axios';
import overrides from '@/assets/stop_override.json';

import config from '@/assets/config.json';

const min_lat = config.min_lat;
const max_lat = config.max_lat;
const min_long = config.min_long;
const max_long = config.max_long;
const banned_onward_connection_stop = config.excludedOnwardConnectionStop;
const timetables = config.timetables;
const routes_to_include = config.routes_to_include;
const no_tracking_routes = config.no_tracking_routes;
const real_time_slice_amount = config.real_time_slice_amount;
const GracePeriodTime = config.grace_period_time // minutes
const WithinRadiusGrace = config.within_radius_grace // minutes

export default {
  data() {
    return {
      thisStop: config.thisStop,
      displayName: config.displayName,
      onwardConnectionsStopsName: config.onwardConnectionsStopsName,
      onwardConnectionsStopsDisplay: config.onwardConnectionsStopsDisplay,
      filteredDestination: config.filteredDestination,
      currentTime: "00:00",
      currentDate: null,
      thisStopRoutes: [],
      thisStopDepartures:[],
      realTimeDepartures: [],
      realTimeOnwardConnections:[], 
      onwardConnectionDepartures: [],
      apiData: null,
      intervalId: null,
      trainStationCRS: config.trainStationCRS,
      trainData: null,
      GracePeriodStorage: GracePeriodTime,

      realTimeTrackingUpdates: [],

      timeToggle: true,
      currentTimeTogglePg: 0,
      loadingDepartures: true,
      onwardConnectionsSlicer: real_time_slice_amount,
      onwardConnectionsHide: false,
      onwardConnectionsDisplay: false,
      onwardConnectionsActive: false,

      scrollingSection1: 0,
      scrollingSection2: 0,
      realTimeSliceAmount: real_time_slice_amount,
      noTrackingData: false,
    }
  },
  methods: {
    async fetchData() {
      axios.get('http://localhost:5000/gtfs-data', {
        params: {
          min_lat: min_lat,
          max_lat: max_lat,
          min_long: min_long,
          max_long: max_long,
          banned_onward_connection_stop: banned_onward_connection_stop,
          zip_path: timetables[0],
          routes_to_include: routes_to_include
        }
      })
      .then(response => {
        this.apiData = response.data;
        this.setupBoard();
      })
      .catch(error => {
        console.error('There was an error fetching the GTFS data:', error);
      });
    },
    async getTrackingData(routeNumber){
      // Get the latitude and longitude of the stop with matching stop name
      const stop = this.apiData['allStops'].find(stop => stop.stop_name === this.thisStop);
      const allstops = this.apiData['allStops'].filter(stop => stop.stop_name !== this.thisStop);
      const latitude = stop ? stop.stop_lat : null;
      const longitude = stop ? stop.stop_lon : null;
      
      // Use the latitude and longitude in your code
      console.log("Latitude:", latitude);
      console.log("Longitude:", longitude);

      if(no_tracking_routes.includes(routeNumber)){
        console.warn(`Route ${routeNumber} is in the list of routes with disabled tracking`)
      }else{
        try {
          const response = await axios.get('http://localhost:5000/tracking-data', {
            params: {
              min_lat: min_lat,
              max_lat: max_lat,
              min_long: min_long,
              max_long: max_long,
              this_stop_lat: latitude,
              this_stop_long: longitude,
              allstops: allstops,
              routeNumber: routeNumber
            },
            headers: {
              'Access-Control-Allow-Origin': '*'
            }
          });
          console.log(response.data);
          // Assign the response data to a variable or use it in your code
          const responseData = response.data;
          console.log("response data", responseData);
          return responseData;
        } catch (error) {
          console.error('There was an error fetching the GTFS data:', error);
        }
      }
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
                      origin_time: stopTimes[0]['departure_time'].replace(/^24:/, '00:').replace(/^25:/, '01:').replace(/^26:/, '02:').replace(/^27:/, '03:'),
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
                    origin_time: stopTimes[0]['departure_time'].replace(/^24:/, '00:').replace(/^25:/, '01:').replace(/^26:/, '02:').replace(/^27:/, '03:'),
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
                          origin_time: stopTimes[0]['departure_time'].replace(/^24:/, '00:').replace(/^25:/, '01:').replace(/^26:/, '02:').replace(/^27:/, '03:'),
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
      this.setupTracking();
    },
    async setupTracking(){
      const departures = this.realTimeDepartures.slice(0, this.realTimeSliceAmount);
      this.realTimeTrackingUpdates = [];

      for (const departure of departures) {
        var data = await this.getTrackingData(departure.route);
        console.log("data", data);  
        if (data) {
          this.realTimeTrackingUpdates.push({
            route: departure.route,
            dep_time: departure.departureTime,
            status: data.status,
            distance: data.distance,
            time_estimate: data.estimated_time,
            percentage: data.percentage,
            towardsStop: data.towardsStop,
            withinRadius: data.withinRadius
          });
        } else {
          console.error('Error fetching tracking data for route:', departure.route);
          this.realTimeTrackingUpdates.push({
            route: departure.route,
            dep_time: departure.departureTime,
            status: 'No data available',
            distance: "No data available",
            time_estimate: "No data available",
            towardsStop: false,
            withinRadius: false,
            percentage: "0",
          });
        }
      }
      console.log("Tracking updates for bus: ", this.realTimeTrackingUpdates);

      setInterval(async () => {
        this.realTimeTrackingUpdates = [];
        for (const departure of departures) {
          var data = await this.getTrackingData(departure.route);
          console.log("data", data);  
          if (data) {
            this.realTimeTrackingUpdates.push({
              route: departure.route,
              dep_time: departure.departureTime,
              status: data.status,
              distance: data.distance,
              time_estimate: data.estimated_time,
              percentage: data.percentage,
              towardsStop: data.towardsStop,
              withinRadius: data.withinRadius
            });
          } else {
            console.error('Error fetching tracking data for route:', departure.route);
            this.realTimeTrackingUpdates.push({
              route: departure.route,
              dep_time: departure.departureTime,
              status: 'No data available',
              distance: "No data available",
              time_estimate: "No data available",
              towardsStop: false,
              withinRadius: false,
              percentage: "0",
            });
          }
        }
        console.log("Tracking updates for bus: ", this.realTimeTrackingUpdates);
      }, 60000);
      

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

          const GracePeriod = this.GracePeriodStorage * 60 * 1000; // 5 minutes in milliseconds

          const timeDifference = departureTime.getTime() - currentTime.getTime();

            

          if (timeDifference >= -GracePeriod) {
            if (!departure['destination'].includes(this.filteredDestination)){
              this.realTimeDepartures.push({
                origin_time: departure['origin_time'].replace(/^24:/, '00:').replace(/^25:/, '01:').replace(/^26:/, '02:').replace(/^27:/, '03:'),
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
                  origin_time: departure['origin_time'].replace(/^24:/, '00:').replace(/^25:/, '01:').replace(/^26:/, '02:').replace(/^27:/, '03:'),
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
          this.scrollingSection2 = 1;
          this.sleep(5000)
          .then(() => {
            this.scrollingSection2 = 0;
          })
        });
      }, 10000);

      // setInterval(() => {
      //   this.sleep(5000)
      //   .then(() => {
      //     this.scrollingSection1 = 1;
      //     this.sleep(25000)
      //     .then(() => {
      //       this.scrollingSection1 = 0;
      //     })
      //   });
      // }, 30000);

      if(this.onwardConnectionDepartures && this.realTimeOnwardConnections){
        setInterval(() => {
          this.sleep(20000)
          .then(() => {
            this.onwardConnectionsHide = true;
            this.sleep(1000)
            .then(() => {
              this.onwardConnectionsSlicer = 3;
              this.onwardConnectionsDisplay = true;
              this.sleep(1000)
              .then(() => {
                this.onwardConnectionsActive = true;
                this.sleep(20000)
                .then(() => {
                    this.onwardConnectionsActive = false;
                    this.sleep(1000)
                    .then(() => { 
                      this.onwardConnectionsDisplay = false;
                      this.onwardConnectionsSlicer = real_time_slice_amount;
                      this.sleep(1000)
                      .then(() => {
                        this.onwardConnectionsHide = false;
                      })
                    })
                })
              })
            })
          });
        }, 44000);
      }
    },
    calculateLeftPosition(departure){
      // Ensure realTimeTrackingUpdates is defined and departure has a departureTime
      if (!this.realTimeTrackingUpdates || !departure || !departure.departureTime) {
        return "50%"; // Default position if data is not available
      }

      const tracking = this.realTimeTrackingUpdates.find(t => t.dep_time === departure.departureTime);
      console.log("TRACKING", tracking);

      if (tracking) {
        if (tracking.distance == "No data available"){
          this.noTrackingData = true;
        }else{
          this.noTrackingData = false;
        }

        if (tracking.towardsStop) {
          const percent = tracking.percentage;
          console.log("percent", percent);
          console.log("within radius ", tracking.withinRadius);
          if(tracking.withinRadius){
            this.GracePeriodStorage = WithinRadiusGrace;
            return "95.25%";
          }else{
            this.GracePeriodStorage = GracePeriodTime
            if(percent == 0){
              return "-8px";
            }else{
              return percent + "%";
            }
          }
        } else {
          if(tracking.withinRadius){
            this.GracePeriodStorage = WithinRadiusGrace;
            return "95.25%";
          }else{
            this.GracePeriodStorage = GracePeriodTime
            return "-8px";
          }
        } 
      } else {
        // If no tracking data matches, return "50%"
        return "-8px";
      }
    }
  },
  mounted() {
      this.fetchData();  // Fetch data immediately on mount
      this.currentTimeLoop();
      this.timeToggler();
      this.scrollingSections();
      // Set up any other necessary intervals or events...
  },   
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
  height: 73px;
  min-height: 73px;
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
  height: auto;
  padding-top: 2rem;
  padding-left: 1.5rem;
  padding-right: 1.5rem;
  padding-bottom: 1.5rem;
  min-height: 40%;
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
  position: relative;
  transition: 0.5s
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
  position: absolute;
  top: 0;
}

.departure .route-placeholder{
  font-size: 2.5em;
  position: relative;
  opacity: 0;
  visibility: hidden;
}

.departure .operator{
  font-style: italic;
  color: rgb(150,150,150);
  position: absolute;
  top: 0;
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

.tracking-info{
  position: relative;
  top: 0%;
  width: 100%;
  left: 0%;
  height: 1rem;
  transition: 0.5s;
  border: 1px solid rgb(50,50,50);
  margin-top: 1rem;
  border-radius: 0.3rem;
  padding-top: 0.7rem;
  padding-left: 2rem;
  padding-right: 2rem;
}

.tracking-info.active{
  height: 5rem;
}

.onwardSlice {
  display: none;
}

.onwardHide{
  opacity: 0;
}

.connections-list{
  display: none;
  opacity: 0;
  transition: 0.5s;
  gap: 1rem;
  position: relative;
  width: 100%;
  height: 100%;
  padding-left: 1.5rem;
  padding-right: 1.5rem;
}

.connections-list .header{
  color: white;
  font-size: 1.5em;
  position: absolute;
  top: 0;
  left: 0;
  border-top: 2px solid white;
  border-bottom: 2px solid white;
  height: 73px;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  display: flex;
  padding-left: 1.5rem;
  padding-right: 1.5rem;
}

.header h3{
  font-size: 0.7em;
  font-style: italic;
  color: rgb(150,150,150)
}

.connections-list.connectionsDisplay{
  display: flex;
}

.connections-list.connectionsActive{
  opacity: 1;
}

.line-tracker{
  width: 100%;
  height: 50%;
  position: relative; 
}

.line-tracker .line{
  width: 100%;
  height: 2px;
  background: rgb(134, 134, 134);
  position: absolute;
  top: 50%;
  left: 0;
  transform: translateY(-50%);
}

.line-tracker .line .ball{
  width: 10px;
  height: 10px;
  background: rgb(255, 255, 255);
  border-radius: 50%;
  position: absolute;
  top: 50%;
  left: 0;
  transform: translateY(-50%);
}

.line-tracker .line .ball-end{
  width: 10px;
  height: 10px;
  background: rgb(255, 255, 255);
  border-radius: 50%;
  position: absolute;
  top: 50%;
  right: 0;
  transform: translateY(-50%);
}

.line-tracker .line .ball-track{
  width: 25px;
  height: 25px;
  background: rgb(0, 0, 0);
  border: 3px solid white;
  border-radius: 50%;
  position: absolute;
  top: 50%;
  left: 0;
  transform: translateY(-50%);
  transition: 1.5s;
  z-index: 200;
}

.origin_time{
  font-size: 0.8em;
  transform: translate(-30%, 100%);
  display: inline-block;
  position: absolute;
}

.arrival_time{
  font-size: 0.8em;
  transform: translate(-30%, 100%);
  display: inline-block;
  position: absolute;
}

.no-departures h2{
  color: white;
  font-size: 2em;
  text-align: center;
}

.no-departures{
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  
}


</style>
