<template>
  <div>
    <h2 class="screen-title">Результат раунду</h2>
    <p class="hint">
      Правильна відповідь:
      <strong>{{ round.correct_answer }}</strong>. {{ round.correct_text }}
    </p>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Гравець</th>
          <th>Відповідь</th>
          <th>Бали</th>
          <th>Рахунок</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, index) in round.results" :key="row.name">
          <td>{{ index + 1 }}</td>
          <td>{{ row.name }}</td>
          <td :class="row.correct ? 'good' : 'bad'">{{ row.answer || "-" }}</td>
          <td>{{ row.points }}</td>
          <td>{{ row.score }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: "RoundResult",
  props: {
    round: {
      type: Object,
      required: true,
    },
  },
};
</script>
