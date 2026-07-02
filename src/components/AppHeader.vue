<template>
  <header class="topbar">
    <div class="brand">
      <h1>Quiz Game</h1>
      <span>Vue + Python WebSocket</span>
    </div>
    <div class="status">
      Статус: <strong>{{ statusText }}</strong>
    </div>
  </header>
</template>

<script>
export default {
  name: "AppHeader",
  props: {
    statusText: {
      type: String,
      required: true,
    },
  },
};
</script>
