from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3, random

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT, score INTEGER)")
    conn.commit()
    conn.close()

init_db()

# ---------- GAME LOGIC ----------
def check_winner(board):
    wins = [
        [0,1,2],[3,4,5],[6,7,8],
        [0,3,6],[1,4,7],[2,5,8],
        [0,4,8],[2,4,6]
    ]
    for w in wins:
        if board[w[0]] == board[w[1]] == board[w[2]] and board[w[0]] != "":
            return board[w[0]], w
    if "" not in board:
        return "Draw", []
    return None, []

def minimax(board, is_max):
    winner, _ = check_winner(board)
    if winner == "O": return 1
    if winner == "X": return -1
    if winner == "Draw": return 0

    if is_max:
        best = -100
        for i in range(9):
            if board[i] == "":
                board[i] = "O"
                best = max(best, minimax(board, False))
                board[i] = ""
        return best
    else:
        best = 100
        for i in range(9):
            if board[i] == "":
                board[i] = "X"
                best = min(best, minimax(board, True))
                board[i] = ""
        return best

def smart_ai(board, difficulty):
    empty = [i for i in range(9) if board[i] == ""]

    if difficulty == "easy":
        return random.choice(empty)

    if difficulty == "medium" and random.random() < 0.5:
        return random.choice(empty)

    # try win
    for i in empty:
        board[i] = "O"
        if check_winner(board)[0] == "O":
            board[i] = ""
            return i
        board[i] = ""

    # block
    for i in empty:
        board[i] = "X"
        if check_winner(board)[0] == "X":
            board[i] = ""
            return i
        board[i] = ""

    # minimax (hard)
    best_val = -100
    move = empty[0]
    for i in empty:
        board[i] = "O"
        val = minimax(board, False)
        board[i] = ""
        if val > best_val:
            best_val = val
            move = i

    return move

# ---------- AUTH ----------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (user,pwd))
        res = cur.fetchone()

        if res:
            session["user"] = user
            return redirect("/lobby")
        return "Invalid login"

    return render_template("login.html")

@app.route("/register", methods=["POST"])
def register():
    user = request.form["username"]
    pwd = request.form["password"]

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO users VALUES (?, ?, ?)", (user,pwd,0))
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/lobby")
def lobby():
    if "user" not in session:
        return redirect("/")
    return render_template("lobby.html")

@app.route("/game")
def game():
    if "user" not in session:
        return redirect("/")
    return render_template("index.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- GAME API ----------
@app.route("/move", methods=["POST"])
def move():
    data = request.get_json()
    board = data["board"]
    difficulty = data.get("difficulty","hard")

    ai = smart_ai(board, difficulty)
    board[ai] = "O"

    winner, combo = check_winner(board)

    # update score
    if winner == "X":
        conn = sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("UPDATE users SET score=score+1 WHERE username=?", (session["user"],))
        conn.commit()
        conn.close()

    return jsonify({"board":board,"winner":winner,"combo":combo})

@app.route("/leaderboard")
def leaderboard():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT username,score FROM users ORDER BY score DESC")
    data = cur.fetchall()
    conn.close()
    return jsonify(data)

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)