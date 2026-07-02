<template>
  <aside class="side">
    <h2 class="screen-title">Лідери</h2>
    <p v-if="leaderboard.length === 0" class="empty">Поки немає гравців.</p>
    <table v-else>
      <thead>
        <tr>
          <th>#</th>
          <th>Ім'я</th>
          <th>Бали</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, index) in leaderboard" :key="row.name">
          <td>{{ index + 1 }}</td>
          <td>{{ row.name }}</td>
          <td>{{ row.score }}</td>
        </tr>
      </tbody>
    </table>
  </aside>
</template>

<script>
export default {
  name: "LeaderboardPanel",
  props: {
    leaderboard: {
      type: Array,
      required: true,
    },
  },
};
</script>
