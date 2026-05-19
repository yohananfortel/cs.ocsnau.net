<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import ModalCourseAdd from './ModalCourseAdd.vue';
const auth = useAuthStore()

const props = defineProps<{ slug: string }>() // Типізація пропсів
const loading = ref(true)
const error = ref<string | null>(null);
const showAddActionForm = ref(false)

import { ActionsAPI } from '@/api/actions'
import type router from '@/router';




// 1. Визначаємо emits (якщо цей компонент сам має щось надсилати вгору)
const emit = defineEmits(['created', 'close'])

const topic = ref('')
const type = ref('')

// або для списку:
const courseActions = ref<any[]>([]); // 'any' дозволить тимчасово ігнорувати помилки



const getCourseActions = async () => {
  try {
    courseActions.value = await ActionsAPI.getAll(props.slug)
  } catch (err) {
    error.value = (err as Error).message
  } finally {
    loading.value = false

    console.log('Отримані активності курсу:', courseActions.value) // Додайте цей рядок для перевірки отриманих даних
  }
}

const createAction = async () => {
  try {
    const newAction = await ActionsAPI.add(
      props.slug,
      topic.value,
      type.value
    )
    emit('created', newAction)
    emit('close')
  } catch (err) {
    console.error((err as Error).message)
  }
}

const handleActionCreated = (newAction: any) => {
  getCourseActions()
}

// 3. Додаємо функцію addAction, яку ви викликаєте в шаблоні @created="addAction"
const addAction = (newAction: any) => {
  courseActions.value.push(newAction)
  showAddActionForm.value = false
}

// Викликаємо функцію, коли компонент готовий
onMounted(() => {
  getCourseActions()
})
</script>


<template>
  <div class="lectures">
    <div class="sidebar">
      <h1>Структура курсу</h1>
      <router-link to="/">← Повернутися до списку дисциплін</router-link> <br />
     <router-link :to="`/knowledge-map`" class="knowledge-map-link">Переглянути карту знань</router-link>
    </div>
    
  

    <p v-if="loading">Завантаження...</p>
    <p v-else-if="error" style="color: red">{{ error }}</p>

    <div v-else class="cousre-items">
     <ul >
      <li v-for="(item, index) in courseActions" :key="index" class="discipline-item">

        <span v-if="JSON.parse(item.settings ).type === 'lecture'">Лекція</span>
        <span v-else-if="JSON.parse(item.settings ).type === 'test'">Тест</span>

        <span>{{ item.topic }} </span>
       
        <router-link :to="`/action/${item.id}`" class="details-link">Деталі</router-link>
     </li>
    </ul>

    <div v-if="auth.token" class="course-actions">
            <button @click="showAddActionForm = true" class="add-action-button">
            Додати активність
            </button>

            <ModalCourseAdd
            v-if="showAddActionForm"
            :slug="props.slug"
            @close="showAddActionForm = false"
            @created="handleActionCreated"
            />
    </div>
    
    
    <div>
        <span v-if="courseActions.length === 0">Немає доступних лекцій для цього курсу.</span>
        <br />
       </div>
    </div>
</div>

</template>


<style scoped>
.modal{
  position:fixed;
  inset:0;
  background:rgba(0,0,0,0.5);
  display:flex;
  justify-content:center;
  align-items:center;
}

.modal-content{
  background:white;
  padding:20px;
  border-radius:10px;
  width:400px;
}

.discipline-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #ccc;
}
.course-actions {
  margin-top: 20px;
}
.add-action-button {
  padding: 10px 20px;
  color: hsla(160, 100%, 37%, 1);
  border: none;
  border-radius: 5px;
  cursor: pointer;
  display: block;

  margin: 0 auto;
}
 
.lectures {
      margin: auto;
    width: 100%;
    display: flex;
    margin-top: 100px;
}

.cousre-items {width: 100%;}
</style>

