<template lang="">
    <div class="select" :class='{focus : inputFocus}, {dropdownOpen:  this.value != "" && this.value.length > 2 && this.filtered.length != 0}'>
        <input v-model="value" @focus="inputFocus = true" @blur="handleBlur()" @input="filteredStations()">
        <h3 :class="{active : this.value != ''}">{{placeholder}}</h3>
        <div class="dropdown-menu" :class="{dropdownActive: inputFocus && this.value != '' && this.value.length > 2 && this.filtered.length != 0}, {focus : inputFocus}">
            <ul>
                <li v-for="station in filtered.slice(0,4)" :key="station.station_id" @click="setValue(station.station_name)">{{station.station_name}}</li>
            </ul>
        </div>
    </div>
    
</template>
<script>
import stations from '@/assets/stations.json';
export default {
    data() {
        return {
            stations: stations,
            value: '',
            inputFocus: false,
            filtered: []
        }
    },
    props: ['placeholder'],
    methods: {
        filteredStations() {
            const lowercaseValue = this.value.toLowerCase();
            var filtered = this.stations.filter(station => station.station_name.toLowerCase().startsWith(lowercaseValue));
            this.filtered = filtered.map(station => ({
                ...station,
                station_name: `${station.station_name} (${station.stationCRS})`
            }));
            console.log(filtered);
        },
        setValue(name){
            this.value = name;
        },
        handleBlur(){
            setTimeout(() => {
                this.inputFocus = false;
            }, 100);
        }
    },
}
</script>
<style>
    .select{
        width: 100%;
        padding: 0.3rem;
        font-size: 24px;
        border: 1px solid #ccc;
        border-radius: 5px;
        display: flex;
        position: relative;
        margin: 0.5rem;
    }
    .select input{
        width: 100%;
        border: none;
        outline: none;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
        font-size: 20px;
        padding-top: 0.3rem;
        padding-bottom: 0.3rem;

    }
    svg{
        width: 1rem;
        height: 1rem;
        stroke: black;
        stroke-width: 0.2rem;
    }
    .select h3{
        font-size: 14px;
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        left: 0.5rem;
        transition: 0.2s;
    }
    .select input:focus + h3{
        top: -3%;
        left: 1rem;
        background: white;
    }
    .select h3.active{
        top: -3%;
        left: 1rem;
        background: white;
    }
    .select.focus{
        border: 1px solid #000000;

    }
    .dropdown-menu{
        position: absolute;
        width: 100%;
        top: 100%;
        background: white;
        border: 1px solid #ccc;
        left: 0%;
        border-radius: 0.3rem;
        display: none;
        border-top-left-radius: 0;
        border-top-right-radius: 0;
        padding-top: 0.7rem;
        padding-bottom: 0.7rem;
        z-index: 200;
    }
    .dropdownActive{
        display: block;
    }
    .dropdownOpen{
        border-bottom-left-radius: 0;
        border-bottom-right-radius: 0;
    }
    .dropdown-menu.focus{
        border: 1px solid #000000;
    }
    .dropdown-menu li{
        font-size: 18px;
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
        text-align: left;
        padding-left: 0.7rem;
        position: relative;
        width: fit-content;
    }
    .dropdown-menu li:hover{
        cursor: pointer;
    }
    .dropdown-menu li:hover::before{
        content: '';
        height: 2px;
        bottom: 10%;
        position: absolute;
        background: rgb(0, 94, 216);
        display: inline-block;
        width: 100%;
    }
</style>