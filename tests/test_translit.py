from friday.translit import latin_to_cyrillic


def test_russian_text_is_unchanged():
    assert latin_to_cyrillic("Привет, как дела?") == "Привет, как дела?"


def test_digits_and_punctuation_are_unchanged():
    assert latin_to_cyrillic("Сейчас 12:30, ок!") == "Сейчас 12:30, ок!"


def test_empty_text():
    assert latin_to_cyrillic("") == ""


def test_dictionary_words():
    assert latin_to_cyrillic("Yandex Music") == "Яндекс Мьюзик"
    assert latin_to_cyrillic("Python") == "Пайтон"
    assert latin_to_cyrillic("GitHub") == "Гитхаб"
    assert latin_to_cyrillic("Windows") == "Виндоус"
    assert latin_to_cyrillic("YouTube") == "Ютуб"


def test_dictionary_ignores_case_but_keeps_first_capital():
    assert latin_to_cyrillic("python") == "пайтон"
    assert latin_to_cyrillic("Python") == "Пайтон"


def test_mixed_sentence():
    text = "Включи Python и Windows"
    assert latin_to_cyrillic(text) == "Включи Пайтон и Виндоус"


def test_fallback_digraphs():
    assert latin_to_cyrillic("chat") == "чат"
    assert latin_to_cyrillic("shop") == "шоп"


def test_fallback_single_letters():
    assert latin_to_cyrillic("box") == "бокс"


def test_fallback_keeps_first_capital():
    assert latin_to_cyrillic("Shop") == "Шоп"


def test_fallback_all_caps_stays_upper():
    assert latin_to_cyrillic("USB") == "УСБ"


def test_latin_inside_russian_text_keeps_the_rest():
    assert latin_to_cyrillic("Открой chat сейчас") == "Открой чат сейчас"
