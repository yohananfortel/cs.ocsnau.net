import argparse
import base64
import hashlib
import json
import os
import random
import socket
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


OPTION_KEYS = ("A", "B", "C", "D")
BASE_POINTS = 100
MAX_SPEED_BONUS = 50
QUESTIONS_PER_GAME = 12
WEBSOCKET_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


@dataclass
class Player:
    player_id: str
    name: str
    handler: object
    address: tuple
    score: int = 0
    connected: bool = True
    answered_questions: set[int] = field(default_factory=set)


class QuizGame:
    def __init__(self, questions, max_players=20, min_players=2):
        self.questions = questions
        self.max_players = max_players
        self.min_players = min_players
        self.players = {}
        self.state = "lobby"
        self.lock = threading.RLock()
        self.game_thread = None
        self.round_questions = []
        self.current_question_index = -1
        self.current_deadline = 0.0
        self.current_round_seconds = 0
        self.current_answers = {}

    def add_player(self, handler, address, raw_name):
        name = str(raw_name).strip()[:24]
        if not name:
            handler.send_json({"type": "error", "message": "Введіть ім'я гравця."})
            return None

        with self.lock:
            if self.state != "lobby":
                handler.send_json({"type": "error", "message": "Гра вже почалась."})
                return None
            if len(self.players) >= self.max_players:
                handler.send_json({"type": "error", "message": "Сервер заповнений. Максимум 20 гравців."})
                return None
            if any(player.name.lower() == name.lower() for player in self.players.values()):
                handler.send_json({"type": "error", "message": "Таке ім'я вже зайняте."})
                return None

            player = Player(str(uuid.uuid4())[:8], name, handler, address)
            self.players[player.player_id] = player
            handler.send_json({
                "type": "joined",
                "player_id": player.player_id,
                "name": player.name,
                "max_players": self.max_players,
            })
            print(f"{player.name} joined from {address[0]}:{address[1]}")

        self.broadcast_lobby()
        return player

    def disconnect_player(self, player):
        with self.lock:
            existing = self.players.get(player.player_id)
            if existing is None:
                return
            existing.connected = False
            if self.state == "lobby":
                del self.players[player.player_id]
            print(f"{player.name} disconnected")
        if self.state == "lobby":
            self.broadcast_lobby()

    def start_game(self):
        with self.lock:
            if self.state != "lobby":
                print("Game is already running or finished.")
                return False
            if len(self.players) < self.min_players:
                print(f"Need at least {self.min_players} players to start. Current: {len(self.players)}")
                return False
            self.state = "running"
            self.game_thread = threading.Thread(target=self.run_game, daemon=True)
            self.game_thread.start()
            return True

    def run_game(self):
        question_count = min(QUESTIONS_PER_GAME, len(self.questions))
        self.round_questions = random.sample(self.questions, question_count)
        self.broadcast({
            "type": "game_started",
            "message": "Гра почалась!",
            "total_questions": len(self.round_questions),
        })

        for index, question in enumerate(self.round_questions):
            with self.lock:
                self.current_question_index = index
                self.current_round_seconds = max(15 - index * 2, 5)
                self.current_deadline = time.time() + self.current_round_seconds
                self.current_answers = {}

            self.broadcast_question(index, question)
            while time.time() < self.current_deadline:
                time.sleep(0.1)

            self.broadcast_round_result(index, question)
            time.sleep(2)

        with self.lock:
            self.state = "finished"
        self.broadcast_game_over()

    def broadcast_question(self, index, question):
        self.broadcast({
            "type": "question",
            "index": index,
            "number": index + 1,
            "total": len(self.round_questions),
            "question": question["question"],
            "options": question["options"],
            "round_seconds": self.current_round_seconds,
            "scores": self.leaderboard(),
        })
        print(f"Question {index + 1}/{len(self.round_questions)} started ({self.current_round_seconds}s)")

    def handle_answer(self, player, message):
        answer = str(message.get("answer", "")).strip().upper()
        question_index = message.get("question_index")
        now = time.time()

        with self.lock:
            if self.state != "running":
                return
            if question_index != self.current_question_index:
                player.handler.send_json({"type": "error", "message": "Це питання вже не активне."})
                return
            if answer not in OPTION_KEYS:
                player.handler.send_json({"type": "error", "message": "Відповідь має бути A, B, C або D."})
                return
            if now > self.current_deadline:
                player.handler.send_json({"type": "error", "message": "Час на це питання вийшов."})
                return
            if question_index in player.answered_questions:
                player.handler.send_json({"type": "error", "message": "Ви вже відповіли на це питання."})
                return

            question = self.round_questions[question_index]
            correct = answer == question["answer"]
            points = 0
            if correct:
                remaining = max(self.current_deadline - now, 0)
                bonus = int((remaining / self.current_round_seconds) * MAX_SPEED_BONUS)
                points = BASE_POINTS + bonus
                player.score += points

            player.answered_questions.add(question_index)
            self.current_answers[player.player_id] = {
                "answer": answer,
                "correct": correct,
                "points": points,
                "score": player.score,
            }

        player.handler.send_json({
            "type": "answer_received",
            "question_index": question_index,
            "answer": answer,
        })

    def broadcast_round_result(self, index, question):
        with self.lock:
            rows = []
            for player in self.players.values():
                result = self.current_answers.get(player.player_id, {
                    "answer": None,
                    "correct": False,
                    "points": 0,
                    "score": player.score,
                })
                rows.append({
                    "name": player.name,
                    "answer": result["answer"],
                    "correct": result["correct"],
                    "points": result["points"],
                    "score": result["score"],
                    "connected": player.connected,
                })

        self.broadcast({
            "type": "round_result",
            "question_index": index,
            "correct_answer": question["answer"],
            "correct_text": question["options"][question["answer"]],
            "results": sorted(rows, key=lambda item: item["score"], reverse=True),
            "leaderboard": self.leaderboard(),
        })

    def broadcast_game_over(self):
        leaderboard = self.leaderboard()
        winner = leaderboard[0] if leaderboard else None
        self.broadcast({
            "type": "game_over",
            "winner": winner,
            "leaderboard": leaderboard,
        })
        if winner:
            print(f"Winner: {winner['name']} with {winner['score']} points")

    def broadcast_lobby(self):
        self.broadcast({
            "type": "lobby",
            "players": self.lobby_players(),
            "max_players": self.max_players,
            "min_players": self.min_players,
        })

    def lobby_players(self):
        with self.lock:
            return [
                {"name": player.name, "score": player.score, "connected": player.connected}
                for player in self.players.values()
                if player.connected
            ]

    def leaderboard(self):
        with self.lock:
            rows = [
                {"name": player.name, "score": player.score, "connected": player.connected}
                for player in self.players.values()
            ]
        return sorted(rows, key=lambda item: item["score"], reverse=True)

    def broadcast(self, message):
        with self.lock:
            players = list(self.players.values())
        for player in players:
            if player.connected:
                ok = player.handler.send_json(message)
                if not ok:
                    player.connected = False


