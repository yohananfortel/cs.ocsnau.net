<script setup lang="ts">
// Імпортуємо інтерфейс, якщо він в окремому файлі, або залишаємо тут
interface Discipline {
  id: string | number;
  topic: string;
  slug: string;
}

// Оголошуємо пропси, щоб компонент знав, що він приймає дані
defineProps<{
  discipline: Discipline
}>()
</script>

<template>
  <div class="item">
    <i class="fa-solid fa-graduation-cap"></i>
    <div class="details">
      <h3>{{ discipline.topic }}</h3>
      <router-link :to="{ name: 'lectures', params: { slug: discipline.slug } }">
        Відкрити
      </router-link>
    </div>
  </div>
</template>