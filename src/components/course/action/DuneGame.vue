<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { io } from 'socket.io-client'
import { marked } from 'marked'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()


// === ПІДКЛЮЧЕННЯ ДО СЕРВЕРА ===
// Змініть URL на адресу вашого сервера (наприклад, ваш IP або домен)
const socket = io('http://localhost:3000')

// === ГЛОБАЛЬНИЙ СТАН (Синхронізується з сервером) ===
const gameState = ref({
  status: 'lobby', // 'lobby', 'game', 'victory'
  players: [],
  board: [],
  timeLeft: 900
})

// === ЛОКАЛЬНИЙ СТАН ГРАВЦЯ ===
const myPlayerId = ref(null)
const joinName = ref('')
const joinColor = ref('#00d4ff')
const availableColors = ['#00d4ff', '#ff3355', '#00ff88', '#ffd700', '#7c3aed', '#ff6b35']

// Кулдаун (штрафний час)
const cooldownTimer = ref(0)
let cooldownInterval = null

// Стан модального вікна питань
const showQuestion = ref(false)
const activeQuestion = ref(null)
const activeCellId = ref(null)
const questionTimeLeft = ref(30)
let questionTimer = null
const parsedQuestion = computed(() => activeQuestion.value ? marked(activeQuestion.value.text) : '')

const answerRevealed = ref(false)
const selectedAnswer = ref(null)
const lastAnswerCorrect = ref(false)

// База питань (в ідеалі теж має бути на сервері, але для простоти залишаємо тут)
const questions = ref([
  { id: 1, type: 'mc', text: 'Скільки буде **2+2**?', options: ['3', '4', '5', '6'], correct: 1, timeLimit: 15 },
  { id: 2, type: 'mc', text: 'Яка столиця України?', options: ['Львів', 'Київ', 'Одеса', 'Харків'], correct: 1, timeLimit: 15 },
  { id: 3, type: 'tf', text: 'Vue.js створений Еваном Ю?', correct: true, timeLimit: 10 }
])

// === ОБРОБКА ПОДІЙ СЕРВЕРА ===
onMounted(() => {
  socket.on('connect', () => {
    myPlayerId.value = socket.id
  })

  socket.on('syncState', (serverState) => {
    gameState.value = serverState
  })
})

onUnmounted(() => {
  socket.disconnect()
  clearInterval(questionTimer)
  clearInterval(cooldownInterval)
})

