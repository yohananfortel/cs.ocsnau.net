<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const errorMessage = ref('')
const isModalOpen = ref(false)

// 1. Функція оновлення токена (замість кук використовуємо localStorage)
const refreshAccessToken = async () => {
  const storedRefreshToken = localStorage.getItem('refreshToken')
  
  if (!storedRefreshToken) return // Якщо токена немає, ми просто гість

  try {
    const response = await fetch('https://cs.ocsnau.net/nxrfzzjm_server/refresh.php', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      // Передаємо refreshToken у тілі запиту, бо кук більше немає
      body: JSON.stringify({ refreshToken: storedRefreshToken })
    })
    
    if (response.ok) {
      const data = await response.json()
      if (data.accessToken) {
        // Зберігаємо нові токени (якщо сервер при рефреші видав і новий refreshToken теж)
        localStorage.setItem('accessToken', data.accessToken)
        if (data.refreshToken) localStorage.setItem('refreshToken', data.refreshToken)
        
        auth.login(data.accessToken)
      }
    } else {
      // Якщо токен протух або невалідний — виходимо
      handleLogout()
    }
  } catch (err) {
    console.warn('Помилка оновлення сесії')
  }
}

onMounted(() => {
  refreshAccessToken()
})

// 2. Логін
const handleLoginSubmit = async () => {
  try {
    const response = await fetch('https://cs.ocsnau.net/nxrfzzjm_server/auth.php', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: username.value, password: password.value })
    })

    const text = await response.text(); // Спочатку отримуємо як текст
    try {
      const data = JSON.parse(text); // Пробуємо перетворити в JSON
      if (response.ok) {
        localStorage.setItem('accessToken', data.accessToken);
        localStorage.setItem('refreshToken', data.refreshToken);
        auth.login(data.accessToken);
        isModalOpen.value = false;
      } else {
        errorMessage.value = data.error || 'Помилка авторизації';
      }
    } catch (jsonErr) {
      console.error("Сервер повернув не JSON:", text);
      errorMessage.value = "Помилка на сервері. Подивіться консоль.";
    }
  } catch (err) {
    errorMessage.value = "Не вдалося з'єднатися з сервером";
  }
}

// 3. Вихід (обов'язково чистимо localStorage)
const handleLogout = () => {
  localStorage.removeItem('accessToken')
  localStorage.removeItem('refreshToken')
  auth.logout()
}

const handleAuthAction = () => {
  if (auth.token) {
    handleLogout()
  } else {
    isModalOpen.value = true
  }
}

const closeModal = () => {
  isModalOpen.value = false
}
</script>

<template>
  <header class="header">
        <div class="header-top-line"></div>

        <router-link :to="{ path: '/' }">
          <img class="header__logo" src="https://ocsnau.net/wp-content/themes/ocsnau_v3/assets/images/logo_ukr_color.png?v=2" alt="Емблема">
        </router-link>
        
        <div class="header__text">
            Компʼютерні науки
        </div>
        <button @click="handleAuthAction" class="auth-btn">
            {{ auth.token ? 'Вийти' : 'Увійти' }}
        </button>
        
        <div v-if="isModalOpen" class="modal-overlay" @click.self="closeModal">
          <div class="modal-content">
            <button class="close-btn" @click="closeModal">&times;</button>
            
            <h2>Вхід в систему</h2>
            <div class="login-form">
              <input 
                  v-model="username" 
                  type="text" 
                  placeholder="Логін"
                >
                <input 
                  v-model="password" 
                  type="password" 
                  placeholder="Пароль"
                  @keyup.enter="handleLoginSubmit" 
                >
                
                <p v-if="errorMessage" style="color: red; font-size: 0.8em; margin: 0;">
                  {{ errorMessage }}
                </p>

                <button @click="handleLoginSubmit" class="submit-btn">
                  Підтвердити
                </button>
            </div>
          </div>
        </div>

    </header>

  <RouterView />
</template>

<style scoped>
:root {
    --r-main-font: 'Roboto', sans-serif;
    --r-heading-font: 'Roboto', sans-serif;
    --college-blue: #005f47;
    --header-height: 120px;
}

body { 
    font-family: sans-serif; 
    line-height: 1.6; 
    padding: 0; 
    margin: 0;
    background-color: #ffffff;
}

header {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: var(--header-height);
    background: #fff;
    border-bottom: 2px solid var(--college-blue);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 5px;
    box-sizing: border-box;
    z-index: 9999;
    font-family: var(--r-main-font);
}

@media (min-width: 600px) {
  header {
    padding: 0 30px;
  }
}

.header__logo {
    height: 40px; 
    width: auto;
    margin-right: 20px;
}

@media (min-width: 600px) {
  .header__logo {
    height: 80px; 
    width: auto;
    margin-right: 20px;
}
}

