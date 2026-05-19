<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { VueFlow, useVueFlow, Handle, Position } from '@vue-flow/core'
import type { Node, Edge } from '@vue-flow/core' // Використовуємо Node | Edge замість Elements
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls' 
import { addEdge } from '@vue-flow/core'
import router from '@/router'

import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router' 

import { KnowlegeMapAPI } from '@/api/knowlegemap'

// Стилі бібліотеки
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

const { fitView } = useVueFlow()

const elements = ref<(Node | Edge)[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const auth = useAuthStore()

const loadKnowledgeMap = async () => {  
  loading.value = true
  try {
    const data = await KnowlegeMapAPI.getAll()
    
    elements.value = data.map((el: any) => {
      // Якщо це вузол (не має source/target), додаємо йому тип 'custom'
      if (!el.source && !el.target) {
        return {
          ...el,
          type: 'custom',
          // Конвертуємо в числа, щоб уникнути збоїв рендеру, якщо з БД прийдуть рядки
          position: el.position || { 
            x: parseFloat(el.position_x) || 0, 
            y: parseFloat(el.position_y) || 0 
          }
        }
      }
      return el
    })

    await nextTick()
    setTimeout(() => { fitView() }, 50) 
  } catch (err) {
    error.value = (err as Error).message
  } finally {
    loading.value = false
  }
}

const goToLecture = (id: string | number) => {
  //console.log('Перехід до лекції:', id)
  router.push(`/action/${id}`)
}

const onNodeDragStop = async ({ node }: { node: any }) => {


  if(auth.token) {
    try {

      const data = await KnowlegeMapAPI.updatePosition(node.id, {
        x: node.position.x,
        y: node.position.y
      });

      console.log('Позиція :', node.position.x, node.position.y);

      console.log('Оновлена позиція з БД:', data.text);

      console.log(`Позицію лекції ${node.id} збережено`);
    } catch (err) {
      console.error("Не вдалося зберегти позицію", err);
    }
  }

}

const onConnect = async (params: any) => {
  if(auth.token) {
  // 1. Візуально додаємо зв'язок у граф відразу
  elements.value = addEdge({ ...params, animated: true }, elements.value)

  try {
    // 2. Відправляємо запит на бекенд для збереження в БД
    await KnowlegeMapAPI.createRelation({
      source: params.source,
      target: params.target
    });
    console.log(`Зв'язок між ${params.source} та ${params.target} створено`);
  } catch (err) {
    console.error("Помилка збереження зв'язку", err);
    // Тут варто додати логіку видалення стрілочки, якщо запит впав
  }
  }
}

onMounted(() => {
  loadKnowledgeMap()
})
</script>

<template>
  <div class="flow-container">
    <div v-if="loading" class="overlay">Завантаження...</div>
    <div v-if="error" class="error-msg">{{ error }}</div>

    <VueFlow 
      v-model="elements" 
      :fit-view-on-init="true"
      class="knowledge-map"
      @node-drag-stop="onNodeDragStop"
      @connect="onConnect"
    >
      <Background pattern-color="#e0e0e0" :gap="20" />
      <Controls />
      
      <template #node-custom="{ id, data, label }">
        <div class="lecture-card">
          <Handle type="target" :position="Position.Top" />
          
          <div class="card-header">{{ label }}</div>
          <div class="card-body">
            <strong>{{ label }}</strong>
            <p v-if="data?.description">{{ data.description }}</p>
          </div>
          <div class="card-footer">
            <button class="read-btn" @click="goToLecture(id)">Перейти</button>
          </div>

          <Handle type="source" :position="Position.Bottom" />
        </div>
      </template>
    </VueFlow>
  </div>
</template>

<style scoped>
.flow-container {
  height: 600px;
  width: 100%;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  background-color: #f9f9f9;
  position: relative; /* Додано для позиціонування overlay */
}

.overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
  font-weight: bold;
}

.error-msg {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  background: #ff4d4f;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  z-index: 10;
}

.lecture-card {
  background: white;
  border: 2px solid #42b983;
  border-radius: 8px;
  padding: 0;
  min-width: 180px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  font-family: sans-serif;
}

.card-header {
  background: #42b983;
  color: white;
  padding: 4px 8px;
  font-size: 10px;
  text-transform: uppercase;
  font-weight: bold;
}

.card-body {
  padding: 10px;
}

.card-body p {
  margin: 5px 0 0;
  font-size: 12px;
  color: #666;
}

.card-footer {
  border-top: 1px solid #eee;
  padding: 8px;
  text-align: right;
}

.read-btn {
  background: #42b983;
  color: white;
  border: none;
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.2s;
}

.read-btn:hover {
  background: #9ee0c2;
}

:deep(.vue-flow__edge-path) {
  stroke: #b1b1b7;
  stroke-width: 2;
}

:deep(.vue-flow__edge-text) {
  font-size: 10px;
  fill: #888;
}
</style>