// Обчислювальні властивості
const myPlayer = computed(() => gameState.value.players.find(p => p.id === myPlayerId.value))
const sortedPlayers = computed(() => [...gameState.value.players].sort((a, b) => b.score - a.score))
const formatTime = (seconds) => {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0')
  const s = (seconds % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

// === МЕТОДИ ЛОБІ ===
const cycleColor = () => {
  const colorIdx = availableColors.indexOf(joinColor.value)
  joinColor.value = availableColors[(colorIdx + 1) % availableColors.length]
}

const joinGame = () => {
  if (joinName.value.trim().length > 0) {
    socket.emit('joinGame', joinName.value, joinColor.value)
  }
}

const startGame = () => {
  socket.emit('startGame')
}

// === МЕТОДИ ГРИ ===
const startCooldown = (seconds) => {
  cooldownTimer.value = seconds
  clearInterval(cooldownInterval)
  cooldownInterval = setInterval(() => {
    cooldownTimer.value--
    if (cooldownTimer.value <= 0) clearInterval(cooldownInterval)
  }, 1000)
}

const clickCell = (cell) => {
  // Перевірки перед кліком
  if (cooldownTimer.value > 0) return // Якщо під штрафом
  if (cell.blocked) return // Якщо клітинка заблокована
  if (cell.owner === myPlayerId.value) return // Якщо це вже наша клітинка
  if (!myPlayer.value) return // Якщо ми лише глядачі

  activeCellId.value = cell.id
  activeQuestion.value = questions.value[Math.floor(Math.random() * questions.value.length)]
  showQuestion.value = true
  questionTimeLeft.value = activeQuestion.value.timeLimit
  answerRevealed.value = false
  selectedAnswer.value = null

  clearInterval(questionTimer)
  questionTimer = setInterval(() => {
    questionTimeLeft.value--
    if (questionTimeLeft.value <= 0) {
      submitAnswer(-1) // Тайм-аут
    }
  }, 1000)
}

const submitAnswer = (answer) => {
  if (answerRevealed.value) return
  clearInterval(questionTimer)

  selectedAnswer.value = answer
  const isCorrect = answer === activeQuestion.value.correct
  lastAnswerCorrect.value = isCorrect
  answerRevealed.value = true

  // Відправляємо результат на сервер
  socket.emit('answerQuestion', {
    cellId: activeCellId.value,
    isCorrect: isCorrect
  })

  if (!isCorrect) {
    startCooldown(5) // 5 секунд штрафу за неправильну відповідь
  }

  // Закриваємо модалку через 1.5 секунди
  setTimeout(() => {
    showQuestion.value = false
  }, 1500)
}

const getPlayerColor = (id) => {
  const p = gameState.value.players.find(player => player.id === id)
  return p ? p.color : '#333'
}
</script>

<template>
  <div id="app-container">

    <!-- ===== ЛОБІ ===== -->
    <div id="lobby" class="screen" :class="{ active: gameState.status === 'lobby' }">
      <div class="logo">TerritoryQuest <span style="font-size: 0.5em; color: var(--accent2)">MMO</span></div>
      <div class="lobby-card">
        <h2>🎮 Підключення до сервера</h2>

        <div v-if="!myPlayer" class="field-group">
          <label>Ваше ім'я</label>
          <div style="display: flex; gap: 10px;">
            <input v-model="joinName" placeholder="Введіть нікнейм..." />
            <div class="color-dot" :style="{ background: joinColor }" @click="cycleColor"
              style="cursor:pointer; width: 40px; height: 40px; border-radius: 8px;"></div>
          </div>
          <button class="btn btn-primary" style="margin-top: 15px;" @click="joinGame">ПРИЄДНАТИСЯ</button>
        </div>

        <div v-else class="ready-state">
          <h3>Ви в лобі як: <span :style="{ color: myPlayer.color }">{{ myPlayer.name }}</span></h3>
          <p>Очікуємо інших гравців...</p>
        </div>

        <div class="field-group" style="margin-top: 30px;">
          <label>Гравці на сервері ({{ gameState.players.length }}/30)</label>
          <div class="player-list">
            <div class="player-entry" v-for="p in gameState.players" :key="p.id">
              <div class="color-dot" :style="{ background: p.color }"></div>
              <span>{{ p.name }}</span>
              <span v-if="p.id === myPlayerId" style="font-size: 0.8rem; color: var(--text2)">(Ви)</span>
            </div>
          </div>
        </div>

        <button v-if="myPlayer" class="btn btn-primary" @click="startGame">🚀 ПОЧАТИ ГРУ ДЛЯ ВСІХ</button>
      </div>
    </div>

    <!-- ===== ГРА ===== -->
    <div id="game" class="screen" :class="{ active: gameState.status === 'game' }">
      <div class="game-header">
        <div class="game-title">TERRITORY<span style="color:var(--accent2)">QUEST</span></div>
        <div class="timer-display" :class="{ urgent: gameState.timeLeft < 60 }">
          <span>⏱</span> <span>{{ formatTime(gameState.timeLeft) }}</span>
        </div>
      </div>

      <div class="game-body">
        <!-- ЛІВА ПАНЕЛЬ: Статистика та Топ Гравців -->
        <div class="sidebar">
          <div v-if="myPlayer" class="my-stats" :style="{ borderColor: myPlayer.color }">
            <h3>Мій профіль</h3>
            <div style="font-size: 1.2rem; font-weight: bold; color: white;">{{ myPlayer.name }}</div>
            <div>Очки: <span style="color: var(--accent)">{{ myPlayer.score }}</span></div>

            <!-- Індикатор кулдауну -->
            <div v-if="cooldownTimer > 0" class="cooldown-alert"
              style="margin-top: 10px; padding: 10px; background: var(--red); color: white; border-radius: 5px; text-align: center;">
              ⏳ ШТРАФ: {{ cooldownTimer }}с
            </div>

            



          </div>

          <div style="margin-top: 20px;">
            
            <div v-if="auth.token">
              <button v-if="myPlayer" class="btn btn-primary" @click="startGame">🚀 ПОЧАТИ ГРУ ДЛЯ ВСІХ</button>
            </div>

            <h3>🏆 Лідери</h3>
            <div v-for="(p, i) in sortedPlayers.slice(0, 5)" :key="p.id"
              style="display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border);">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 0.8rem; color: var(--text2);">#{{ i + 1 }}</span>
                <div class="score-dot"
                  :style="{ background: p.color, width: '12px', height: '12px', borderRadius: '50%' }"></div>
                <span style="font-size: 0.9rem;">{{ p.name }}</span>
              </div>
              <strong style="font-size: 0.9rem;">{{ p.score }}</strong>
            </div>
          </div>
        </div>

        <!-- ІГРОВЕ ПОЛЕ -->
        <div class="board-container">
          <!-- Використовуємо адаптивну сітку, що підлаштується під кількість клітинок -->
          <div class="grid"
            style="display: grid; grid-template-columns: repeat(auto-fill, minmax(30px, 1fr)); gap: 2px;">
            <!-- ОПТИМІЗАЦІЯ: v-memo дозволяє не перемальовувати клітинки, якщо їхній власник не змінився -->
            <div v-for="cell in gameState.board" :key="cell.id" v-memo="[cell.owner]" class="cell" :class="[
              cell.owner ? 'owned' : (cell.blocked ? 'blocked' : 'neutral'),
              cooldownTimer > 0 ? 'disabled' : ''
            ]" :style="{ backgroundColor: cell.owner ? getPlayerColor(cell.owner) + '40' : '' }"
              @click="clickCell(cell)">
              {{ cell.blocked ? '🔒' : '' }}
              <div v-if="cell.owner" class="cell-owner-ring"
                :style="{ boxShadow: 'inset 0 0 0 3px ' + getPlayerColor(cell.owner) }">
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== ВІКНО ПИТАННЯ ===== -->
    <teleport to="body">
      <div class="modal-overlay" v-if="showQuestion">
        <div class="modal" style="position:relative">
          <div class="modal-header">
            <div>Питання на захоплення</div>
            <div style="font-family:'Orbitron',monospace; font-size:1.2rem;"
              :style="{ color: questionTimeLeft < 5 ? 'var(--red)' : 'var(--yellow)' }">
              {{ questionTimeLeft }}с
            </div>
          </div>

          <div class="question-text" v-html="parsedQuestion"></div>

          <!-- Варіанти відповідей -->
          <div class="options" v-if="activeQuestion?.type === 'mc'">
            <button class="option-btn" v-for="(opt, oi) in activeQuestion.options" :key="oi" :class="{
              correct: answerRevealed && oi === activeQuestion.correct,
              wrong: answerRevealed && selectedAnswer === oi && oi !== activeQuestion.correct
            }" :disabled="answerRevealed" @click="submitAnswer(oi)">
              <span>{{ opt }}</span>
            </button>
          </div>

          <div class="tf-options" v-if="activeQuestion?.type === 'tf'">
            <button class="tf-btn true-btn" :disabled="answerRevealed"
              :class="{ correct: answerRevealed && activeQuestion.correct === true, wrong: answerRevealed && selectedAnswer === true && activeQuestion.correct !== true }"
              @click="submitAnswer(true)">✅ ПРАВДА</button>
            <button class="tf-btn false-btn" :disabled="answerRevealed"
              :class="{ correct: answerRevealed && activeQuestion.correct === false, wrong: answerRevealed && selectedAnswer === false && activeQuestion.correct !== false }"
              @click="submitAnswer(false)">❌ НЕПРАВДА</button>
          </div>

          <!-- Результат (відображається коротко перед закриттям) -->
          <div class="result-overlay" v-if="answerRevealed">
            <div class="result-icon">{{ lastAnswerCorrect ? '✅' : '❌' }}</div>
            <div class="result-text" :style="{ color: lastAnswerCorrect ? 'var(--green)' : 'var(--red)' }">
              {{ lastAnswerCorrect ? 'ТЕРИТОРІЯ ВАША!' : 'ПОМИЛКА! ШТРАФ 5 СЕК.' }}
            </div>
          </div>
        </div>
      </div>
    </teleport>

    <!-- ===== ЕКРАН ПЕРЕМОГИ ===== -->
    <div id="victory" class="screen" :class="{ active: gameState.status === 'victory' }">
      <div class="victory-card">
        <div class="victory-trophy" style="font-size: 4rem;">🏆</div>
        <div class="victory-title">ГРУ ЗАВЕРШЕНО</div>
        <div class="victory-results">
          <div class="victory-row" v-for="(p, i) in sortedPlayers.slice(0, 10)" :key="p.id"
            style="display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #444;">
            <div><strong style="color: var(--accent2)">#{{ i + 1 }}</strong> {{ p.name }}</div>
            <div><strong>{{ p.score }}</strong> очок</div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* Додайте сюди ваші існуючі стилі. Я залишив ключові структурні для MMO-версії */
