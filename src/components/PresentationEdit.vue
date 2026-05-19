<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import Reveal from 'reveal.js'
import Markdown from 'reveal.js/plugin/markdown/markdown.esm.js'
import Highlight from 'reveal.js/plugin/highlight/highlight.esm.js'
import MathPlugin from 'reveal.js/plugin/math/math.esm.js'
import mermaid from 'mermaid'

const props = defineProps<{ lectureContent: string }>()
const isVisual = ref(true)
const dynamicSlideTitle = ref('')
let deck: Reveal.Api | null = null

// Зберігаємо поточні індекси слайда
const lastIndices = ref({ h: 0, v: 0 })

// Оновлення заголовка та Mermaid
const updateHeaderTitle = (event: any) => {
  const { currentSlide, indexh, indexv } = event;
  if (!currentSlide) return;

  // Оновлюємо збережені індекси (прибрано дублювання)
  lastIndices.value = { h: indexh ?? 0, v: indexv ?? 0 };

  const h2 = currentSlide.querySelector('h2')
  dynamicSlideTitle.value = h2 ? h2.innerText : ""

  const mermaidElements = currentSlide.querySelectorAll('.mermaid')
  if (mermaidElements.length > 0) {
    // Очищуємо попередній рендер mermaid
    mermaidElements.forEach((el: any) => el.removeAttribute('data-processed'))
    
    // Використовуємо лише один сучасний метод рендеру (mermaid.run)
    mermaid.run({ nodes: mermaidElements }).catch((e) => console.error('Mermaid error:', e));
  }
}

const initReveal = async (h = 0, v = 0) => {
  await nextTick()
  
  mermaid.initialize({ 
    startOnLoad: false, 
    theme: 'base', 
    themeVariables: {
      primaryColor: '#e7f3ff',
      primaryTextColor: '#0056b3',
      lineColor: '#0056b3',
      fontSize: '18px'
    }
  })

  // Створюємо екземпляр
  deck = new Reveal({
    embedded: true, // Щоб не захоплював увесь екран
    hash: false,
    center: false,
    transition: 'slide',
    plugins: [Markdown, Highlight, MathPlugin]
  })

  // Створюємо Promise, який чекає на повну готовність Reveal та Markdown
  const revealReady = new Promise((resolve) => {
    deck?.on('ready', resolve)
  })

  // Ініціалізуємо
  await deck.initialize()
  await revealReady
  
  deck.slide(h, v, 0)

  // Підписуємось на події
  deck.on('slidechanged', updateHeaderTitle)
  
  // Даємо Markdown-плагіну кілька мілісекунд, щоб перетворити текст на HTML, 
  // інакше querySelector('h2') на першому слайді може нічого не знайти
  setTimeout(() => {
    updateHeaderTitle({ 
      currentSlide: deck?.getCurrentSlide(),
      indexh: h,
      indexv: v 
    })
  }, 50)
}

// "Hard Reset" при зміні контенту
watch(() => props.lectureContent, async () => {
  const currentPos = deck ? deck.getIndices() : { h: 0, v: 0 }

  isVisual.value = false 
  if (deck) {
    deck.destroy() // Важливо знищити старий екземпляр
  }
  
  await nextTick()
  isVisual.value = true 
  
  await nextTick()
  await initReveal(currentPos.h, currentPos.v)
})

onMounted(() => initReveal(0, 0))

onUnmounted(() => {
  if (deck) deck.destroy()
})

</script>

<template>
  <div class="presentation-wrapper">
    <h1 v-if="dynamicSlideTitle" class="dynamic-title">{{ dynamicSlideTitle }}</h1>

    <div v-if="isVisual" class="reveal">
      <div class="slides">
            <section 
          data-markdown 
          data-separator="^\n---\n$"
          data-separator-vertical="^\n--\n$"
        >
          <textarea data-template v-text="props.lectureContent"></textarea>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* scoped гарантує, що стилі не вилізуть за межі компонента */
@import 'reveal.js/dist/reveal.css';
@import 'reveal.js/dist/theme/white.css';

.presentation-wrapper {
  position: relative;
  width: 100%;
  height: 50vh; /* Має заповнювати preview-pane */
}

.dynamic-title {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 10;
  font-size: 28px;
  font-weight: bold;
  color: #fff; /* Змініть на чорний, якщо використовуєте світлу тему reveal */
  pointer-events: none; /* Щоб не заважав клікати по презентації */
  margin: 0;
}
</style>