
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked' // Упевніться, що marked встановлено: npm i marked

// === СТАН ===
const screen = ref('lobby') // 'lobby', 'game', 'teacher', 'victory'
const teacherTab = ref('stats')

// Налаштування лобі
const config = ref({
  mode: 'classic',
  fogOfWar: false,
  surroundRule: false,
  attackMode: false,
  players: [
    { id: 1, name: 'Гравець 1', color: '#00d4ff', avatar: '😎' },
    { id: 2, name: 'Гравець 2', color: '#ff3355', avatar: '🤖' }
  ]
})

// Стан гри
const players = ref([])
const board = ref([])
const currentPlayerIdx = ref(0)
const gameTimeLeft = ref(900) // 15 хвилин
let gameTimer = null

const currentPlayer = computed(() => players.value[currentPlayerIdx.value])
const sortedPlayers = computed(() => [...players.value].sort((a, b) => b.score - a.score))
const modeLabel = computed(() => {
  return config.value.mode === 'blitz' ? 'БЛІЦ' : config.value.mode === 'team' ? 'КОМАНДНИЙ' : 'КЛАСИКА'
})

// Стан модального вікна питань
const showQuestion = ref(false)
const activeQuestion = ref(null)
const questionTimeLeft = ref(30)
let questionTimer = null
const parsedQuestion = computed(() => activeQuestion.value ? marked(activeQuestion.value.text) : '')

const answerRevealed = ref(false)
const selectedAnswer = ref(null)
const openAnswerText = ref('')
const lastAnswerCorrect = ref(false)
const lastPointsEarned = ref(0)
const lastPenaltyText = ref('')

const notifications = ref([])
const questions = ref([
  { id: 1, type: 'mc', cellTypeName: 'Звичайна', cellIcon: '🟩', difficulty: 1, text: 'Скільки буде 2+2?', options: ['3', '4', '5', '6'], correct: 1, timeLimit: 30 }
  // Додайте інші питання за потребою
])

const availableColors = ['#00d4ff', '#ff3355', '#00ff88', '#ffd700', '#7c3aed', '#ff6b35']

// === МЕТОДИ ЛОБІ ===
const cycleColor = (idx) => {
  const currentColor = config.value.players[idx].color
  const colorIdx = availableColors.indexOf(currentColor)
  config.value.players[idx].color = availableColors[(colorIdx + 1) % availableColors.length]
}
const addPlayer = () => {
  if (config.value.players.length < 6) {
    const id = config.value.players.length + 1
    config.value.players.push({ id, name: `Гравець ${id}`, color: availableColors[id % availableColors.length], avatar: '👤' })
  }
}
const removePlayer = (idx) => {
  if (config.value.players.length > 2) {
    config.value.players.splice(idx, 1)
  }
}

// === МЕТОДИ ГРИ ===
const startGame = () => {
  // Ініціалізація гравців
  players.value = config.value.players.map(p => ({
    ...p,
    score: 0,
    combo: 0,
    cells: 0
  }))
  
  // Генерація поля (20x20 для прикладу)
  board.value = Array.from({ length: 400 }, (_, i) => ({
    id: i,
    owner: null,
    locked: false,
    blocked: Math.random() < 0.05, // 5% блоків
    justCaptured: false
  }))
  
  currentPlayerIdx.value = 0
  gameTimeLeft.value = config.value.mode === 'blitz' ? 420 : 900
  
  screen.value = 'game'
  startTimer()
}

const endGame = () => {
  clearInterval(gameTimer)
  screen.value = 'victory'
}

const startTimer = () => {
  clearInterval(gameTimer)
  gameTimer = setInterval(() => {
    gameTimeLeft.value--
    if (gameTimeLeft.value <= 0) endGame()
  }, 1000)
}