class GameRequestHandler(SimpleHTTPRequestHandler):
    game = None
    static_dir = None

    def log_message(self, format, *args):
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/ws":
            self.handle_websocket()
            return
        if parsed.path in ("/", "/index.html"):
            self.serve_file("index.html", "text/html; charset=utf-8")
            return
        if parsed.path == "/questions.json":
            self.serve_file("questions.json", "application/json; charset=utf-8")
            return
        self.send_error(404, "Not found")

    def serve_file(self, filename, content_type):
        path = os.path.join(self.static_dir, filename)
        try:
            with open(path, "rb") as file:
                content = file.read()
        except OSError:
            self.send_error(404, "File not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def handle_websocket(self):
        self.ws_send_lock = threading.Lock()
        key = self.headers.get("Sec-WebSocket-Key")
        if not key:
            self.send_error(400, "Missing WebSocket key")
            return

        accept = base64.b64encode(hashlib.sha1((key + WEBSOCKET_GUID).encode("ascii")).digest()).decode("ascii")
        self.send_response(101, "Switching Protocols")
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()

        player = None
        try:
            while True:
                text = self.read_ws_text()
                if text is None:
                    break
                try:
                    message = json.loads(text)
                except json.JSONDecodeError:
                    self.send_json({"type": "error", "message": "Невірний JSON."})
                    continue

                message_type = message.get("type")
                if player is None:
                    if message_type != "join":
                        self.send_json({"type": "error", "message": "Спочатку треба підключитись з ім'ям."})
                        continue
                    player = self.game.add_player(self, self.client_address, message.get("name", ""))
                    if player is None:
                        break
                    continue

                if message_type == "answer":
                    self.game.handle_answer(player, message)
                elif message_type == "ping":
                    self.send_json({"type": "pong", "server_time": time.time()})
                else:
                    self.send_json({"type": "error", "message": f"Невідоме повідомлення: {message_type}"})
        finally:
            if player is not None:
                self.game.disconnect_player(player)

    def read_ws_text(self):
        header = self.rfile.read(2)
        if len(header) < 2:
            return None

        first_byte, second_byte = header
        opcode = first_byte & 0x0F
        masked = second_byte & 0x80
        length = second_byte & 0x7F

        if opcode == 8:
            return None
        if opcode not in (1, 9):
            return None

        if length == 126:
            length = int.from_bytes(self.rfile.read(2), "big")
        elif length == 127:
            length = int.from_bytes(self.rfile.read(8), "big")

        mask = self.rfile.read(4) if masked else b""
        payload = self.rfile.read(length)
        if masked:
            payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))

        if opcode == 9:
            self.send_ws_frame(payload, opcode=10)
            return ""
        return payload.decode("utf-8")

    def send_json(self, message):
        text = json.dumps(message, ensure_ascii=False)
        return self.send_ws_frame(text.encode("utf-8"), opcode=1)

    def send_ws_frame(self, payload, opcode=1):
        try:
            with self.ws_send_lock:
                header = bytes([0x80 | opcode])
                length = len(payload)
                if length < 126:
                    header += bytes([length])
                elif length < 65536:
                    header += bytes([126]) + length.to_bytes(2, "big")
                else:
                    header += bytes([127]) + length.to_bytes(8, "big")
                self.request.sendall(header + payload)
            return True
        except OSError:
            return False


