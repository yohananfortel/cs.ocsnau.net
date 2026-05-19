<script setup lang="ts"> 
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ActionsAPI } from '@/api/actions'

// Імпортуємо компоненти
import LectureView from '@/components/LectureView.vue' // <-- Додано імпорт
import SelfTest from '@/components/course/action/SelfTest.vue' // <-- Додано імпорт
import QuizGame from '@/components/course/action/QuizGame.vue' // <-- Додано імпорт
import DuneGame from '@/components/course/action/DuneGame.vue'

interface ActiveAction {
  id: string | number;
  content: string;
  title?: string;
  type?: string;
  slug?: string;
  lecture_id: string | number;
  settings: string; 
}

const auth = useAuthStore()
const route = useRoute()

const loading = ref(true)
const error = ref<string | null>(null)
const action = ref<ActiveAction | null>(null)

const isSaving = ref(false)
const isEditing = ref(false)

// Парсимо налаштування безпечно
const actionSettings = computed(() => {
  if (!action.value?.settings) return {};
  try {
    return JSON.parse(action.value.settings);
  } catch (e) {
    console.error("Помилка парсингу JSON:", e);
    return {};
  }
});

// Визначаємо фінальний тип активності (з поля type або з settings)
const currentType = computed(() => {
  console.log('Поточні налаштування активності:', action); // Додайте цей рядок для перевірки налаштувань
  return action.value?.type || actionSettings.value.type;
});

const getActionDetails = async (id: number | string) => {
  try {
    loading.value = true
    const data = await ActionsAPI.getOne(id)
    action.value = data
  } catch (e) {
    error.value = 'Помилка завантаження'
    console.error(e)
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  if (!action.value) return
  
  try {
    isSaving.value = true
    
    // Синхронізуємо action.type з JSON всередині settings перед збереженням, 
    // якщо ваша логіка базується на JSON
    const settingsObj = actionSettings.value;
    settingsObj.type = action.value.type;
    action.value.settings = JSON.stringify(settingsObj);

    await ActionsAPI.update(action.value.id, action.value)
    isEditing.value = false
  } catch (e) {
    error.value = 'Не вдалося зберегти зміни'
  } finally {
    isSaving.value = false
  }
}

onMounted(() => {
  const id = route.params.id
  if (id) {
    getActionDetails(id as string)
  } else {
    error.value = 'ID активності не знайдено'
    loading.value = false
  }
})

</script>

<template>
  <div class="action-details">
    <div v-if="loading" class="status">Завантаження...</div>
    
    <div v-else-if="error" class="error-msg">
      Помилка: {{ error }}
    </div> 

    <div v-else-if="action">
      <div class="header-actions">
        <h1>{{ isEditing ? 'Редагування активності' : (action.title || 'Деталі активності') }}</h1>
        
        <div v-if="auth.token">
          <button v-if="!isEditing" @click="isEditing = true" class="btn btn-outline">
            ✏️ Редагувати
          </button>
          <button v-else @click="isEditing = false" class="btn btn-secondary">
            Скасувати
          </button>
        </div>
      </div>

      <form v-if="isEditing" @submit.prevent="handleSave" class="edit-form">
        <div class="form-group">
          <label>Назва активності:</label>
          <input v-model="action.title" type="text" class="form-control" />
        </div>

        <div class="form-group">
          <label>Slug (URL сегмент):</label>
          <input v-model="action.slug" type="text" class="form-control" />
        </div>

        <div class="form-group">
          <label>Тип активності:</label>
          <select v-model="action.type" class="form-control">
            <option value="lecture">Лекція</option>
            <option value="test">Тест</option>
          </select>
        </div>

        <button type="submit" :disabled="isSaving" class="btn btn-primary">
          {{ isSaving ? 'Збереження...' : 'Зберегти зміни' }}
        </button>
      </form>
    
      <div v-if="!isEditing" class="content-view">
        <LectureView 
          v-if="currentType === 'lecture'"
          :slug="action.slug || ''" 
          :topic_name="action.title || 'Активність без назви'" 
          :markdown="action.content"
          :lecture_id="+action.lecture_id"
        />
          
        <SelfTest 
          v-else-if="currentType === 'test'"
          :slug="action.slug || ''" 
          :topic_name="action.title || 'Активність без назви'" 
          :markdown="action.content"
          :lecture_id="+action.lecture_id"
        />

        <QuizGame 
          v-else-if="currentType === 'kahoot'"
          :slug="action.slug || ''" 
          :topic_name="action.title || 'Активність без назви'" 
          :markdown="action.content"
          :lecture_id="+action.lecture_id"
        />

        <DuneGame 
          v-else-if="currentType === 'dune'"
          :lecture_id="+action.lecture_id"
        />
        
        <div v-else class="status">
          Невідомий тип активності: {{ currentType }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Ваші стилі залишаються без змін */
.error-msg { color: red; }
.status { font-style: italic; padding: 20px; }
.action-details { padding: 80px 20px 20px; max-width: 1200px; margin: 0 auto; }
.header-actions { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.btn { padding: 10px 20px; cursor: pointer; border-radius: 4px; border: 1px solid #ccc; }
.btn-primary { background-color: #007bff; color: white; border: none; }
.btn-outline { background: transparent; border: 1px solid #007bff; color: #007bff; }
.edit-form { display: flex; flex-direction: column; gap: 1.5rem; background: #f9f9f9; padding: 2rem; border-radius: 8px; margin-bottom: 30px; }
.form-group { display: flex; flex-direction: column; gap: 0.5rem; }
.form-control { padding: 0.8rem; border: 1px solid #ccc; border-radius: 4px; font-size: 1rem; }
</style>