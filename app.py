# -*- coding: utf-8 -*-
"""
AUTO CHOICE — локальный тест «Какой способ покупки автомобиля вам подходит?».

Запуск: python app.py
Сайт откроется по адресу: http://127.0.0.1:5000
"""

from flask import Flask, redirect, render_template, request, session, url_for

from branding import BRAND
from quiz_data import DISCLAIMER, QUESTIONS, TOTAL_QUESTIONS
from scoring import build_result

app = Flask(__name__)
# Ключ нужен только для работы сессий на локальном компьютере.
# Никакие данные наружу не отправляются.
app.secret_key = "auto-choice-local-dev"


@app.context_processor
def inject_common():
    """Передаёт название бренда во все шаблоны."""
    return {"brand": BRAND}


@app.route("/")
def index():
    """Стартовый экран."""
    session.clear()
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    """Начало теста: создаём пустой список ответов."""
    session["answers"] = {}
    return redirect(url_for("question", number=1))


@app.route("/question/<int:number>", methods=["GET", "POST"])
def question(number):
    """Показ одного вопроса и сохранение ответа на него."""
    answers = session.get("answers")
    if answers is None:
        return redirect(url_for("index"))

    if number < 1 or number > TOTAL_QUESTIONS:
        return redirect(url_for("question", number=1))

    # Не даём перепрыгнуть через ещё не отвеченные вопросы.
    first_unanswered = 1
    for i in range(1, TOTAL_QUESTIONS + 1):
        if str(i) not in answers:
            first_unanswered = i
            break
    else:
        first_unanswered = TOTAL_QUESTIONS
    if number > first_unanswered:
        return redirect(url_for("question", number=first_unanswered))

    current = QUESTIONS[number - 1]
    error = None

    if request.method == "POST":
        choice = request.form.get("answer", type=int)
        valid = choice is not None and 0 <= choice < len(current["options"])
        if not valid:
            error = "Пожалуйста, выберите один из вариантов, чтобы продолжить."
        else:
            answers[str(number)] = choice
            session["answers"] = answers
            session.modified = True
            if number >= TOTAL_QUESTIONS:
                return redirect(url_for("result"))
            return redirect(url_for("question", number=number + 1))

    return render_template(
        "question.html",
        q=current,
        number=number,
        total=TOTAL_QUESTIONS,
        selected=answers.get(str(number)),
        error=error,
        progress_percent=int(number / TOTAL_QUESTIONS * 100),
    )


@app.route("/result")
def result():
    """Экран результата."""
    answers = session.get("answers")
    if not answers:
        return redirect(url_for("index"))

    # Если отвечено не на всё — ведём на первый вопрос без ответа.
    if len(answers) < TOTAL_QUESTIONS:
        for i in range(1, TOTAL_QUESTIONS + 1):
            if str(i) not in answers:
                return redirect(url_for("question", number=i))

    ordered = [answers[str(i)] for i in range(1, TOTAL_QUESTIONS + 1)]
    return render_template(
        "result.html",
        result=build_result(ordered),
        disclaimer=DISCLAIMER,
    )


if __name__ == "__main__":
    app.run(debug=True)
