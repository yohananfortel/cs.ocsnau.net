<template>
  <div>
    <h2 class="screen-title">Підключення до гри</h2>
    <p class="hint">
      Введи ім'я. Якщо сторінка запущена через Vite, Vue підключиться до Python-сервера на порту 5000.
    </p>
    <div class="form">
      <label>
        Ім'я гравця
        <input
          :value="name"
          maxlength="24"
          @input="$emit('update:name', $event.target.value.trim())"
          @keyup.enter="$emit('connect')"
        />
      </label>
      <button class="primary" :disabled="!name || connected" @click="$emit('connect')">
        Підключитися
      </button>
    </div>
    <p v-if="error" class="message bad">{{ error }}</p>
  </div>
</template>

<script>
export default {
  name: "ConnectScreen",
  props: {
    name: {
      type: String,
      required: true,
    },
    connected: {
      type: Boolean,
      required: true,
    },
    error: {
      type: String,
      default: "",
    },
  },
  emits: ["update:name", "connect"],
};
</script>
