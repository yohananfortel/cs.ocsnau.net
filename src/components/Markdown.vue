<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

const props = defineProps({
  lectureContent: {
    type: String,
    default: ''
  }
})

const htmlContent = computed(() => md.render(props.lectureContent))
</script>

<template>
  <div class="markdown-body" v-html="htmlContent"></div>
</template>

<style>
.markdown-body h1 { border-bottom: 1px solid #eee; }
.markdown-body code { background: #f4f4f4; padding: 2px 4px; }
.markdown-body img { max-width: 100%; }

.markdown-body hr { display: none;}

.markdown-body h1 { font-size: 2em; margin-top: 0.67em; margin-bottom: 0.67em; }
.markdown-body h2 { font-size: 1.5em; margin-top: 0.83em; margin-bottom: 0.83em; }
.markdown-body h3 { font-size: 1.25em; margin-top: 1em; margin-bottom: 1em; }
.markdown-body h4 { font-size: 1em; margin-top: 1.33em; margin-bottom: 1.33em; }
.markdown-body h5 { font-size: 0.875em; margin-top: 1.67em; margin-bottom: 1.67em; }
.markdown-body h6 { font-size: 0.75em; margin-top: 2.33em; margin-bottom: 2.33em; }
</style>