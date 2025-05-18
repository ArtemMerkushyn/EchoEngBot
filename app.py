from flask import Flask, request, jsonify, send_from_directory
import json
import random
import os

app = Flask(__name__)
DB_FILE = "database.json"

# Загрузка базы данных
def load_database():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({}, f)
    with open(DB_FILE, 'r') as f:
        return json.load(f)

# Сохранение базы данных
def save_database(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Главная страница — отдаём HTML
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

# Получение ответа от бота
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").strip().lower()
    db = load_database()

    if user_input in db:
        answer = random.choice(db[user_input])
        return jsonify({"response": answer})
    else:
        return jsonify({"response": "I don't know how to answer this. Please teach me!"})

# Обучение бота новой фразе и ответу
@app.route("/teach", methods=["POST"])
def teach():
    data = request.json
    phrase = data.get("phrase", "").strip().lower()
    answer = data.get("answer", "").strip()

    if not phrase or not answer:
        return jsonify({"status": "error", "message": "The phrase and answer must not be empty."}), 400

    db = load_database()

    if phrase not in db:
        db[phrase] = [answer]
    else:
        if answer not in db[phrase]:
            db[phrase].append(answer)

    save_database(db)
    return jsonify({"status": "success", "message": f"Phrase '{phrase}' successfully trained."})

if __name__ == "__main__":
    app.run(debug=True)
