<template>
    <Selector placeholder="From" ref="fromSelector" v-model="value"/>
    <Selector placeholder="To" ref="toSelector" v-model="value"/>
    <button @click="getSelectedValues()">Log Values</button>
</template>

<script>
import Selector from '@/components/Selector.vue'

export default {
  components: {
    Selector
  },
  methods:{
    getSelectedValues(){
      const from = this.$refs.fromSelector.value;
      const to = this.$refs.toSelector.value;
      console.log(from, to);
    }
  }
}
</script>
