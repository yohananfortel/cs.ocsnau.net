<template>
  <div>
    <h2 class="screen-title">{{ message }}</h2>
    <p class="hint">Зараз з'явиться наступне питання.</p>
  </div>
</template>

<script>
export default {
  name: "WaitingScreen",
  props: {
    message: {
      type: String,
      required: true,
    },
  },
};
</script>
