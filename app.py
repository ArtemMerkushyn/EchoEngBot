from flask import Flask, request, jsonify, send_from_directory
import json
import random
import os

app = Flask(__name__)
DB_FILE = "database.json"
Syn_FILE = "synonymsdb.json"

# Загрузка базы данных
def load_database():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({}, f)
    with open(DB_FILE, 'r') as f:
        return json.load(f)
    
# Загрузка синонимов
def load_synonyms():
    try:
        with open(Syn_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Проверяет, является ли введённая фраза синонимом
def resolve_synonym(phrase, synonyms):
    for main_phrase, syn_list in synonyms.items():
        if phrase == main_phrase or phrase in syn_list:
            return main_phrase
    return phrase

# Сохранение базы данных
def save_database(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Главная страница — отдаём HTML
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

# Обрабатывает входящее сообщение от пользователя
# Ищет фразу или её синоним в базе и возвращает ответ
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").strip().lower()

    db = load_database()
    synonyms = load_synonyms()
    main_phrase = resolve_synonym(user_input, synonyms)

    if main_phrase in db:
        answer = random.choice(db[main_phrase])
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

# Возвращает все фразы и ответы, известные боту
@app.route("/all-phrases", methods=["GET"])
def get_all_phrases():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
    except FileNotFoundError:
        return jsonify({"data": {}, "message": "Database is empty."})
    
    return jsonify({"data": db})

# Добавляет новый синоним к основной фразе
@app.route("/add-synonym", methods=["POST"])
def add_synonym():
    data = request.get_json()
    main = data.get("main", "").strip().lower()
    synonym = data.get("synonym", "").strip().lower()

    if not main or not synonym:
        return jsonify({"message": "Main phrase and synonym are required."}), 400

    try:
        with open("synonymsdb.json", "r", encoding="utf-8") as f:
            synonyms = json.load(f)
    except FileNotFoundError:
        synonyms = {}

    if main not in synonyms:
        synonyms[main] = []

    if synonym not in synonyms[main]:
        synonyms[main].append(synonym)

    with open("synonymsdb.json", "w", encoding="utf-8") as f:
        json.dump(synonyms, f, ensure_ascii=False, indent=2)

    return jsonify({"message": f"Synonym '{synonym}' added for '{main}'"})

# Редактирует синоним: заменяет старый синоним на новый для указанной фразы
@app.route("/edit-synonym", methods=["POST"])
def edit_synonym():
    data = request.get_json()
    main = data.get("main", "").strip().lower()
    old_syn = data.get("old_syn", "").strip().lower()
    new_syn = data.get("new_syn", "").strip().lower()
    
    if not main or not old_syn or not new_syn:
        return jsonify({"message": "Main phrase, old synonym, and new synonym are required."}), 400
    
    try:
        with open(Syn_FILE, "r", encoding="utf-8") as f:
            synonyms = json.load(f)
    except FileNotFoundError:
        return jsonify({"message": "Synonym database not found."}), 500
    
    if main not in synonyms or old_syn not in synonyms[main]:
        return jsonify({"message": "Main phrase or old synonym not found."}), 404
    
    synonyms[main].remove(old_syn)
    if new_syn not in synonyms[main]:
        synonyms[main].append(new_syn)
    
    with open(Syn_FILE, "w", encoding="utf-8") as f:
        json.dump(synonyms, f, ensure_ascii=False, indent=2)
    
    return jsonify({"message": f"Synonym '{old_syn}' updated to '{new_syn}' for '{main}'"})

# Удаляет один синоним или все синонимы для указанной основной фразы
@app.route("/delete-synonym", methods=["POST"])
def delete_synonym():
    data = request.get_json()
    main = data.get("main", "").strip().lower()
    synonym = data.get("synonym", "").strip().lower()

    try:
        with open("synonymsdb.json", "r", encoding="utf-8") as f:
            synonyms = json.load(f)
    except FileNotFoundError:
        return jsonify({"message": "Synonym database not found."}), 500
    
    if main not in synonyms:
        return jsonify({"message": "Main phrase not found."}), 404
    
    if synonym:
        if synonym in synonyms[main]:
            synonyms[main].remove(synonym)
            if not synonyms[main]: # если список стал пустым — удалим ключ
                del synonyms[main]
            message = f"Synonym '{synonym}' removed from '{main}'."
        else:
            return jsonify({"message": "Synonym not found for that phrase."}), 404
    else:
        del synonyms[main]
        message = f"All synonyms removed for '{main}'."

    with open(Syn_FILE, "w", encoding="utf-8") as f:
        json.dump(synonyms, f, ensure_ascii=False, indent=2)
    
    return jsonify({message: message})

# Возвращает все синонимы в виде словаря
@app.route("/all-synonyms", methods=["GET"])
def get_all_synonyms():
    try:
        with open(Syn_FILE, "r", encoding="utf-8") as f:
            syn = json.load(f)
    except FileNotFoundError:
        return jsonify({"data": {}, "message": "Synonym database is empty."})
    
    return jsonify({"data": syn})

if __name__ == "__main__":
    app.run(debug=True)
