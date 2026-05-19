<script setup lang="ts">
import { ref, onMounted } from 'vue'
import draggable from 'vuedraggable'
import { useAuthStore } from '@/stores/auth'

// 1. Описуємо структуру об'єкта дисципліни
interface Discipline {
  id: string | number;
  topic: string;
  slug: string;
  order: number;
}

const auth = useAuthStore()

const newSubjectName = ref('')

// 2. Вказуємо цей тип для ref
const disciplines = ref<Discipline[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const fetchData = async () => {
  try {
    const response = await fetch('https://cs.ocsnau.net/nxrfzzjm_server/courses.php')
    if (!response.ok) throw new Error('Помилка мережі')
    
    // Тепер data явно типізована
    const data: Discipline[] = await response.json()
    disciplines.value = data
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Невідома помилка'
  } finally {
    loading.value = false
  }
}

// Додавання нової дисципліни
const addNewSubject = async () => {
  if (!newSubjectName.value) return
  
  try {
    const res = await fetch('https://cs.ocsnau.net/nxrfzzjm_server/courses.php', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json' // Важливо для POST запитів з JSON
      },
      body: JSON.stringify({ 
        name: newSubjectName.value,
        action: 'create'
      })
    })

    const data = await res.json()

    // Якщо сервер повертає масив або статус 200/201, вважаємо це успіхом
    if (res.ok && Array.isArray(data)) {
      disciplines.value = data // Можна відразу оновити список без зайвого fetchData()
      newSubjectName.value = '' 
    } else if (data.success) { // На випадок, якщо API колись поверне {success: true}
      await fetchData()
      newSubjectName.value = ''
    } else {
      throw new Error('Сервер повернув неочікувану відповідь')
    }
  } catch (err) {
    alert('Помилка при додаванні дисципліни')
    console.error(err)
  }
}

const onDragEnd = async () => {
  try {
    const orderData = disciplines.value.map((item, index) => ({
      id: item.id,
      order: index
    }))

    console.log('Новий порядок:', orderData)

    const res = await fetch('https://cs.ocsnau.net/nxrfzzjm_server/courses.php', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        order: orderData,
        action: 'update_order'
      })
    })

    console.log('Сервер відповів на оновлення порядку:', res.text())

    if (!res.ok) throw new Error('Помилка мережі при оновленні порядку')
    
    // Не обов'язково чекати відповіді, якщо сервер не повертає оновлений список
    // Але можна додатково перевірити статус або повідомлення від сервера
  } catch (err) {
    alert('Помилка при оновленні порядку дисциплін')
    console.error(err)
  }
}


onMounted(() => {
  fetchData()
})
</script>

<template>
  <h1>Доступні курси</h1>

  <p v-if="loading">Завантаження...</p>
  <p v-else-if="error" style="color: red">{{ error }}</p>
  <ul v-else>

    <draggable 
      v-model="disciplines" 
      item-key="id" 
      tag="ul" 
      :animation="200"
      ghost-class="ghost-card"
      @end="onDragEnd"
      :disabled="!auth.token" 
    >
      <template #item="{ element }">

    <li class="discipline-item">
      <span>{{ element.topic }}</span>
      
      <router-link :to="{ name: 'course', params: { slug: element.slug } }" class="btn">
        Переглянути
      </router-link>

      <span v-if="auth.token" style="margin-left: 10px; color: gray;">
      order: {{ element.order }}
      </span>

    </li>
      </template>
    </draggable>


    <li v-if="auth.token" class="add-new-inline">
        <input v-model="newSubjectName" placeholder="Нова дисципліна..." />
        <button @click="addNewSubject">＋</button>
  </li>

  </ul> 

</template>

<style scoped>
button {
  background: var(--college-blue, #005f47);
  color: white;
  border: none;
  padding: 8px 12px;
  cursor: pointer;
}
</style>