// AUTO CHOICE — минимальный JavaScript.
// Тест полностью работает и без JS; здесь только две небольшие задачи:
// 1) сообщение кнопки «Обсудить мой случай» на странице результата;
// 2) подсветка выбранного варианта ответа (подстраховка для старых браузеров).

document.addEventListener("DOMContentLoaded", function () {
    // 1. Кнопка «Обсудить мой случай» — пока ничего никуда не отправляет.
    var consultBtn = document.getElementById("consult-btn");
    var consultMessage = document.getElementById("consult-message");
    if (consultBtn && consultMessage) {
        consultBtn.addEventListener("click", function () {
            consultMessage.hidden = false;
        });
    }

    // 2. Подсветка выбранного варианта (в современных браузерах это делает CSS :has).
    var radios = document.querySelectorAll('.option input[type="radio"]');
    radios.forEach(function (radio) {
        radio.addEventListener("change", function () {
            radios.forEach(function (r) {
                var option = r.closest(".option");
                if (option) {
                    option.classList.toggle("is-selected", r.checked);
                }
            });
        });
    });
});
