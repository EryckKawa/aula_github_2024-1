import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from solution import validate_normalize_request


def test_r1_sucesso_country_normalizado():
    r = validate_normalize_request(
        {"request_id": "r1", "features": {"age": 34, "income": 1200.5, "country": " br "}})
    assert r == {"ok": True, "request_id": "r1",
                 "features": {"age": 34, "income": 1200.5, "country": "BR"}}


def test_r2_age_fora_da_faixa():
    r = validate_normalize_request(
        {"request_id": "r2", "features": {"age": 121, "income": 1200.5, "country": "BR"}})
    assert r == {"ok": False, "request_id": "r2",
                 "errors": [{"field": "features.age", "code": "out_of_range"}]}


def test_r3_income_nao_finito():
    r = validate_normalize_request(
        {"request_id": "r3", "features": {"age": 34, "income": float("inf"), "country": "BR"}})
    assert r == {"ok": False, "request_id": "r3",
                 "errors": [{"field": "features.income", "code": "not_finite"}]}


def test_r4_chave_desconhecida():
    r = validate_normalize_request(
        {"request_id": "r4", "features": {"age": 34, "income": 1200.5, "country": "BR", "device": "ios"}})
    assert r == {"ok": False, "request_id": "r4",
                 "errors": [{"field": "features.device", "code": "unknown_field"}]}


def test_r5_menor_de_16_com_renda():
    r = validate_normalize_request(
        {"request_id": "r5", "features": {"age": 15, "income": 100, "country": "BR"}})
    assert r == {"ok": False, "request_id": "r5",
                 "errors": [{"field": "features.income", "code": "consistency"}]}
