<script setup lang="ts"> 
import { useAuthStore } from '@/stores/auth'
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router' 
import Presentation from './Presentation.vue'
import Markdown from './Markdown.vue'

const auth = useAuthStore()
const router = useRouter()

// 1. Оновлюємо типізацію пропсів, щоб прийняти markdown
const props = defineProps<{ 
  slug: string,
  topic_name?: string, 
  markdown: string 
  lecture_id: number
}>()

const goBack = () => router.back()
const viewMode = ref('markdown') 

// 2. Створюємо інтерфейс та реактивну змінну
interface Lecture {
  topic_name: string;
  markdown: string;
  lecture_id: number;
  slug: string;
}

const lecture = ref<Lecture>({
  topic_name: props.topic_name || `Лекція ${props.slug}`,
  markdown: props.markdown,
  slug: props.slug,
  lecture_id: props.lecture_id
})

watch(() => props.markdown, (newContent) => {
  lecture.value.markdown = newContent
})


console.log('LectureView props:', lecture)
 
</script>

<template>
  <div class="lecture">
        
    <div class="lecture-container">
      
        <div class="lecture-header">
          <button @click="goBack" class="btn-back">← Назад</button>
            <h2>{{ lecture.topic_name }}</h2>
            
            {{  lecture.lecture_id  }}

            <router-link 
    v-if="auth.token && lecture.lecture_id" 
    :to="{ name: 'edit-lecture', params: { slug: lecture.lecture_id } }" 
    class="btn-edit"
>
  <i class="fa-solid fa-pen-to-square"></i> Редагувати
</router-link>
        </div>

        <div class="controls">
            <button :class="{ active: viewMode === 'markdown' }" @click="viewMode = 'markdown'">Markdown</button>
            <button :class="{ active: viewMode === 'presentation' }" @click="viewMode = 'presentation'">Презентація</button>
        </div>

        <div class="content-viewer">
            <div v-if="viewMode === 'markdown'">  
                <Markdown :lectureContent="lecture.markdown" />
            </div>
            <div v-else-if="viewMode === 'presentation'">
                <Presentation :lectureContent="lecture.markdown" />
            </div>
        </div>
    </div>
  </div>
</template>

<style scoped>
/* Додаємо стилі для вирівнювання заголовка та кнопки */
.lecture{
    display: flex;
  flex-direction: column;
  height: 100vh;
  width: 90vw;
  max-width: 80%;
  padding-top: 100px;

}
.lecture-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;

  background: #f0f0f0;
}

button {
  padding: 8px 20px;
    background-color: #42b983;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    transition: 0.3s;
}

.active {
  background-color: #2c8e6b;
}



</style>