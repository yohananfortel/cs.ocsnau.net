<template>
  <div>
    <h2 class="screen-title">Гру завершено</h2>
    <p v-if="winner" class="hint">
      Переможець: <strong>{{ winner.name }}</strong>, {{ winner.score }} балів.
    </p>
    <p v-else class="hint">Немає переможця.</p>
  </div>
</template>

<script>
export default {
  name: "GameOver",
  props: {
    winner: {
      type: Object,
      default: null,
    },
  },
};
</script>
