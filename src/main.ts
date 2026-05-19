import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia' // 1. Імпортуємо
import App from './App.vue'
import router from './router'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia) // 2. Використовуємо
app.use(router)


app.mount('#app')
