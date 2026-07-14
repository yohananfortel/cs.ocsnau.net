<template>
  <div>
    <div class="meta">
      <span>Питання {{ question.number }} з {{ question.total }}</span>
      <span class="timer">{{ timer }} с</span>
    </div>
    <h2 class="question">{{ question.question }}</h2>
    <div class="answers">
      <button
        v-for="key in optionKeys"
        :key="key"
        class="answer"
        :disabled="answerLocked || timer <= 0"
        @click="$emit('answer', key)"
      >
        <span class="answer-key">{{ key }}</span>
        <span>{{ question.options[key] }}</span>
      </button>
    </div>
    <p class="message">{{ answerMessage }}</p>
  </div>
</template>

<script>
export default {
  name: "QuestionScreen",
  props: {
    question: {
      type: Object,
      required: true,
    },
    timer: {
      type: Number,
      required: true,
    },
    answerLocked: {
      type: Boolean,
      required: true,
    },
    answerMessage: {
      type: String,
      required: true,
    },
    optionKeys: {
      type: Array,
      required: true,
    },
  },
  emits: ["answer"],
};
</script>
