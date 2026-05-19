<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ActionsAPI } from '@/api/actions'

const props = defineProps<{ slug: string }>()
const emit = defineEmits(['close','created'])

const topic = ref('')
const type = ref<number | null>(null)

interface ActionType {
  id: number
  name: string
}

const typesActions = ref<ActionType[]>([])

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

const getActions = async () => {
  try {
    typesActions.value = await ActionsAPI.getTypes()
  } catch (err) {
    console.error((err as Error).message)
  }
}

onMounted(() => {
  getActions()
})
</script>

<template>
<div class="modal">
  <div class="modal-content">

    <h3>Додати активність</h3>

    <input v-model="topic" placeholder="Назва активності">

  <select v-model="type">
      <option v-for="type in typesActions" :key="type.id" :value="type.id">
        {{ type.name }}
      </option>
   </select>

    <button @click="createAction">
      Зберегти
    </button>
    
    <button @click="$emit('close')">
      Закрити
    </button>

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

input {
  width: 100%;
  padding: 8px;
  margin: 10px 0;
  box-sizing: border-box;
}

button {
  padding: 8px 20px;
  margin: 5px auto;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: 0.3s;
  display: block;
}
button:hover {
  background-color: #3aa876;
}

</style>