const formatTime = (seconds) => {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0')
  const s = (seconds % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

// Логіка сітки
const canClickCell = (cell) => !cell.blocked && !cell.locked
const isFogCell = (cell, idx) => false // Спрощена логіка туману війни для прикладу
const cellStyle = (cell) => {
  if (cell.owner) return { backgroundColor: `${getPlayerColor(cell.owner)}20` }
  return {}
}
const cellIcon = (cell) => {
  if (cell.blocked) return '🔒'
  return ''
}
const getPlayerColor = (id) => players.value.find(p => p.id === id)?.color || '#fff'

const clickCell = (cell, idx) => {
  if (!canClickCell(cell) && !config.value.attackMode) return
  if (cell.owner === currentPlayer.value.id) return
  
  // Виклик питання
  activeQuestion.value = questions.value[Math.floor(Math.random() * questions.value.length)]
  showQuestion.value = true
  questionTimeLeft.value = activeQuestion.value.timeLimit
  answerRevealed.value = false
  selectedAnswer.value = null
  openAnswerText.value = ''
  
  clearInterval(questionTimer)
  questionTimer = setInterval(() => {
    questionTimeLeft.value--
    if (questionTimeLeft.value <= 0) {
      submitAnswer(-1) // Тайм-аут
    }
  }, 1000)
}

// === МЕТОДИ ПИТАНЬ ===
const submitAnswer = (answer) => {
  if (answerRevealed.value) return
  clearInterval(questionTimer)
  selectedAnswer.value = answer
  
  const isCorrect = answer === activeQuestion.value.correct
  lastAnswerCorrect.value = isCorrect
  answerRevealed.value = true
  
  if (isCorrect) {
    currentPlayer.value.combo++
    lastPointsEarned.value = 1 * (currentPlayer.value.combo >= 3 ? 2 : 1) // Множник комбо
    currentPlayer.value.score += lastPointsEarned.value
    currentPlayer.value.cells++
  } else {
    currentPlayer.value.combo = 0
    lastPenaltyText.value = 'Хід переходить іншому гравцю!'
  }
}

const submitOpenAnswer = () => {
  // Для відкритих питань (спрощена логіка)
  submitAnswer(openAnswerText.value.trim().toLowerCase())
}

const closeQuestion = () => {
  showQuestion.value = false
  if (!lastAnswerCorrect.value) {
    // Перехід ходу
    currentPlayerIdx.value = (currentPlayerIdx.value + 1) % players.value.length
  }
}

const notify = (text) => {
  const id = Date.now()
  notifications.value.push({ id, text })
  setTimeout(() => {
    notifications.value = notifications.value.filter(n => n.id !== id)
  }, 3000)
}

onUnmounted(() => {
  clearInterval(gameTimer)
  clearInterval(questionTimer)
})
</script>

<template>
  <div id="app-container">
    <!-- ===== LOBBY ===== -->
    <div id="lobby" class="screen" :class="{active: screen === 'lobby'}">
      <div class="logo">TerritoryQuest</div>
      <div class="logo-sub">Освітня Гра Захоплення Територій</div>
      <div class="lobby-card">
        <h2>🎮 Налаштування Гри</h2>
        <div class="field-group">
          <label>Режим Гри</label>
          <select v-model="config.mode">
            <option value="classic">⚔️ Класичний (15 хв)</option>
            <option value="blitz">⚡ Бліц (7 хв)</option>
            <option value="team">👥 Командний</option>
          </select>
        </div>
        <div class="field-group">
          <label>Опції</label>
          <div style="display:flex;gap:20px;flex-wrap:wrap">
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;color:var(--text2);font-size:0.85rem">
              <input type="checkbox" v-model="config.fogOfWar" style="accent-color:var(--accent)"> 👁️ Туман Війни
            </label>
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;color:var(--text2);font-size:0.85rem">
              <input type="checkbox" v-model="config.surroundRule" style="accent-color:var(--accent)"> ⭕ Оточення (Go)
            </label>
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;color:var(--text2);font-size:0.85rem">
              <input type="checkbox" v-model="config.attackMode" style="accent-color:var(--accent)"> ⚔️ Атака чужих
            </label>
          </div>
        </div>
        <div class="field-group">
          <label>Гравці</label>
          <div class="player-list">
            <div class="player-entry" v-for="(p, i) in config.players" :key="i">
              <input v-model="p.name" :placeholder="'Гравець ' + (i+1)" />
              <div class="color-dot" :style="{background: p.color}" @click="cycleColor(i)"></div>
              <button class="btn btn-danger" v-if="config.players.length > 2" @click="removePlayer(i)">✕</button>
            </div>
          </div>
          <button class="btn btn-sm" @click="addPlayer" v-if="config.players.length < 6">+ Додати гравця</button>
        </div>
        <button class="btn btn-primary" @click="startGame">🚀 ПОЧАТИ ГРУ</button>
        <button class="btn btn-teacher btn-sm" @click="screen='teacher'">🧑‍🏫 Панель Викладача</button>
      </div>
    </div>

    <!-- ===== GAME ===== -->
    <div id="game" class="screen" :class="{active: screen === 'game'}">
      <div class="game-header">
        <div class="game-title">TERRITORY<span style="color:var(--accent2)">QUEST</span></div>
        <div class="player-scores">
          <div class="score-badge" v-for="(p, i) in players" :key="i"
               :class="{'active-turn': currentPlayerIdx === i}"
               :style="{borderColor: currentPlayerIdx === i ? p.color : 'var(--border)'}">
            <div class="score-dot" :style="{background: p.color}"></div>
            <span class="score-name">{{ p.name }}</span>
            <span class="score-val">{{ p.score }}</span>
            <span class="combo-badge" v-if="p.combo >= 3">🔥×{{ p.combo }}</span>
          </div>
        </div>
        <div class="timer-display" :class="{urgent: gameTimeLeft < 60}">
          <span>⏱</span>
          <span>{{ formatTime(gameTimeLeft) }}</span>
        </div>
        <button class="btn btn-sm" @click="endGame">🏁 Завершити</button>
      </div>
      <div class="game-body">
        <div class="sidebar">
          <div>
            <h3>Поточний Хід</h3>
            <div class="turn-indicator" :style="{borderColor: currentPlayer?.color}">
              <div style="font-size:1.5rem">{{ currentPlayer?.avatar }}</div>
              <div class="turn-name" :style="{color: currentPlayer?.color}">{{ currentPlayer?.name }}</div>
              <div style="font-size:0.75rem;color:var(--text2);margin-top:4px">
                {{ config.attackMode ? 'Клік на будь-яку клітинку' : 'Клік на доступну клітинку' }}
              </div>
            </div>
          </div>
          <div>
            <h3 style="margin-bottom:10px">Легенда</h3>
            <div class="legend-item"><span class="legend-icon">🟩</span> Звичайна (+1)</div>
            <div class="legend-item"><span class="legend-icon">💎</span> Бонусна (+3)</div>
            <div class="legend-item"><span class="legend-icon">💣</span> Пастка (ризик)</div>
            <div class="legend-item"><span class="legend-icon">🔒</span> Заблокована</div>
            <div class="legend-item"><span class="legend-icon">⚡</span> Швидка (×2)</div>
          </div>
          <div>
            <h3 style="margin-bottom:10px">Режим</h3>
            <div class="mode-tag">{{ modeLabel }}</div>
            <div v-if="config.fogOfWar" class="mode-tag" style="margin-top:6px;color:var(--text2)">👁️ ТУМАН</div>
            <div v-if="config.surroundRule" class="mode-tag" style="margin-top:6px;color:var(--accent3)">⭕ ОТО- ЧЕННЯ</div>
          </div>
        </div>

        <div class="board-container">
          <div class="grid">
            <div v-for="(cell, idx) in board" :key="idx"
                 class="cell"
                 :class="[
                   cell.owner ? 'owned' : (cell.blocked ? 'blocked' : 'neutral'),
                   cell.locked ? 'locked' : '',
                   (!canClickCell(cell) && !config.attackMode) ? 'disabled' : '',
                   config.fogOfWar && isFogCell(cell, idx) ? 'fog-cell' : '',
                   cell.justCaptured ? 'just-captured' : '',
                 ]"
                 :style="cellStyle(cell)"
                 @click="clickCell(cell, idx)">
              {{ cellIcon(cell) }}
              <div v-if="cell.owner && !cell.locked" class="cell-owner-ring"
                   :style="{boxShadow: 'inset 0 0 0 2px ' + getPlayerColor(cell.owner) + '60'}">
              </div>
              <div v-if="config.attackMode && cell.owner && cell.owner !== currentPlayer?.id" class="attack-indicator"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== QUESTION MODAL ===== -->
    <teleport to="body">
      <div class="modal-overlay" v-if="showQuestion" @click.self="closeQuestion">
        <div class="modal" style="position:relative">
          <div class="modal-header">
            <div class="cell-type-badge">
              <span class="cell-type-icon">{{ activeQuestion?.cellIcon }}</span>
              <div>
                <div style="font-size:0.9rem;font-weight:600">{{ activeQuestion?.cellTypeName }}</div>
                <div style="color:var(--text2);font-size:0.75rem">Складність: {{ '★'.repeat(activeQuestion?.difficulty || 1) }}</div>
              </div>
            </div>
            <div style="text-align:right">
              <div class="timer-ring" :class="{urgent: questionTimeLeft < 5}">
                <svg width="36" height="36" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" r="15.9"/>
                  <circle class="progress" cx="18" cy="18" r="15.9"
                    :stroke-dasharray="'100 100'"
                    :stroke-dashoffset="100 - (questionTimeLeft / (activeQuestion?.timeLimit || 30) * 100)"
                    stroke-width="3"/>
                </svg>
              </div>
              <div style="font-family:'Orbitron',monospace;font-size:0.9rem;margin-top:4px"
                   :style="{color: questionTimeLeft < 5 ? 'var(--red)' : 'var(--yellow)'}">
                {{ questionTimeLeft }}с
              </div>
            </div>
          </div>

          <div class="modal-timer">
            <div class="modal-timer-fill"
                 :class="{warning: questionTimeLeft / (activeQuestion?.timeLimit || 30) < 0.5, danger: questionTimeLeft / (activeQuestion?.timeLimit || 30) < 0.25}"
                 :style="{width: (questionTimeLeft / (activeQuestion?.timeLimit || 30) * 100) + '%'}"></div>
          </div>

          <div class="question-text" v-html="parsedQuestion"></div>

          <!-- Multiple choice -->
          <div class="options" v-if="activeQuestion?.type === 'mc'">
            <button class="option-btn" v-for="(opt, oi) in activeQuestion.options" :key="oi"
                    :class="{
                      correct: answerRevealed && oi === activeQuestion.correct,
                      wrong: answerRevealed && selectedAnswer === oi && oi !== activeQuestion.correct,
                      selected: selectedAnswer === oi && !answerRevealed
                    }"
                    :disabled="answerRevealed"
                    @click="submitAnswer(oi)">
              <span class="option-key">{{ String.fromCharCode(65+oi) }}</span>
              <span>{{ opt }}</span>
            </button>
          </div>

          <!-- True/False -->
          <div class="tf-options" v-if="activeQuestion?.type === 'tf'">
            <button class="tf-btn true-btn" :disabled="answerRevealed"
                    :class="{correct: answerRevealed && activeQuestion.correct===true, wrong: answerRevealed && selectedAnswer===true && activeQuestion.correct!==true}"
                    @click="submitAnswer(true)">✅ ПРАВДА</button>
            <button class="tf-btn false-btn" :disabled="answerRevealed"
                    :class="{correct: answerRevealed && activeQuestion.correct===false, wrong: answerRevealed && selectedAnswer===false && activeQuestion.correct!==false}"
                    @click="submitAnswer(false)">❌ НЕПРАВДА</button>
          </div>

          <!-- Open Answer -->
          <div class="open-answer" v-if="activeQuestion?.type === 'open'">
            <div class="field-group">
              <label>Ваша відповідь:</label>
              <textarea v-model="openAnswerText" :disabled="answerRevealed"
                        placeholder="Введіть відповідь..."></textarea>
            </div>
            <button class="btn btn-primary" v-if="!answerRevealed" @click="submitOpenAnswer"
                    style="margin-top:0">Підтвердити</button>
            <div v-if="answerRevealed" style="margin-top:12px;padding:12px;background:var(--bg3);border-radius:8px;font-size:0.85rem;color:var(--text2)">
              <strong style="color:var(--accent)">Правильна відповідь:</strong><br>{{ activeQuestion.answer }}
            </div>
          </div>

          <!-- Result overlay -->
          <div class="result-overlay" v-if="answerRevealed">
            <div class="result-icon">{{ lastAnswerCorrect ? '✅' : '❌' }}</div>
            <div class="result-text" :style="{color: lastAnswerCorrect ? 'var(--green)' : 'var(--red)'}">
              {{ lastAnswerCorrect ? 'ПРАВИЛЬНО!' : 'НЕПРАВИЛЬНО!' }}
            </div>
            <div class="result-points" v-if="lastAnswerCorrect">
              +{{ lastPointsEarned }} очків
              <span v-if="currentPlayer?.combo >= 3" style="color:var(--accent2)"> 🔥 КОМБО!</span>
            </div>
            <div class="result-points" v-else style="color:var(--red)">{{ lastPenaltyText }}</div>
            <button class="result-continue" @click="closeQuestion">ПРОДОВЖИТИ →</button>
          </div>
        </div>
      </div>

      <!-- NOTIFICATIONS -->
      <div class="notification" v-for="n in notifications" :key="n.id">{{ n.text }}</div>
    </teleport>

    <!-- ===== TEACHER (Дописано) ===== -->
    <div id="teacher" class="screen" :class="{active: screen === 'teacher'}">
      <div class="teacher-header">
        <div class="logo" style="font-size:1.8rem;margin-bottom:0">🧑‍🏫 Панель Викладача</div>
        <button class="btn btn-sm" @click="screen='lobby'">← Назад</button>
      </div>
      <div class="tabs">
        <div class="tab" :class="{active: teacherTab==='stats'}" @click="teacherTab='stats'">📊 Статистика</div>
        <div class="tab" :class="{active: teacherTab==='questions'}" @click="teacherTab='questions'">❓ Питання</div>
        <div class="tab" :class="{active: teacherTab==='add'}" @click="teacherTab='add'">➕ Додати</div>
      </div>

      <div v-if="teacherTab==='stats'">
        <div class="stats-grid">
          <div class="stat-card">
            <h4>Всього Питань</h4>
            <div class="stat-val">{{ questions.length }}</div>
            <div class="stat-sub">у базі</div>
          </div>
          <div class="stat-card">
            <h4>Типи Питань</h4>
            <div class="stat-val">3</div>
            <div class="stat-sub">MC / TF / Відкриті</div>
          </div>
          <div class="stat-card">
            <h4>Гравці</h4>
            <div class="stat-val">{{ config.players.length }}</div>
            <div class="stat-sub">зареєстровано</div>
          </div>
        </div>
      </div>
      
      <div v-if="teacherTab==='questions'" class="questions-list">
        <!-- Заглушка для списку питань -->
        <p style="color: var(--text2);">Тут відображається список ваших питань.</p>
      </div>

      <div v-if="teacherTab==='add'" class="add-question-form">
        <!-- Заглушка для форми додавання -->
        <p style="color: var(--text2);">Тут форма додавання нового питання.</p>
      </div>
    </div>

    <!-- ===== VICTORY SCREEN (Дописано) ===== -->
    <div id="victory" class="screen" :class="{active: screen === 'victory'}">
      <div class="victory-card">
        <div class="victory-trophy">🏆</div>
        <div class="victory-title">ГРУ ЗАВЕРШЕНО</div>
        <div class="victory-results">
          <div class="victory-row" v-for="(p, i) in sortedPlayers" :key="p.id">
            <div class="victory-rank">#{{ i + 1 }}</div>
            <div class="victory-name">{{ p.name }}</div>
            <div class="victory-score">{{ p.score }} очок</div>
          </div>
        </div>
        <button class="btn btn-primary" @click="screen = 'lobby'">ПОВЕРНУТИСЯ В ЛОБІ</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