h1 {
    margin-top: calc(var(--header-height) + 20px);
    margin-left: 20px;
    font-family: var(--r-main-font);
}

.header-top-line {
    height: 15px;
    background-color: var(--college-blue);
    width: 100%;
    position: absolute;
    top: 0;
    left: 0;
}



.header-text {
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.college-name {
    font-size: 14px;
    font-weight: 700;
    color: #555;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

#dynamic-slide-title { 
    font-size: 42px;
    font-weight: 900;
    text-transform: uppercase;
    color: #000000;
}

.reveal .slides section h2 {
    display: none;
}

.reveal .slides {
    margin-top: var(--header-height) !important;
}

.smart-block-1 {
    background-color: #03a44221;
    border-left: 6px solid var(--college-blue);
    padding: 10px 15px;
    margin: 15px 0;
    border-radius: 4px;
}

ul { 
    margin-top: 20px;
    padding: 0 20px;
    list-style: none;
}

li { 
    background: #fff; 
    margin-bottom: 10px; 
    padding: 15px; 
    border-radius: 5px; 
    box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
}

a { 
    text-decoration: none; 
    color: #007bff; 
    font-weight: bold; 
    font-size: 1.1em; 
}

a:hover { color: #0056b3; }

.date { 
    font-size: 0.8em; 
    color: #888; 
    margin-left: 10px; 
}

.trainer-container { 
    font-family: sans-serif; 
    padding: 20px; 
    background: #f9f9f9; 
    border-radius: 10px; 
    color: #333; 
}

.truth-table, #kmap-trainer-table { 
    border-collapse: collapse; 
    background: white; 
}

.truth-table th, .truth-table td, #kmap-trainer-table th, #kmap-trainer-table td {
    border: 1px solid #ccc; 
    padding: 8px 12px; 
    text-align: center;
}

.truth-table th { background: #eee; }

.kmap-wrapper { 
    position: relative; 
    padding-top: 20px; 
    padding-left: 20px; 
}

.label-ab { 
    position: absolute; 
    top: 0; 
    left: 80px; 
    font-weight: bold; 
    font-size: 0.9em; 
}

.label-c { 
    position: absolute; 
    top: 45px; 
    left: 0; 
    font-weight: bold; 
    font-size: 0.9em; 
}

#kmap-trainer-table input {
    width: 30px; 
    height: 30px; 
    text-align: center; 
    font-size: 1.2em;
    border: 1px solid #aaa; 
    border-radius: 4px;
}

.controls { 
    margin-top: 20px; 
    display: flex; 
    gap: 10px; 
}

button { 
    padding: 10px 20px; 
    cursor: pointer; 
    border: none; 
    border-radius: 5px; 
    background: #007bff; 
    color: white; 
    font-weight: bold; 
}

button:hover { background: #0056b3; }

#kmap-feedback { 
    margin-top: 15px; 
    font-weight: bold; 
    min-height: 1.2em; 
}

.correct-cell { background-color: #d4edda !important; }
.wrong-cell { background-color: #f8d7da !important; }

.logo {
  display: block;
  margin: 0 auto 2rem;
}

nav {
  width: 100%;
  font-size: 12px;
  text-align: center;
  margin-top: 2rem;
}

nav a.router-link-exact-active {
  color: var(--color-text);
}

nav a.router-link-exact-active:hover {
  background-color: transparent;
}

nav a {
  display: inline-block;
  padding: 0 1rem;
  border-left: 1px solid var(--color-border);
}

nav a:first-of-type {
  border: 0;
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }

  nav {
    text-align: left;
    margin-left: -1rem;
    font-size: 1rem;

    padding: 1rem 0;
    margin-top: 1rem;
  }
}
.auth-btn {
  padding: 8px 20px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: 0.3s;
}
.auth-btn:hover {
  background-color: #3aa876;
}

/* Затемнення фону */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5); /* напівпрозорий чорний */
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000; /* вище за ваш хедер */
}

/* Контейнер вікна */
.modal-content {
  background: white;
  padding: 30px;
  border-radius: 12px;
  position: relative;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.2);
}

/* Кнопка закриття (хрестик) */
.close-btn {
  position: absolute;
  top: 10px;
  right: 15px;
  background: none;
  border: none;
  font-size: 24px;
  color: #333;
  cursor: pointer;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-top: 20px;
}

.login-form input {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

/* Затемнення фону */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5); /* напівпрозорий чорний */
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000; /* вище за ваш хедер */
}

/* Контейнер вікна */
.modal-content {
  background: white;
  padding: 30px;
  border-radius: 12px;
  position: relative;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.2);
}

/* Кнопка закриття (хрестик) */
.close-btn {
  position: absolute;
  top: 10px;
  right: 15px;
  background: none;
  border: none;
  font-size: 24px;
  color: #333;
  cursor: pointer;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-top: 20px;
}

.login-form input {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
</style>
