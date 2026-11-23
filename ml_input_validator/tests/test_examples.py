import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solution import validate_and_normalize


def test_r1_sucesso_country_normalizado():
    result = validate_and_normalize({
        "request_id": "r-1",
        "features": {"age": 34, "income": 1200.5, "country": " br "},
    })
    assert result == {
        "ok": True,
        "request_id": "r-1",
        "features": {"age": 34, "income": 1200.5, "country": "BR"},
    }


def test_r2_age_fora_da_faixa():
    result = validate_and_normalize({
        "request_id": "r-2",
        "features": {"age": 121, "income": 1200.5, "country": "BR"},
    })
    assert result == {
        "ok": False,
        "request_id": "r-2",
        "errors": [{"field": "features.age", "code": "out_of_range"}],
    }


def test_r3_income_nao_finito():
    result = validate_and_normalize({
        "request_id": "r-3",
        "features": {"age": 34, "income": float("inf"), "country": "BR"},
    })
    assert result == {
        "ok": False,
        "request_id": "r-3",
        "errors": [{"field": "features.income", "code": "not_finite"}],
    }


def test_r4_chave_desconhecida():
    result = validate_and_normalize({
        "request_id": "r-4",
        "features": {"age": 34, "income": 1200.5, "country": "BR",
                     "device": "ios"},
    })
    assert result == {
        "ok": False,
        "request_id": "r-4",
        "errors": [{"field": "features.device", "code": "unknown_field"}],
    }


def test_r5_menor_16_com_renda_inconsistente():
    result = validate_and_normalize({
        "request_id": "r-5",
        "features": {"age": 15, "income": 100, "country": "BR"},
    })
    assert result == {
        "ok": False,
        "request_id": "r-5",
        "errors": [{"field": "features.income", "code": "consistency"}],
    }
