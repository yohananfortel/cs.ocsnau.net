<template>
  <div class="app">
    <AppHeader :status-text="statusText" />

    <main class="layout">
      <section class="main">
        <ConnectScreen
          v-if="screen === 'connect'"
          v-model:name="name"
          :connected="connected"
          :error="error"
          @connect="connect"
        />

        <LobbyScreen
          v-else-if="screen === 'lobby'"
          :players="players"
          :min-players="minPlayers"
          :max-players="maxPlayers"
        />

        <WaitingScreen
          v-else-if="screen === 'between'"
          :message="serverMessage"
        />

        <QuestionScreen
          v-else-if="screen === 'question'"
          :question="question"
          :timer="timer"
          :answer-locked="answerLocked"
          :answer-message="answerMessage"
          :option-keys="optionKeys"
          @answer="sendAnswer"
        />

        <RoundResult
          v-else-if="screen === 'round'"
          :round="round"
        />

        <GameOver
          v-else-if="screen === 'over'"
          :winner="winner"
        />
      </section>

      <LeaderboardPanel :leaderboard="leaderboard" />
    </main>
  </div>
</template>

<script>
import AppHeader from "./components/AppHeader.vue";
import ConnectScreen from "./components/ConnectScreen.vue";
import LobbyScreen from "./components/LobbyScreen.vue";
import WaitingScreen from "./components/WaitingScreen.vue";
import QuestionScreen from "./components/QuestionScreen.vue";
import RoundResult from "./components/RoundResult.vue";
import GameOver from "./components/GameOver.vue";
import LeaderboardPanel from "./components/LeaderboardPanel.vue";

export default {
  name: "App",
  components: {
    AppHeader,
    ConnectScreen,
    LobbyScreen,
    WaitingScreen,
    QuestionScreen,
    RoundResult,
    GameOver,
    LeaderboardPanel,
  },
  data() {
    return {
      optionKeys: ["A", "B", "C", "D"],
      socket: null,
      connected: false,
      screen: "connect",
      statusText: "не підключено",
      name: "Гравець",
      error: "",
      players: [],
      leaderboard: [],
      minPlayers: 2,
      maxPlayers: 20,
      question: null,
      timer: 0,
      timerId: null,
      answerLocked: false,
      answerMessage: "",
      serverMessage: "",
      round: null,
      winner: null,
    };
  },
  methods: {
    connect() {
      if (!this.name || this.connected) return;

      this.error = "";
      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      const host = window.location.port === "5173"
        ? `${window.location.hostname}:5000`
        : window.location.host;
      const url = `${protocol}://${host}/ws`;

      this.socket = new WebSocket(url);
      this.statusText = "підключення...";

      this.socket.addEventListener("open", () => {
        this.connected = true;
        this.statusText = "підключено";
        this.send({ type: "join", name: this.name });
      });

      this.socket.addEventListener("message", (event) => {
        this.handleMessage(JSON.parse(event.data));
      });

      this.socket.addEventListener("close", () => {
        this.connected = false;
        if (this.screen !== "over") {
          this.statusText = "з'єднання закрито";
        }
      });

      this.socket.addEventListener("error", () => {
        this.error = "Не вдалося підключитися до Python-сервера.";
        this.statusText = "помилка";
      });
    },
    send(message) {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify(message));
      }
    },
    handleMessage(message) {
      if (message.type === "joined") {
        return;
      }
      if (message.type === "lobby") {
        this.screen = "lobby";
        this.players = message.players || [];
        this.leaderboard = this.players;
        this.minPlayers = message.min_players || 2;
        this.maxPlayers = message.max_players || 20;
      } else if (message.type === "game_started") {
        this.screen = "between";
        this.serverMessage = message.message || "Гра почалась!";
      } else if (message.type === "question") {
        this.showQuestion(message);
      } else if (message.type === "answer_received") {
        this.answerLocked = true;
        this.answerMessage = `Відповідь ${message.answer} прийнята.`;
      } else if (message.type === "round_result") {
        this.showRound(message);
      } else if (message.type === "game_over") {
        this.showGameOver(message);
      } else if (message.type === "error") {
        this.error = message.message || "Помилка.";
        alert(this.error);
      }
    },
    showQuestion(message) {
      this.screen = "question";
      this.question = message;
      this.leaderboard = message.scores || this.leaderboard;
      this.answerLocked = false;
      this.answerMessage = "Оберіть одну відповідь.";
      this.timer = message.round_seconds || 0;
      clearInterval(this.timerId);
      this.timerId = setInterval(() => {
        this.timer = Math.max(0, this.timer - 1);
        if (this.timer === 0) {
          clearInterval(this.timerId);
          if (!this.answerLocked) {
            this.answerMessage = "Час вийшов.";
          }
        }
      }, 1000);
    },
    sendAnswer(answer) {
      if (!this.question || this.answerLocked) return;
      this.answerLocked = true;
      this.answerMessage = `Надсилаю відповідь ${answer}...`;
      this.send({
        type: "answer",
        question_index: this.question.index,
        answer,
      });
    },
    showRound(message) {
      clearInterval(this.timerId);
      this.round = message;
      this.leaderboard = message.leaderboard || [];
      this.screen = "round";
    },
    showGameOver(message) {
      clearInterval(this.timerId);
      this.winner = message.winner;
      this.leaderboard = message.leaderboard || [];
      this.screen = "over";
      this.statusText = "гру завершено";
    },
  },
};
</script>