def load_questions(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            questions = json.load(file)
    except FileNotFoundError as exc:
        raise ValueError(f"Questions file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Questions file has invalid JSON: {exc}") from exc

    if not isinstance(questions, list) or len(questions) < QUESTIONS_PER_GAME:
        raise ValueError(f"Questions file must contain at least {QUESTIONS_PER_GAME} questions.")

    for index, item in enumerate(questions, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Question #{index} must be an object.")
        if not isinstance(item.get("question"), str) or not item["question"].strip():
            raise ValueError(f"Question #{index} must have a non-empty question text.")
        options = item.get("options")
        if not isinstance(options, dict) or any(key not in options for key in OPTION_KEYS):
            raise ValueError(f"Question #{index} must have options A, B, C, and D.")
        for key in OPTION_KEYS:
            if not isinstance(options[key], str) or not options[key].strip():
                raise ValueError(f"Question #{index} option {key} must be a non-empty string.")
        answer = str(item.get("answer", "")).strip().upper()
        if answer not in OPTION_KEYS:
            raise ValueError(f"Question #{index} answer must be A, B, C, or D.")
        item["answer"] = answer

    return questions


def get_lan_ip():
    probe = None
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("8.8.8.8", 80))
        return probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        if probe is not None:
            try:
                probe.close()
            except OSError:
                pass


def parse_args():
    parser = argparse.ArgumentParser(description="Vue + Python WebSocket quiz server")
    parser.add_argument("--host", default="0.0.0.0", help="Host/IP to bind. Use 0.0.0.0 for LAN.")
    parser.add_argument("--port", type=int, default=5000, help="HTTP/WebSocket port.")
    parser.add_argument("--questions", default="questions.json", help="Path to questions JSON.")
    return parser.parse_args()


def main():
    args = parse_args()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    questions_path = args.questions
    if not os.path.isabs(questions_path):
        questions_path = os.path.join(base_dir, questions_path)

    try:
        questions = load_questions(questions_path)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    GameRequestHandler.game = QuizGame(questions)
    GameRequestHandler.static_dir = base_dir

    server = ThreadingHTTPServer((args.host, args.port), GameRequestHandler)
    port = server.server_address[1]
    lan_ip = get_lan_ip()
    print(f"Server started on http://{lan_ip}:{port}")
    print("Players open this address in a browser.")
    print("Press Enter here when everyone is in the lobby.")

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    try:
        while True:
            input()
            if GameRequestHandler.game.start_game():
                break
        while GameRequestHandler.game.game_thread and GameRequestHandler.game.game_thread.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
