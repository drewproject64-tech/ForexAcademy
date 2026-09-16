import pytest

from bot import (
    ANALYSIS,
    LESSONS,
    CalcState,
    calculator_menu,
    learn_menu,
    main_menu,
    parse_numbers,
)


def callback_data(markup):
    return [
        button.callback_data
        for row in markup.inline_keyboard
        for button in row
        if button.callback_data
    ]


def test_parse_numbers_valid():
    assert parse_numbers("2500 1.5", 2) == [2500.0, 1.5]
    assert parse_numbers("1000 1 50", 3) == [1000.0, 1.0, 50.0]
    assert parse_numbers("10,5 2", 2) == [10.5, 2.0]


@pytest.mark.parametrize(
    ("value", "count"),
    [
        ("", 2),
        ("2500", 2),
        ("2500 1.5 extra", 2),
        ("abc 1", 2),
        ("nan 1", 2),
        ("inf 1", 2),
    ],
)
def test_parse_numbers_invalid(value, count):
    with pytest.raises(ValueError):
        parse_numbers(value, count)


def test_main_menu_has_three_core_functions_and_help():
    data = callback_data(main_menu())
    assert data == ["menu:learn", "menu:analysis", "menu:calculators", "menu:help"]


def test_all_learn_buttons_have_content():
    data = callback_data(learn_menu())
    keys = [item.split(":", 1)[1] for item in data if item.startswith("learn:")]
    assert keys
    assert set(keys) == set(LESSONS)


def test_all_calculator_buttons_are_supported():
    data = callback_data(calculator_menu())
    assert {"calc:percentage", "calc:rr", "calc:position", "home"} <= set(data)
    assert CalcState.percentage.state
    assert CalcState.risk_reward.state
    assert CalcState.position.state


def test_analysis_topics_have_content():
    assert set(ANALYSIS) == {"technical", "fundamental", "support", "sessions"}


def test_run_again_buttons_keep_calculator_identity():
    from bot import input_menu

    assert callback_data(input_menu("percentage"))[0] == "calculator:again:percentage"
    assert callback_data(input_menu("rr"))[0] == "calculator:again:rr"
    assert callback_data(input_menu("position"))[0] == "calculator:again:position"
