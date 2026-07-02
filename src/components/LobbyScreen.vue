<template>
  <div>
    <h2 class="screen-title">Очікування старту</h2>
    <p class="hint">
      Коли всі зайшли, адміністратор натискає Enter у вікні Python-сервера.
      Мінімум гравців: {{ minPlayers }}.
    </p>
    <p class="message">Підключено: {{ players.length }} / {{ maxPlayers }}</p>
  </div>
</template>

<script>
export default {
  name: "LobbyScreen",
  props: {
    players: {
      type: Array,
      required: true,
    },
    minPlayers: {
      type: Number,
      required: true,
    },
    maxPlayers: {
      type: Number,
      required: true,
    },
  },
};
</script>
