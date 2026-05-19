<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { io, Socket } from 'socket.io-client'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 1. Інтерфейси
interface Player {
  id: string;
  nickname: string;
  score: number;
}

interface Question {
  text: string;
  options: string[];
  correct: string;
  isFinished?: boolean;
}

const props = defineProps<{
  slug: string,
  topic_name?: string, 
  markdown: string 
  lecture_id: number
}>()

const auth = useAuthStore()
const router = useRouter()

// ФУНКЦІЯ НАЗАД
const goBack = () => router.back()

// --- Стан гри ---
//const socket: Socket = io('//81.163.127.86:3000')

const socket: Socket = io('https://api.ocsnau.net/') // Змінити на реальний URL сервера
const gameState = ref<'lobby' | 'waiting' | 'playing' | 'finished'>('lobby')
const role = ref<'none' | 'host' | 'player'>('none')
const roomCode = ref('')
const players = ref<Player[]>([])

// --- Стан гравця ---
const nickname = ref((auth as any).user?.name || '')
const roomInput = ref('')
const hasAnswered = ref(false)
const selectedAnswer = ref('')

// --- Стан хоста ---
const markdownInput = ref(props.markdown || '')
const parsedQuestions = ref<Question[]>([])
const currentQuestionIndex = ref(0)
const currentQuestion = ref<Question | null>(null)

// --- Таймер ---
const timeLeft = ref(20)
const timerMax = 20 // Максимальний час для смуги таймера
let timerInterval: ReturnType<typeof setInterval> | null = null

// Обчислюємо ширину прогрес-бару
const timerProgress = computed(() => (timeLeft.value / timerMax) * 100)

const startLocalTimer = () => {
  stopLocalTimer()
  timeLeft.value = timerMax
  timerInterval = setInterval(() => {
    if (timeLeft.value > 0) {
      timeLeft.value--
    } else {
      stopLocalTimer()
      hasAnswered.value = true
    }
  }, 1000)
}

