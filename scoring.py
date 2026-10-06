# -*- coding: utf-8 -*-
"""
Подсчёт результата теста.

Логика отделена от Flask-приложения, чтобы её можно было
менять и проверять независимо от интерфейса.
"""

from quiz_data import QUESTIONS, RESULTS, THRESHOLDS


def max_possible_score():
    """Максимально возможная сумма баллов за весь тест."""
    return sum(max(option["points"] for option in q["options"]) for q in QUESTIONS)


def calculate_score(answers):
    """
    Считает сумму баллов.

    answers — список индексов выбранных вариантов
    в порядке вопросов, например [0, 2, 1, 3, 2, 0, 1].
    """
    total = 0
    for question, choice in zip(QUESTIONS, answers):
        total += question["options"][choice]["points"]
    return total


def result_key_for_score(score):
    """Переводит сумму баллов в ключ результата по порогам из quiz_data."""
    if score >= THRESHOLDS["order_min"]:
        return "order"
    if score >= THRESHOLDS["compare_min"]:
        return "compare"
    return "stock"


def _scored_answers(answers):
    """Список ответов с баллами, категориями и факторами, в порядке вопросов."""
    scored = []
    for index, (question, choice) in enumerate(zip(QUESTIONS, answers)):
        option = question["options"][choice]
        scored.append({
            "question_index": index,
            "points": option["points"],
            "group": option["group"],
            "factor": option["factor"],
        })
    return scored


def _pop_unused(items, used_groups):
    """
    Снимает с начала списка первый элемент, чья смысловая категория
    ещё не использована. Элементы с уже занятой категорией пропускаются
    (это и есть удаление смысловых дублей). Если подходящих нет — None.
    """
    while items:
        item = items.pop(0)
        if item["group"] not in used_groups:
            return item
    return None


def pick_factors(answers, result_key, limit=3):
    """
    Выбирает до трёх факторов, сильнее всего повлиявших на результат.

    Правила:
    - факторы берутся только из реально выбранных ответов пользователя;
    - два фактора из одной смысловой категории (group) не показываются;
    - «под заказ» — самые сильные ответы в пользу заказа;
    - «в наличии» — самые сильные ответы в пользу покупки из наличия;
    - «сравнить оба» — по очереди самые сильные разные аргументы
      обеих сторон, тоже без повторов категорий;
    - при равных баллах раньше идёт фактор из более раннего вопроса;
    - если разных причин меньше трёх, показываем столько, сколько есть,
      и не добиваем блок слабыми или повторяющимися причинами.
    """
    scored = _scored_answers(answers)
    used_groups = set()
    picked = []

    if result_key in ("order", "stock"):
        # Одна сторона: сортируем по силе ответа и берём разные категории.
        if result_key == "order":
            candidates = sorted(
                scored, key=lambda s: (-s["points"], s["question_index"])
            )
        else:
            candidates = sorted(
                scored, key=lambda s: (s["points"], s["question_index"])
            )
        while len(picked) < limit:
            item = _pop_unused(candidates, used_groups)
            if item is None:
                break
            picked.append(item)
            used_groups.add(item["group"])

    else:  # compare — чередуем аргументы обеих сторон
        pro_order = sorted(
            (s for s in scored if s["points"] >= 2),
            key=lambda s: (-s["points"], s["question_index"]),
        )
        pro_stock = sorted(
            (s for s in scored if s["points"] <= 1),
            key=lambda s: (s["points"], s["question_index"]),
        )
        # С какой стороны начать чередование: где больше аргументов;
        # при равенстве — где фактор встретился раньше в тесте.
        if len(pro_stock) > len(pro_order) or (
            len(pro_stock) == len(pro_order)
            and pro_stock
            and pro_order
            and pro_stock[0]["question_index"] < pro_order[0]["question_index"]
        ):
            sides = [pro_stock, pro_order]
        else:
            sides = [pro_order, pro_stock]

        turn = 0
        while len(picked) < limit and (sides[0] or sides[1]):
            item = _pop_unused(sides[turn % 2], used_groups)
            if item is not None:
                picked.append(item)
                used_groups.add(item["group"])
            turn += 1

    return [s["factor"] for s in picked]


def build_result(answers):
    """Возвращает готовый словарь с результатом для страницы."""
    score = calculate_score(answers)
    key = result_key_for_score(score)
    return {
        "key": key,
        "title": RESULTS[key]["title"],
        "text": RESULTS[key]["text"],
        "factors": pick_factors(answers, key),
        # Баллы остаются во внутренней логике, на странице не показываются.
        "score": score,
        "max_score": max_possible_score(),
    }
