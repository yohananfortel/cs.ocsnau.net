<script setup lang="ts">
import WelcomeItem from './WelcomeItem.vue'
import DocumentationIcon from './icons/IconDocumentation.vue'
import ToolingIcon from './icons/IconTooling.vue'
import EcosystemIcon from './icons/IconEcosystem.vue'
import CommunityIcon from './icons/IconCommunity.vue'
import SupportIcon from './icons/IconSupport.vue'

 
import { ref, onMounted } from 'vue'

// Створюємо реактивні змінні

const loading = ref(true)
const error = ref<string | null>(null);

// Створіть інтерфейс для даних лекції
interface Lecture {
  topic_name: string;
  markdown: string;
  id: number | string;
}

// Вкажіть цей тип у ref
const lecture = ref<Lecture | null>(null); 
// або для списку:
const disciplines = ref<any[]>([]); // 'any' дозволить тимчасово ігнорувати помилки

// Функція для отримання даних
const fetchData = async () => {
  try {
    const response = await fetch('https://cs.ocsnau.net/nxrfzzjm_server/topics.php', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json' // Важливо для POST запитів з JSON
      },
      body: JSON.stringify({ 
        action: 'create'
      })
    })


    if (!response.ok) throw new Error('Помилка мережі')
    
    const data = await response.json()
    disciplines.value = data
  } catch (err) {
    error.value = (err as Error).message;
  } finally {
    loading.value = false
  }
}

// Викликаємо функцію, коли компонент готовий
onMounted(() => {
  fetchData()
})
</script>





<template>
  <div class="lectures">
    <h1>Лекції з дисципліни</h1>
    <p>Тут буде список лекцій для обраного предмета.</p>
    <router-link to="/">← Повернутися до списку дисциплін</router-link>
  </div>

    <p v-if="loading">Завантаження...</p>
     <p v-else-if="error" style="color: red">{{ error }}</p>
     <ul v-else>
      <li v-for="(item, index) in disciplines" :key="index" class="discipline-item">
        <span>{{ item.topic_name }}</span>
        
        <router-link :to="{ name: 'lecture', params: { slug: item.id } }" class="btn">
          Переглянути
        </router-link>
     </li>
     </ul>

</template>