const stopLocalTimer = () => {
  if (timerInterval !== null) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

// Якщо сервер надсилає час — це основне джерело правди
let serverWatchdog: ReturnType<typeof setTimeout> | null = null

socket.on('timer_update', (time: number) => {
  timeLeft.value = time

  // Сервер живий — зупиняємо локальний таймер
  stopLocalTimer()

  // Watchdog: якщо сервер мовчить >2с — запускаємо локальний як резерв
  if (serverWatchdog) clearTimeout(serverWatchdog)
  serverWatchdog = setTimeout(() => {
    if (timeLeft.value > 0) startLocalTimer()
  }, 2000)
})

socket.on('time_up', () => {
  stopLocalTimer()
  if (serverWatchdog) clearTimeout(serverWatchdog)
  hasAnswered.value = true
})

// --- Обробка подій Socket.IO ---
socket.on('room_created', (code: string) => {
  roomCode.value = code
  gameState.value = 'waiting'
})

socket.on('players_update', (updatedPlayers: Player[]) => {
  players.value = updatedPlayers
})

socket.on('question', (questionData: Question) => {
  if (questionData && questionData.isFinished) {
    stopLocalTimer()
    nextQuestion()
    gameState.value = 'finished'
  } else {
    currentQuestion.value = questionData
    hasAnswered.value = false
    selectedAnswer.value = ''
    if (gameState.value !== 'playing') gameState.value = 'playing'
    startLocalTimer()
  }
})

// --- Дії ---
const createRoom = () => {
  role.value = 'host'
  socket.emit('create_room', { name: 'Host' })
}

const joinRoom = () => {
  role.value = 'player'
  roomCode.value = roomInput.value
  socket.emit('join_room', { roomCode: roomCode.value, nickname: nickname.value })
  gameState.value = 'waiting'
}

const parseMarkdown = (text: string): Question[] => {
  if (!text) return []
  const blocks = text.trim().split(/\n\s*\n/)
  
  return blocks.map((block: string) => {
    const lines = block.split('\n')
    const questionText = (lines[0] || '').replace(/^#+\s*/, '').trim()
    const options: string[] = []
    let correct = ''
    
    for (let i = 1; i < lines.length; i++) {
      const line = (lines[i] || '').trim()
      if (!line) continue

      if (line.startsWith('- [x]') || line.startsWith('* [x]')) {
        const opt = line.replace(/^[-*]\s*\[x\]\s*/i, '')
        options.push(opt)
        correct = opt
      } else if (line.startsWith('- [ ]') || line.startsWith('* [ ]')) {
        const opt = line.replace(/^[-*]\s*\[ \]\s*/, '')
        options.push(opt)
      }
    }
    return { text: questionText, options, correct }
  }).filter((q: Question) => q.options.length > 0 && q.text)
}

const startGame = () => {
  parsedQuestions.value = parseMarkdown(markdownInput.value)
  if (parsedQuestions.value.length === 0) return alert('Не вдалося знайти питання.')
  currentQuestionIndex.value = 0
  gameState.value = 'playing'
  sendCurrentQuestion()
  startLocalTimer()
}

const sendCurrentQuestion = () => {
  currentQuestion.value = parsedQuestions.value[currentQuestionIndex.value] || null
  socket.emit('new_question', { roomCode: roomCode.value, question: currentQuestion.value })
}

const nextQuestion = () => {
  currentQuestionIndex.value++
  if (currentQuestionIndex.value < parsedQuestions.value.length) {
    sendCurrentQuestion()
    startLocalTimer()
  } else {
    stopLocalTimer()
    socket.emit('new_question', { 
      roomCode: roomCode.value, 
      question: { isFinished: true, text: '', options: [], correct: '' } 
    })
    gameState.value = 'finished'
  }
}

const submitAnswer = (answerText: string) => {
  if (hasAnswered.value) return
  hasAnswered.value = true
  selectedAnswer.value = answerText
  socket.emit('answer', { roomCode: roomCode.value, answer: answerText })
}

const resetGame = () => {
  stopLocalTimer()
  if (serverWatchdog) clearTimeout(serverWatchdog)
  gameState.value = 'lobby'
  role.value = 'none'
  roomCode.value = ''
  hasAnswered.value = false
}

const sortedPlayers = computed(() => {
  return [...players.value].sort((a, b) => b.score - a.score)
})

onUnmounted(() => {
  stopLocalTimer()
  if (serverWatchdog) clearTimeout(serverWatchdog)
  socket.disconnect()
})
</script>

<template>
  <div class="kahoot-container">
    <div class="lecture-header">
      <button @click="goBack" class="btn-back">🔙 Назад</button>
      <router-link 
        v-if="auth.token && props.lecture_id" 
        :to="{ name: 'edit-lecture', params: { slug: props.lecture_id.toString() } }" 
        class="btn-edit"
      >
        ✏️ Редагувати
      </router-link>
    </div>

    <div v-if="gameState === 'lobby'" class="lobby">
      <h2>Вікторина</h2>
      
      <div class="panel">
        <h3>Я гравець</h3>
        <input v-model="nickname" placeholder="Твоє ім'я" />
        <input v-model="roomInput" placeholder="Код кімнати" />
        <button @click="joinRoom" :disabled="!nickname || !roomInput">Приєднатись</button>
      </div>

      <div class="divider" v-if="auth.token">--- АБО ---</div>

      <div class="panel" v-if="auth.token">
        <h3>Я ведучий (Хост)</h3>
        <button @click="createRoom">Створити нову кімнату</button>
      </div>
    </div>

    <div v-if="gameState === 'waiting'" class="waiting-room">
      <div v-if="role === 'host'">
        <h2>Кімната створена! Код: <span class="highlight">{{ roomCode }}</span></h2>
        <p>Гравців приєдналося: {{ players.length }}</p>
        <ul>
          <li v-for="player in players" :key="player.id">{{ player.nickname }}</li>
        </ul>

        <div class="markdown-editor">
          <h3>Введіть питання у форматі Markdown:</h3>
          <p class="hint">Використовуйте - [ ] для неправильних і - [x] для правильної відповіді.</p>
          <textarea v-model="markdownInput" rows="10" placeholder="# Який колір неба?&#10;- [ ] Зелений&#10;- [x] Синій&#10;- [ ] Червоний"></textarea>
          <button @click="startGame" :disabled="players.length === 0 || !markdownInput">Почати гру</button>
        </div>
      </div>

      <div v-else>
        <h2>Очікуємо ведучого...</h2>
        <p>Ви в кімнаті: {{ roomCode }}. Ваш нік: {{ nickname }}</p>
        <p>Підключені гравці:</p>
        <ul>
          <li v-for="player in players" :key="player.id">{{ player.nickname }}</li>
        </ul>
      </div>
    </div>

    <div v-if="gameState === 'playing'" class="gameplay">
      <div class="timer-wrapper">
        <div class="timer-bar" :style="{ width: timerProgress + '%' }"></div>
        <span class="timer-text">{{ timeLeft }}с</span>
      </div>

      <div v-if="role === 'host' && currentQuestion">
        <h2>Питання {{ currentQuestionIndex + 1 }} з {{ parsedQuestions.length }}</h2>
        <h3>{{ currentQuestion.text }}</h3>
        <ul>
          <li v-for="(opt, i) in currentQuestion.options" :key="i" :class="{ correct: opt === currentQuestion.correct }">
            {{ opt }}
          </li>
        </ul>
        <button @click="nextQuestion">Наступне питання</button>
      </div>

      <div v-else-if="currentQuestion">
        <h2>{{ currentQuestion.text }}</h2>
        <div class="options-grid">
          <button 
            v-for="(opt, i) in currentQuestion.options" 
            :key="i"
            @click="submitAnswer(opt)"
            :disabled="hasAnswered || timeLeft <= 0"
            :class="{ answered: hasAnswered, selected: selectedAnswer === opt }"
          >
            {{ opt }}
          </button>
        </div>
        <p v-if="timeLeft <= 0 && !hasAnswered" class="status-message out-of-time">Час вичерпано! ⏱️</p>
        <p v-if="hasAnswered" class="status-message">Відповідь прийнято!</p>
      </div>
    </div>
    
    <div v-if="gameState === 'finished'" class="finished">
      <h2>Гру завершено!</h2>
      <h3>Фінальна таблиця результатів:</h3>
      <table class="leaderboard-table">
        <thead>
          <tr>
            <th>Місце</th>
            <th>Гравець</th>
            <th>Бали</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(player, index) in sortedPlayers" :key="player.id">
            <td>{{ index + 1 }}</td>
            <td>{{ player.nickname }}</td>
            <td>{{ player.score }}</td>
          </tr>
        </tbody>
      </table>
      <button @click="resetGame" style="margin-top: 20px;">Повернутись в головне меню</button>
    </div>
  </div>
</template>

<style scoped>
.kahoot-container {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  text-align: center;
}

.lecture-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.panel {
  background: #f4f4f4;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.divider {
  margin: 20px 0;
  color: #888;
}

input, textarea {
  width: 100%;
  padding: 10px;
  margin: 10px 0;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}

button {
  background-color: #4CAF50;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  width: 100%;
  margin-top: 10px;
}

button:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
}

.btn-back {
  background-color: #607D8B;
  width: auto;
}

.btn-edit {
  background-color: #FF9800;
  color: white;
  padding: 10px 20px;
  text-decoration: none;
  border-radius: 4px;
  display: inline-block;
}

.highlight {
  color: #e91e63;
  font-weight: bold;
}

/* Стилі таймера */
.timer-wrapper {
  width: 100%;
  height: 24px;
  background-color: #eee;
  border-radius: 12px;
  margin-bottom: 25px;
  position: relative;
  overflow: hidden;
  border: 2px solid #ddd;
}

.timer-bar {
  height: 100%;
  background: linear-gradient(90deg, #ff9800, #f44336);
  transition: width 1s linear;
}

.timer-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-weight: bold;
  font-size: 14px;
  color: #333;
  text-shadow: 0 0 2px white;
}

/* Сітка питань */
.options-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-top: 20px;
}

.options-grid button {
  padding: 30px;
  font-size: 18px;
  background-color: #2196F3;
}

.options-grid button.answered {
  opacity: 0.6;
}

.options-grid button.selected {
  border: 4px solid #ff9800;
  opacity: 1;
}

.correct {
  color: #4CAF50;
  font-weight: bold;
}

/* Таблиця лідерів */
.leaderboard-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.leaderboard-table th, .leaderboard-table td {
  border: 1px solid #ddd;
  padding: 12px;
}

.leaderboard-table th {
  background-color: #f2f2f2;
}

.hint {
  font-size: 0.9em;
  color: #666;
}

.status-message {
  margin-top: 20px;
  font-size: 1.2em;
  color: #4CAF50;
  font-weight: bold;
}

.out-of-time {
  color: #f44336 !important;
}
</style>