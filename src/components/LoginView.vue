<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const email = ref('')
const password = ref('')
const auth = useAuthStore()
const router = useRouter()

const submitLogin = async () => {
  try {
    const response = await fetch('https://cs.ocsnau.net/nxrfzzjm_server/login.php', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value, password: password.value })
    })

    const data = await response.json()
    
    if (data.token) {
      auth.login(data.token) // Зберігаємо токен в Pinia
      router.push('/') // Перенаправляємо на головну
    } else {
      alert('Невірний логін або пароль')
    }
  } catch (err) {
    console.error("Помилка входу", err)
  }
}
</script>

<template>
  <div class="login-page">
    <h2>Вхід в систему</h2>
    <input v-model="email" type="email" placeholder="Email">
    <input v-model="password" type="password" placeholder="Пароль">
    <button @click="submitLogin">Підтвердити</button>
  </div>
</template>