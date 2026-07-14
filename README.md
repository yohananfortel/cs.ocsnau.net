# Vue Quiz Game

Multiplayer quiz game for 2-20 players on a local network.

The backend is Python and the interface is Vue in the browser. The game uses WebSocket, because browser Vue apps cannot connect to a raw TCP socket directly.

## Files

- `server.py` - Python HTTP + WebSocket server.
- `index.html` - Vue interface for players.
- `questions.json` - Ukrainian question bank.

## Requirements

- Python 3.11 or newer
- Browser on every player's device
- Internet connection for Vue CDN, or replace the CDN script with a local Vue file

## Start The Server

Open a terminal in this folder:

```powershell
python server.py --host 0.0.0.0 --port 5000 --questions questions.json
```

The server prints an address like:

```text
Server started on http://192.168.1.25:5000
```

Players open that address in a browser.

## Start The Game

1. All players open the server address in a browser.
2. Each player enters a name and clicks `Підключитися`.
3. The teacher or host waits until everyone is in the lobby.
4. The host presses `Enter` in the server terminal.
5. The game starts for everyone at the same time.

## Game Rules

- 2-20 players can join before the game starts.
- Every match uses 12 random questions from `questions.json`.
- Questions are simple Ukrainian history, geography, and math questions.
- All players answer the same question at the same time.
- Each question has four choices: A, B, C, D.
- Each player can answer only once per question.
- Correct answers give 100 points plus a speed bonus up to 50 points.
- Round time starts at 15 seconds and gets shorter by 2 seconds each round, down to a minimum of 5 seconds.
- At the end, the browser shows the winner and leaderboard.

## How It Works

- `server.py` serves `index.html` through HTTP.
- The Vue app opens a WebSocket connection to `/ws`.
- The server keeps all game state: players, questions, timer, answers, score, and leaderboard.
- The client only displays data and sends selected answers.
- Messages are JSON objects sent through WebSocket.

## Troubleshooting

- If players cannot open the page, make sure everyone is on the same Wi-Fi or local network.
- If the browser cannot connect, allow Python through Windows Firewall on private networks.
- If the page opens but Vue does not load, check the internet connection because `index.html` loads Vue from CDN.
- To test on the same computer, open `http://127.0.0.1:5000`.