#app-container {
  font-family: sans-serif;
  color: #fff;
  min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  margin-top: 100px;
}

.screen {
  display: none;
  padding: 20px;
}

.screen.active {
  display: block;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
}

.btn-primary {
  background: #00d4ff;
  color: #000;
}

.lobby-card,
.victory-card {
  max-width: 500px;
  margin: 0 auto;
  background: #1e1e1e;
  padding: 30px;
  border-radius: 12px;
}

.game-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: #1e1e1e;
  padding: 15px;
  border-radius: 8px;
}

.game-body {
  display: flex;
  gap: 20px;
  height: calc(100vh - 120px);
}

.sidebar {
  width: 250px;
  background: #1e1e1e;
  padding: 20px;
  border-radius: 8px;
  overflow-y: auto;
}

.board-container {
  flex-grow: 1;
  background: #1e1e1e;
  padding: 20px;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}

.cell {
  aspect-ratio: 1;
  background: #2a2a2a;
  border-radius: 4px;
  cursor: pointer;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: transform 0.1s;
}

.cell:hover:not(.disabled):not(.blocked) {
  transform: scale(1.1);
  z-index: 10;
  background: #444;
}

.cell.disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.cell.blocked {
  background: #111;
  cursor: not-allowed;
}

.cell-owner-ring {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 4px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 100;
}

.modal {
  background: #1e1e1e;
  padding: 30px;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 20px;
}

.option-btn,
.tf-btn {
  padding: 15px;
  background: #2a2a2a;
  border: 1px solid #444;
  color: #fff;
  border-radius: 8px;
  cursor: pointer;
}

.option-btn.correct,
.tf-btn.correct {
  background: #28a745;
  border-color: #28a745;
}

.option-btn.wrong,
.tf-btn.wrong {
  background: #dc3545;
  border-color: #dc3545;
}

.result-overlay {
  position: absolute;
  inset: 0;
  background: rgba(30, 30, 30, 0.95);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border-radius: 12px;
}

.result-icon {
  font-size: 4rem;
}

.grid {
  width: 100%;
}
</style>