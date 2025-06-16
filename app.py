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

# редактирование ответа
@app.route("/edit", methods=["POST"])
def edit_answer():
    data = request.get_json()
    phrase = data.get("phrase", "").strip().lower()
    old_answer = (data.get("old_answer") or "").strip()
    new_answer = (data.get("new_answer") or "").strip()

    if not phrase or not old_answer or not new_answer:
        return jsonify({"message": "Missing required fields."})
    
    # загружаем базу
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
    except FileNotFoundError:
        return jsonify({"message": "Knowledge base is empty."})
    
    if phrase not in db or old_answer not in db[phrase]:
        return jsonify({"message": "Phrase or old answer not found."})
    
    # обновляем ответ
    db[phrase].remove(old_answer)
    db[phrase].append(new_answer)

    # сохраняем ответ
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    
    return jsonify({"message": "Answer updated successfully."})

# удаление фразы или конкретного ответа к этой фразе
@app.route("/delete", methods=["POST"])
def delete_from_bot():
    data = request.get_json()
    phrase = data.get("phrase", "").strip().lower()
    answer = (data.get("answer") or "").strip()

    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
    except FileNotFoundError:
        db = {}

    if phrase not in db:
        return jsonify({"message": "Phrase not found."})

    if answer:
        # Удаляем конкретный ответ
        if answer in db[phrase]:
            db[phrase].remove(answer)
            if not db[phrase]:
                del db[phrase]  # Если больше нет ответов, удаляем всю фразу
            message = "Answer deleted."
        else:
            return jsonify({"message": "Answer not found."})
    else:
        # Удаляем всю фразу
        del db[phrase]
        message = "Phrase and all answers deleted."

    # Сохраняем изменения
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    return jsonify({"message": message})

if __name__ == "__main__":
    app.run(debug=True)
