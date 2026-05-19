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

// Оновлення заголовка та Mermaid
const updateHeaderTitle = (event: any) => {
  const currentSlide = event.currentSlide
  const h2 = currentSlide.querySelector('h2')
  dynamicSlideTitle.value = h2 ? h2.innerText : ""

  const mermaidElements = currentSlide.querySelectorAll('.mermaid')
  if (mermaidElements.length > 0) {
   // mermaidElements.forEach((el: Element) => el.removeAttribute('data-processed'))
   
   mermaidElements.forEach((el: any) => el.removeAttribute('data-processed'))
   mermaid.init(undefined, mermaidElements)
  }
}

const initReveal = async () => {
  await nextTick()
  
  mermaid.initialize({ 
    startOnLoad: false, 
    theme: 'base', 
    themeVariables: {
      primaryColor: '#e7f3ff',
      primaryTextColor: '#0056b3',
      lineColor: '#0056b3',
      fontSize: '14px'
    }
  })

  deck = new Reveal({
    embedded: true,
    hash: false,
    center: false, // Відключаємо автоцентрування по вертикалі, щоб контент був зверху
    transition: 'slide',
   // width: 960,
   // height: 700,
   // margin: 0.04,
    plugins: [Markdown, Highlight, MathPlugin]
  })

  await deck.initialize()
  
  deck.on('slidechanged', updateHeaderTitle)
  updateHeaderTitle({ currentSlide: deck.getCurrentSlide() })
}

// Перезавантаження при зміні тексту (автозбереження/редагування)
watch(() => props.lectureContent, async () => {
  isVisual.value = false 
  if (deck) {
    deck.destroy() 
  }
  
  await nextTick()
  isVisual.value = true 
  
  await nextTick()
  await initReveal()
})

onMounted(initReveal)

onUnmounted(() => {
  if (deck) deck.destroy()
})
</script>

<template>
  <div class="presentation-wrapper">
    <div id="dynamic-slide-title">{{ dynamicSlideTitle || 'Завантаження...' }}</div>
    
<div v-if="isVisual" class="reveal">
      <div class="slides">
        <section 
          data-markdown 
          data-separator="^\n---\n$"
          data-separator-vertical="^\n--\n$"
        >
          {{props.lectureContent}}
        </section>
      </div>
    </div>

  </div>
</template>

<style>
/* scoped гарантує, що стилі не вилізуть за межі компонента */
@import 'reveal.js/dist/reveal.css';
@import 'reveal.js/dist/theme/white.css';

.presentation-wrapper {
  position: relative;
  width: 100%;
  height: 80vh; /* Має заповнювати preview-pane */
 
}

      .reveal .slides section h2 {
            display: none;
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

#dynamic-slide-title{
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 20px;
  text-align: center;
}
.reveal section  {
    font-size: 0.7em; /* Sets font size for all paragraphs in a slide */
}
</style>