:root {
  --bg: #080c14;
  --bg2: #0d1424;
  --bg3: #111c30;
  --panel: #0a1020;
  --border: #1e3a5f;
  --accent: #00d4ff;
  --accent2: #ff6b35;
  --accent3: #7c3aed;
  --green: #00ff88;
  --red: #ff3355;
  --yellow: #ffd700;
  --text: #c8d8f0;
  --text2: #7090b0;
  --glow: 0 0 20px rgba(0,212,255,0.4);
  --glow2: 0 0 20px rgba(255,107,53,0.4);
}


/* === SCREENS === */
.screen { display: none; min-height: 100vh; }
.screen.active { display: flex; flex-direction: column; }

/* LOBBY */
#lobby {
  align-items: center; justify-content: center;
  background: radial-gradient(ellipse at 20% 50%, #0d2040 0%, transparent 60%),
              radial-gradient(ellipse at 80% 20%, #1a0a2e 0%, transparent 50%),
              var(--bg);
  padding: 20px;
}
.logo {
  font-family: 'Orbitron', monospace;
  font-size: clamp(2rem, 5vw, 4rem);
  font-weight: 900;
  background: linear-gradient(135deg, var(--accent), var(--accent3), var(--accent2));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  text-align: center;
  text-shadow: none;
  filter: drop-shadow(0 0 30px rgba(0,212,255,0.5));
  letter-spacing: 4px;
  margin-bottom: 8px;
}
.logo-sub {
  text-align: center; color: var(--text2); font-size: 0.9rem;
  letter-spacing: 8px; text-transform: uppercase; margin-bottom: 50px;
}
.lobby-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 40px;
  width: 100%; max-width: 520px;
  box-shadow: 0 0 60px rgba(0,212,255,0.08);
}
.lobby-card h2 {
  font-family: 'Orbitron', monospace;
  font-size: 1rem; letter-spacing: 4px;
  color: var(--accent); text-transform: uppercase;
  margin-bottom: 24px;
}
.field-group { margin-bottom: 20px; }
.field-group label { display: block; font-size: 0.8rem; color: var(--text2); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px; }
.field-group input, .field-group select {
  width: 100%;
  background: var(--bg3); border: 1px solid var(--border);
  color: var(--text); font-family: 'Exo 2', sans-serif; font-size: 1rem;
  padding: 12px 16px; border-radius: 8px; outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.field-group input:focus, .field-group select:focus {
  border-color: var(--accent); box-shadow: var(--glow);
}
.player-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
.player-entry {
  display: flex; gap: 8px; align-items: center;
}
.player-entry input { flex: 1; }
.color-dot {
  width: 28px; height: 28px; border-radius: 50%; border: 2px solid var(--border);
  cursor: pointer; flex-shrink: 0;
}
.btn {
  font-family: 'Orbitron', monospace; font-size: 0.85rem;
  letter-spacing: 2px; text-transform: uppercase;
  padding: 14px 28px; border-radius: 8px; cursor: pointer;
  border: none; transition: all 0.2s;
}
.btn-primary {
  background: linear-gradient(135deg, var(--accent), var(--accent3));
  color: #42b983; width: 100%; margin-top: 8px;
  box-shadow: 0 4px 20px rgba(0,212,255,0.3);
}
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,212,255,0.5); }
.btn-sm {
  background: var(--bg3); border: 1px solid var(--border);
  color: var(--text2); font-size: 0.7rem; padding: 8px 14px;
}
.btn-sm:hover { border-color: var(--accent); color: var(--accent); }
.btn-danger { background: var(--bg3); border: 1px solid var(--red); color: var(--red); padding: 8px 12px; font-size: 0.75rem; border-radius: 6px; }
.btn-teacher {
  background: transparent; border: 1px solid var(--accent3);
  color: var(--accent3); width: 100%; margin-top: 12px;
}
.btn-teacher:hover { background: rgba(124,58,237,0.1); }

