<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const props = defineProps<{
  slug: string,
  topic_name?: string, 
  markdown: string 
  lecture_id: number
}>()

const goBack = () => router.back()

// Стан тесту
const currentQuestionIndex = ref(0)
const selectedAnswer = ref<number | null>(null)
const score = ref(0)
const isFinished = ref(false)

// Парсинг Markdown у структуровані дані
const questions = computed(() => {
  if (!props.markdown) return []
  
  // Розбиваємо за заголовками третєого рівня ###
  const rawQuestions = props.markdown.split('###').filter(q => q.trim())
  
  return rawQuestions.map(q => {
    const lines = q.trim().split('\n')
    const questionText = lines[0]?.trim() || 'Питання без тексту'
    
    const options = lines
      .filter(line => line.trim().startsWith('-') || line.trim().startsWith('*'))
      .map(line => {
        // Визначаємо правильність: містить [x] або закінчується на !
        const isCorrect = line.includes('[x]') || line.trim().endsWith('!')
        // Очищаємо текст від маркерів списку та позначок правильності
        const text = line
          .replace(/^[-*]\s*/, '')   // видаляємо маркер списку
          .replace(/\[x\]|\[\s\]/g, '') // видаляємо [x] або [ ]
          .replace(/!$/, '')          // видаляємо знак оклику в кінці
          .trim()
        
        return { text, isCorrect }
      })

    return { questionText, options }
  })
})

const currentQuestion = computed(() => {
  return questions.value.length > 0 ? questions.value[currentQuestionIndex.value] : null
})

const submitAnswer = () => {
  if (selectedAnswer.value === null || !currentQuestion.value) return

 // Створюємо безпечне посилання на обрану відповідь
  const option = currentQuestion.value.options[selectedAnswer.value]

  // Перевіряємо, чи існує option, перш ніж читати isCorrect
  if (option?.isCorrect) {
    score.value++
  }

  if (currentQuestionIndex.value < questions.value.length - 1) {
    currentQuestionIndex.value++
    selectedAnswer.value = null
  } else {
    isFinished.value = true
  }
}

const restart = () => {
  currentQuestionIndex.value = 0
  selectedAnswer.value = null
  score.value = 0
  isFinished.value = false
}
</script>

<template>
  <div class="test-container">
    <div class="lecture-header">
      <button @click="goBack" class="btn-back">← Назад</button>
      <h2>{{ topic_name || `Лекція ${slug}` }}</h2>
      
      <router-link 
       v-if="auth.token && props.lecture_id" 
    :to="{ name: 'edit-lecture', params: { slug: props.lecture_id } }" 
    class="btn-edit"
      >
        ✏️ Редагувати
      </router-link>
    </div>

    <hr />

    <div v-if="!isFinished && currentQuestion" class="test-content">
      <div class="progress">Питання {{ currentQuestionIndex + 1 }} з {{ questions.length }}</div>
      
      <h3 class="question-text">{{ currentQuestion.questionText }}</h3>

      <div class="options">
        <label 
          v-for="(opt, idx) in currentQuestion.options" 
          :key="idx" 
          :class="{ 'option-item': true, active: selectedAnswer === idx }"
        >
          <input 
            type="radio" 
            :value="idx" 
            v-model="selectedAnswer" 
            class="hidden-radio"
          />
          <span class="option-marker">{{ String.fromCharCode(65 + idx) }}.</span>
          <span class="option-text">{{ opt.text }}</span>
        </label>
      </div>

      <button 
        class="btn-next" 
        @click="submitAnswer" 
        :disabled="selectedAnswer === null"
      >
        {{ currentQuestionIndex === questions.length - 1 ? 'Завершити' : 'Далі' }}
      </button>
    </div>

    <div v-else-if="isFinished" class="result">
      <h2>Тест завершено! 🎉</h2>
      <div class="score-board">
        <span class="final-score">{{ score }} / {{ questions.length }}</span>
        <p>Ваш результат: {{ Math.round((score / questions.length) * 100) }}%</p>
      </div>
      <button class="btn-restart" @click="restart">Спробувати знову</button>
    </div>

    <div v-else class="status">
      Питання завантажуються або відсутні...
    </div>
  </div>
</template>

<style scoped>
.test-container {
  max-width: 700px;
  margin: 20px auto;
  padding: 30px;
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}

.lecture-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.btn-back { background: none; border: none; color: #666; cursor: pointer; font-size: 1rem; }
.btn-edit { text-decoration: none; color: #2196f3; font-weight: bold; }

.question-text {
  font-size: 1.4rem;
  margin: 20px 0;
  color: #2c3e50;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 25px 0;
}

.option-item {
  display: flex;
  align-items: center;
  padding: 15px;
  border: 2px solid #edf2f7;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.option-item:hover {
  background: #f7fafc;
  border-color: #cbd5e0;
}

.option-item.active {
  background: #ebf8ff;
  border-color: #4299e1;
}

.hidden-radio {
  display: none;
}

.option-marker {
  font-weight: bold;
  margin-right: 15px;
  color: #4299e1;
}

.btn-next, .btn-restart {
  width: 100%;
  padding: 15px;
  background: #48bb78;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 1.1rem;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-next:disabled {
  background: #cbd5e0;
  cursor: not-allowed;
}

.btn-next:hover:not(:disabled) {
  background: #38a169;
}

.result {
  text-align: center;
  padding: 40px 0;
}

.score-board {
  margin: 30px 0;
}

.final-score {
  font-size: 3rem;
  font-weight: bold;
  color: #2b6cb0;
}
</style>