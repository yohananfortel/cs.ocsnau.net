<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router' 
import PresentationEdit from './PresentationEdit.vue';

const props = defineProps<{ slug: string }>() // Типізація пропсів
const auth = useAuthStore()
const router = useRouter()

interface Lecture {
  topic_name: string;
  markdown: string;
  lecture_id?: number;
}

const loading = ref(true)
const saveStatus = ref('Збережено') // 'Збереження...', 'Збережено', 'Помилка'
let debounceTimer: ReturnType<typeof setTimeout>
const lecture = ref<Lecture>({ topic_name: '', markdown: '' });
const error = ref<string | null>(null);


// 1. Завантаження початкових даних
const fetchLecture = async () => {

  console.log('Завантаження лекції з ID:', props.slug);
  try {
    const url = `https://cs.ocsnau.net/nxrfzzjm_server/lecture.php?id=${props.slug}`;
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Помилка мережі')
    
    const data = await response.json()

    lecture.value = data
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Невідома помилка';
  } finally {
    loading.value = false
  }
}

// 2. Функція збереження на сервер
const saveToServer = async () => {
  saveStatus.value = 'Збереження...'
  try {
    const res = await fetch('https://cs.ocsnau.net/nxrfzzjm_server/update_lecture.php', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${auth.token}`
      },
      body: JSON.stringify({
        id: props.slug,
        topic_name: lecture.value.topic_name,
        markdown: lecture.value.markdown
      })
    })


    if (res.ok) {
      saveStatus.value = 'Збережено' 
    } else {
      saveStatus.value = `Помилка збереження: ${res.status}`
    }
  } catch (err) {
    saveStatus.value = 'Помилка мережі'
  }
}

// 3. Слідкуємо за змінами (Автозбереження)
watch(() => lecture.value.markdown, () => {
  saveStatus.value = 'Очікування...'
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    saveToServer()
  }, 2000) // Зберегти через 2 секунди після останньої зміни
})

onMounted(fetchLecture)


// Посилання на прихований input
const fileInput = ref<HTMLInputElement | null>(null)

// Функція, яка "клікає" по прихованому інпуту
const triggerFileInput = () => {
  fileInput.value?.click()
}

// Функція, яка спрацьовує, коли користувач обрав файл
const handleFileUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) return

  // Створюємо об'єкт FormData для відправки файлу
  const formData = new FormData()
  formData.append('image', file)
  formData.append('lecture_id', props.slug) // Додаємо ID лекції, щоб сервер знав, куди зберігати картинку

  try {
    // Відправляємо запит на ваш PHP-скрипт (вкажіть правильний шлях!)
    const response = await fetch('https://cs.ocsnau.net/nxrfzzjm_server/upload.php', {
      method: 'POST',
      body: formData
    })

    const data = await response.json()



    if (data.success) {

      console.log('Відповідь сервера:', data);
      // Створюємо Markdown-розмітку для картинки
      // У Reveal.js можна додати класи для розміру, але почнемо з базового
      const markdownImage = `\n![Опис картинки](${data.url})\n`
      
      // Додаємо картинку в текст лекції
      lecture.value.markdown += markdownImage
      
      // Очищаємо інпут, щоб можна було завантажити той самий файл ще раз, якщо треба
      target.value = ''


    } else {
      alert('Помилка завантаження: ' + data.error)
    }
  } catch (error) {
    console.error('Помилка запиту:', error)
    alert('Не вдалося з\'єднатися з сервером для завантаження картинки.')
  }
}


</script>

<template>
  <div class="edit-page">
    <header class="edit-header">
      <button @click="router.back()" class="btn-back">←</button>
      <input v-model="lecture.topic_name" class="title-input" placeholder="Назва лекції" />


      <h3 v-if="error" class="error-msg">{{ props.slug}}</h3>
      <span class="status-badge" :class="saveStatus">{{ saveStatus }}</span>
    </header>
    <div class="edit-header">
      <button @click="triggerFileInput" class="btn-upload"> 🖼️ Додати картинку</button>
    </div>

    <div v-if="loading" class="loading-screen">Завантаження редактора...</div>

    <div v-else class="editor-split-container">
      <div class="editor-toolbar"> 
        <input 
          type="file" 
          ref="fileInput" 
          @change="handleFileUpload" 
          accept="image/*" 
          style="display: none;" 
        />
      </div>

      <div class="editor-pane">
        <textarea class="markdown-editor"
          v-model="lecture.markdown" 
          placeholder="Пишіть Markdown тут..."
          spellcheck="false"
        ></textarea>
      </div>

      <div class="preview-pane">
        
            <PresentationEdit :lectureContent="lecture.markdown" />
        
      </div>
    </div>
  </div>
</template>

<style scoped>
.edit-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 90vw;
  padding-top: 100px;
 /* Враховуючи ваш фіксований хедер, якщо він є */
}

.edit-header {
  display: flex;
  align-items: center;
  padding: 10px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #ddd;
  gap: 15px;
}

.title-input {
  flex-grow: 1;
  font-size: 1.2rem;
  font-weight: bold;
  border: 1px transparent;
  padding: 5px;
  background: transparent;
}

.title-input:focus {
  border-bottom: 1px solid #42b983;
  outline: none;
}

.status-badge {
  font-size: 0.8rem;
  padding: 4px 10px;
  border-radius: 12px;
}
.status-badge.Збережено { background: #e2f5ea; color: #28a745; }
.status-badge.Збереження... { background: #fff3cd; color: #856404; }

.editor-split-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.editor-pane, .preview-pane {
  flex: 1;
  height: 100%;
  overflow-y: auto;
}

.editor-pane textarea {
  width: 100%;
  height: 100%;
  border: none;
  padding: 20px;
  font-family: 'Fira Code', monospace;
  font-size: 14px;
  resize: none;
  outline: none;
  background: #fafafa;
  line-height: 1.6;
}

.preview-pane {
  border-left: 2px solid #eee;
  background: white;
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

/* Приховуємо скролбари для чистоти, якщо потрібно */
textarea::-webkit-scrollbar { width: 8px; }
textarea::-webkit-scrollbar-thumb { background: #ddd; border-radius: 4px; }
</style>