/* GAME SCREEN */
#game { flex-direction: column; height: 100vh; overflow: hidden; }
.game-header {
  margin-top: 174px;

  background: var(--panel);
  border-bottom: 1px solid var(--border);
  padding: 10px 20px;
  display: flex; align-items: center; gap: 20px;
  flex-shrink: 0;
}
.game-title {
  font-family: 'Orbitron', monospace; font-size: 0.9rem;
  letter-spacing: 3px; color: var(--accent);
}
.player-scores {
  display: flex; gap: 12px; flex: 1;
}
.score-badge {
  display: flex; align-items: center; gap: 8px;
  background: var(--bg3); border-radius: 8px;
  padding: 6px 14px; border: 1px solid var(--border);
  font-size: 0.85rem; position: relative; overflow: hidden;
}
.score-badge.active-turn::after {
  content: '';
  position: absolute; inset: 0;
  border-radius: 8px;
  box-shadow: inset 0 0 0 2px var(--accent);
  animation: pulse-border 1s ease-in-out infinite;
}
@keyframes pulse-border { 0%,100%{opacity:1} 50%{opacity:0.4} }
.score-dot { width: 12px; height: 12px; border-radius: 3px; }
.score-name { font-weight: 600; }
.score-val { font-family: 'Orbitron', monospace; font-size: 0.9rem; color: var(--yellow); }
.combo-badge {
  background: linear-gradient(135deg, #ff6b35, #ffd700);
  color: #000; border-radius: 4px; padding: 2px 6px;
  font-size: 0.65rem; font-weight: 700; letter-spacing: 1px;
}
.timer-display {
  font-family: 'Orbitron', monospace; font-size: 1.1rem;
  font-weight: 700; color: var(--yellow);
  display: flex; align-items: center; gap: 8px;
}
.timer-display.urgent { color: var(--red); animation: blink 0.5s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
.timer-ring {
  width: 36px; height: 36px;
  position: relative;
}
.timer-ring svg { transform: rotate(-90deg); }
.timer-ring circle {
  fill: none; stroke: var(--border); stroke-width: 3;
}
.timer-ring .progress {
  stroke: var(--yellow); stroke-linecap: round;
  transition: stroke-dashoffset 0.1s linear;
}
.timer-ring.urgent .progress { stroke: var(--red); }

.game-body {
  display: flex; flex: 1; overflow: hidden;
}
.sidebar {
  width: 220px; flex-shrink: 0;
  background: var(--panel);
  border-right: 1px solid var(--border);
  padding: 16px; overflow-y: auto;
  display: flex; flex-direction: column; gap: 12px;
}
.sidebar h3 {
  font-family: 'Orbitron', monospace; font-size: 0.7rem;
  letter-spacing: 3px; color: var(--text2); text-transform: uppercase;
}
.legend-item {
  display: flex; align-items: center; gap: 10px;
  font-size: 0.82rem; color: var(--text2);
}
.legend-icon { font-size: 1.1rem; }
.mode-tag {
  background: var(--bg3); border: 1px solid var(--border);
  border-radius: 6px; padding: 6px 10px;
  font-size: 0.75rem; color: var(--accent2);
  font-family: 'Orbitron', monospace; letter-spacing: 1px;
  text-align: center;
}
.turn-indicator {
  background: linear-gradient(135deg, rgba(0,212,255,0.1), rgba(124,58,237,0.1));
  border: 1px solid var(--accent);
  border-radius: 8px; padding: 10px;
  text-align: center; font-size: 0.85rem;
}
.turn-name { font-weight: 700; font-size: 1rem; }

.board-container {
  flex: 1; display: flex; align-items: center; justify-content: center;
  overflow: auto; padding: 10px;
  background: radial-gradient(ellipse at center, #0d1a2e 0%, var(--bg) 100%);
}
.grid {
  display: grid;
  grid-template-columns: repeat(20, 1fr);
  gap: 2px;
  padding: 4px;
  background: rgba(30,58,95,0.3);
  border-radius: 8px;
  border: 1px solid var(--border);
}
.cell {
  width: 34px; height: 34px;
  border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  position: relative;
  border: 1px solid rgb(0 165 63);;
  background: var(--bg3);
  user-select: none;
}
.cell:hover:not(.disabled) {
  transform: scale(1.15);
  z-index: 2;
  filter: brightness(1.4);
}
.cell.disabled { cursor: not-allowed; opacity: 0.6; }
.cell.locked {
  background: #1a1a2e !important;
  cursor: not-allowed;
}
.cell.neutral { background: var(--bg3); }
.cell.blocked {
  background: #2a0a0a !important;
  border-color: var(--red) !important;
}
.cell.just-captured {
  animation: capture-flash 0.5s ease-out;
}
@keyframes capture-flash {
  0% { transform: scale(1.3); filter: brightness(2); }
  100% { transform: scale(1); filter: brightness(1); }
}
.cell-owner-ring {
  position: absolute; inset: 1px; border-radius: 3px;
  pointer-events: none;
}

/* QUESTION MODAL */
.modal-overlay {
  position: fixed; inset: 0;
  background: #F4F4F4;
  display: flex; align-items: center; justify-content: center;
  z-index: 100; padding: 20px;
  backdrop-filter: blur(8px);
}
.modal {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 16px;
  width: 100%; max-width: 600px;
  max-height: 90vh; overflow-y: auto;
  padding: 32px;
  box-shadow: 0 0 80px rgba(0,212,255,0.15);
  animation: modal-in 0.25s ease-out;
}
@keyframes modal-in {
  from { transform: scale(0.9) translateY(20px); opacity: 0; }
  to { transform: scale(1) translateY(0); opacity: 1; }
}
.modal-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 20px;
}
.cell-type-badge {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.8rem; color: var(--text2);
}
.cell-type-icon { font-size: 1.5rem; }
.question-text {
  font-size: 1rem; line-height: 1.7;
  color: var(--text);
  padding: 20px; background: var(--bg3);
  border-radius: 10px; border-left: 3px solid var(--accent);
  margin-bottom: 24px;
}
.question-text h1,.question-text h2,.question-text h3 { color: var(--accent); margin-bottom: 8px; }
.question-text p { margin-bottom: 8px; }
.question-text code { background: rgba(0,212,255,0.1); padding: 2px 6px; border-radius: 4px; font-family: monospace; color: var(--accent); }
.question-text pre { background: var(--bg); padding: 12px; border-radius: 6px; overflow-x: auto; margin: 8px 0; }
.question-text strong { color: var(--yellow); }
.question-text em { color: var(--accent2); }
.question-text ul, .question-text ol { padding-left: 20px; margin-bottom: 8px; }
.options { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
.option-btn {
  background: var(--bg3); border: 1px solid var(--border);
  color: var(--text); font-family: 'Exo 2', sans-serif; font-size: 0.95rem;
  padding: 14px 18px; border-radius: 8px; cursor: pointer;
  text-align: left; transition: all 0.15s;
  display: flex; align-items: center; gap: 12px;
}
.option-btn:hover:not(:disabled) { border-color: var(--accent); background: rgba(0,212,255,0.08); transform: translateX(4px); }
.option-btn.correct { border-color: var(--green); background: rgba(0,255,136,0.1); color: var(--green); }
.option-btn.wrong { border-color: var(--red); background: rgba(255,51,85,0.1); color: var(--red); }
.option-btn.selected { border-color: var(--accent); }
.option-key {
  font-family: 'Orbitron', monospace; font-size: 0.75rem;
  background: var(--bg); border: 1px solid var(--border);
  border-radius: 4px; padding: 2px 7px; flex-shrink: 0;
}
.tf-options { display: flex; gap: 12px; margin-bottom: 20px; }
.tf-btn {
  flex: 1; padding: 20px; border-radius: 10px;
  font-family: 'Orbitron', monospace; font-size: 1rem; letter-spacing: 2px;
  cursor: pointer; border: 1px solid var(--border);
  background: var(--bg3); color: var(--text); transition: all 0.15s;
  text-align: center;
}
.tf-btn:hover:not(:disabled) { transform: translateY(-3px); }
.tf-btn.true-btn:hover:not(:disabled) { border-color: var(--green); color: var(--green); box-shadow: 0 4px 20px rgba(0,255,136,0.2); }
.tf-btn.false-btn:hover:not(:disabled) { border-color: var(--red); color: var(--red); box-shadow: 0 4px 20px rgba(255,51,85,0.2); }
.open-answer { margin-bottom: 20px; }
.open-answer textarea {
  width: 100%; background: var(--bg3); border: 1px solid var(--border);
  color: var(--text); font-family: 'Exo 2', sans-serif; font-size: 0.95rem;
  padding: 14px; border-radius: 8px; resize: vertical; min-height: 100px;
  outline: none; transition: border-color 0.2s;
}
.open-answer textarea:focus { border-color: var(--accent); }
.modal-timer {
  width: 100%; height: 6px; background: var(--bg3);
  border-radius: 3px; overflow: hidden; margin-bottom: 16px;
}
.modal-timer-fill {
  height: 100%; border-radius: 3px;
  transition: width 0.1s linear, background 0.3s;
  background: linear-gradient(90deg, var(--green), var(--accent));
}
.modal-timer-fill.warning { background: linear-gradient(90deg, var(--accent2), var(--yellow)); }
.modal-timer-fill.danger { background: var(--red); }
.result-overlay {
  position: absolute; inset: 0; border-radius: 16px;
  display: flex; align-items: center; justify-content: center;
  flex-direction: column; gap: 12px;
  background: #e4e4e4;
  animation: result-in 0.3s ease-out;
  z-index: 10;
}
@keyframes result-in { from{opacity:0;transform:scale(0.8)} to{opacity:1;transform:scale(1)} }
.result-icon { font-size: 4rem; }
.result-text { font-family: 'Orbitron', monospace; font-size: 1.2rem; letter-spacing: 3px; }
.result-points { font-size: 0.9rem; color: var(--yellow); }
.result-continue {
  background: var(--accent); color: #000;
  font-family: 'Orbitron', monospace; font-size: 0.8rem;
  letter-spacing: 2px; padding: 10px 24px; border-radius: 6px;
  border: none; cursor: pointer; margin-top: 8px;
}

/* TEACHER PANEL */
#teacher {
  padding: 30px; background: var(--bg);
  flex-direction: column; gap: 20px;
}
.teacher-header {
  display: flex; justify-content: space-between; align-items: center;
}
.tabs {
  display: flex; gap: 4px; background: var(--bg3);
  padding: 4px; border-radius: 10px;
}
.tab {
  padding: 8px 20px; border-radius: 7px; cursor: pointer;
  font-family: 'Orbitron', monospace; font-size: 0.75rem;
  letter-spacing: 2px; text-transform: uppercase;
  color: var(--text2); transition: all 0.2s;
}
.tab.active { background: var(--accent3); color: #fff; }
.stats-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px;
}
.stat-card {
  background: var(--panel); border: 1px solid var(--border);
  border-radius: 12px; padding: 20px;
}
.stat-card h4 { font-size: 0.75rem; color: var(--text2); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px; }
.stat-val { font-family: 'Orbitron', monospace; font-size: 1.8rem; font-weight: 700; color: var(--accent); }
.stat-sub { font-size: 0.8rem; color: var(--text2); margin-top: 4px; }
.questions-list { display: flex; flex-direction: column; gap: 12px; }
.q-card {
  background: var(--panel); border: 1px solid var(--border);
  border-radius: 10px; padding: 16px; position: relative;
}
.q-card-header { display: flex; gap: 10px; align-items: center; margin-bottom: 10px; }
.q-type-badge {
  font-size: 0.7rem; letter-spacing: 1px; text-transform: uppercase;
  padding: 3px 8px; border-radius: 4px;
  background: rgba(0,212,255,0.1); color: var(--accent); border: 1px solid var(--accent);
}
.q-diff { font-size: 0.75rem; color: var(--text2); }
.q-text { font-size: 0.9rem; color: var(--text); margin-bottom: 8px; }
.q-actions { display: flex; gap: 8px; }
.add-question-form {
  background: var(--panel); border: 1px solid var(--border);
  border-radius: 12px; padding: 24px;
}
.add-question-form h3 {
  font-family: 'Orbitron', monospace; font-size: 0.85rem;
  letter-spacing: 3px; color: var(--accent); margin-bottom: 20px;
}
.form-row { display: flex; gap: 12px; }
.form-row .field-group { flex: 1; }
.field-group textarea {
  width: 100%; background: var(--bg3); border: 1px solid var(--border);
  color: var(--text); font-family: 'Exo 2', sans-serif; font-size: 0.9rem;
  padding: 12px 16px; border-radius: 8px; outline: none;
  resize: vertical; min-height: 80px;
}
.options-input { display: flex; flex-direction: column; gap: 8px; }
.option-input-row { display: flex; gap: 8px; align-items: center; }
.option-input-row input { flex: 1; }
.correct-radio { display: flex; align-items: center; gap: 6px; cursor: pointer; }
.correct-radio input[type="radio"] { accent-color: var(--green); }
.player-stat-row {
  display: flex; align-items: center; gap: 16px;
  background: var(--bg3); border-radius: 8px; padding: 12px 16px;
  margin-bottom: 8px;
}
.player-stat-bar {
  flex: 1; height: 8px; background: var(--bg);
  border-radius: 4px; overflow: hidden;
}
.player-stat-bar-fill { height: 100%; border-radius: 4px; }

/* VICTORY SCREEN */
#victory {
  align-items: center; justify-content: center;
  background: radial-gradient(ellipse at center, #0d2040 0%, var(--bg) 70%);
}
.victory-card {
  text-align: center; padding: 60px 40px;
  background: var(--panel); border: 1px solid var(--border);
  border-radius: 20px; max-width: 500px; width: 100%;
  box-shadow: 0 0 100px rgba(0,212,255,0.2);
}
.victory-trophy { font-size: 5rem; margin-bottom: 20px; animation: bounce 1s ease-in-out infinite; }
@keyframes bounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-15px)} }
.victory-title {
  font-family: 'Orbitron', monospace; font-size: 2rem; font-weight: 900;
  background: linear-gradient(135deg, var(--yellow), var(--accent2));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  margin-bottom: 8px;
}
.victory-results { margin: 30px 0; display: flex; flex-direction: column; gap: 10px; }
.victory-row {
  display: flex; align-items: center; gap: 14px;
  background: var(--bg3); border-radius: 8px; padding: 12px 16px;
}
.victory-rank {
  font-family: 'Orbitron', monospace; font-size: 1.2rem;
  width: 36px; text-align: center;
}
.victory-name { flex: 1; font-weight: 600; font-size: 1.1rem; }
.victory-score {
  font-family: 'Orbitron', monospace; color: var(--yellow); font-size: 1.1rem;
}

/* SCROLLBAR */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

.notification {
  position: fixed; top: 20px; right: 20px; z-index: 9998;
  background: var(--panel); border: 1px solid var(--accent);
  border-radius: 10px; padding: 14px 20px;
  font-size: 0.9rem; color: var(--accent);
  animation: notif-in 0.3s ease-out, notif-out 0.3s ease-in 2.7s forwards;
  max-width: 300px;
  box-shadow: var(--glow);
}
@keyframes notif-in { from{transform:translateX(100%);opacity:0} to{transform:translateX(0);opacity:1} }
@keyframes notif-out { from{opacity:1} to{opacity:0;transform:translateX(100%)} }

.fog-cell { filter: brightness(0.15) !important; pointer-events: none !important; }

.attack-indicator {
  position: absolute; inset: 0; border-radius: 4px;
  border: 2px solid var(--red);
  animation: attack-pulse 1s infinite;
  pointer-events: none;
}
@keyframes attack-pulse { 0%,100%{opacity:1} 50%{opacity:0.2} }

</style>