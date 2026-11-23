import copy
import math
import os
import sys

import pytest

# garante que o solution.py da mesma pasta seja encontrado, de onde quer que o pytest rode
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from solution import validate_normalize_request as v


def req(**features):
    return {"request_id": "r1", "features": features}


def errs(result):
    return [(e["field"], e["code"]) for e in result["errors"]]


# --- Sucesso ---------------------------------------------------------------

def test_sucesso_normaliza_country_e_ordena_features():
    r = v({"request_id": "r1",
           "features": {"country": "  br ", "income": 2500.5, "age": 34}})
    assert r == {"ok": True, "request_id": "r1",
                 "features": {"age": 34, "income": 2500.5, "country": "BR"}}
    assert list(r["features"]) == ["age", "income", "country"]


def test_limites_de_idade():
    assert v(req(age=0, income=0, country="BR"))["ok"]
    assert v(req(age=120, income=10, country="BR"))["ok"]


def test_income_inteiro_nao_e_convertido():
    r = v(req(age=30, income=100, country="br"))
    assert r["features"]["income"] == 100
    assert type(r["features"]["income"]) is int


def test_menor_de_16_com_income_zero_ok():
    assert v(req(age=15, income=0, country="BR"))["ok"]
    assert v(req(age=15, income=0.0, country="BR"))["ok"]


@pytest.mark.parametrize("rid", ["r1", 123, None, ["x"], {"a": 1}])
def test_request_id_repassado_como_veio(rid):
    ok = v({"request_id": rid, "features": {"age": 1, "income": 0, "country": "x"}})
    bad = v({"request_id": rid, "features": None})
    assert ok["request_id"] == rid and bad["request_id"] == rid


# --- Erros por campo ---------------------------------------------------------

def test_missing_vs_null():
    assert errs(v(req(income=0, country="BR"))) == [("features.age", "missing")]
    assert errs(v(req(age=None, income=0, country="BR"))) == [("features.age", "null")]


@pytest.mark.parametrize("age", ["34", 34.0, True, False, [34]])
def test_age_tipo_invalido(age):
    assert errs(v(req(age=age, income=0, country="BR"))) == [("features.age", "invalid_type")]


@pytest.mark.parametrize("age", [-1, 121])
def test_age_fora_da_faixa(age):
    assert errs(v(req(age=age, income=0, country="BR"))) == [("features.age", "out_of_range")]


@pytest.mark.parametrize("income", ["100", True, None])
def test_income_tipo_ou_nulo(income):
    code = "null" if income is None else "invalid_type"
    assert errs(v(req(age=30, income=income, country="BR"))) == [("features.income", code)]


@pytest.mark.parametrize("income", [math.nan, math.inf, -math.inf])
def test_income_nao_finito(income):
    assert errs(v(req(age=30, income=income, country="BR"))) == [("features.income", "not_finite")]


def test_income_negativo_e_inteiro_gigante():
    assert errs(v(req(age=30, income=-0.01, country="BR"))) == [("features.income", "out_of_range")]
    assert v(req(age=30, income=10 ** 400, country="BR"))["ok"]


@pytest.mark.parametrize("country,code", [("", "empty"), ("   ", "empty"),
                                          (55, "invalid_type"), (None, "null")])
def test_country(country, code):
    assert errs(v(req(age=30, income=0, country=country))) == [("features.country", code)]


def test_unknown_field():
    r = v(req(age=30, income=0, country="BR", device="ios"))
    assert errs(r) == [("features.device", "unknown_field")]


# --- Consistência e ordem ----------------------------------------------------

def test_consistency_menor_de_16_com_renda():
    assert errs(v(req(age=15, income=1, country="BR"))) == [("features.income", "consistency")]


def test_consistency_so_quando_age_e_income_validos():
    assert errs(v(req(age="15", income=5, country="BR"))) == [("features.age", "invalid_type")]
    assert errs(v(req(age=15, income=-5, country="BR"))) == [("features.income", "out_of_range")]


def test_todos_os_erros_em_ordem_estavel():
    r = v({"request_id": "r9",
           "features": {"zeta": 1, "country": " ", "income": 10, "age": 10, "alpha": 2}})
    assert errs(r) == [
        ("features.income", "consistency"),
        ("features.country", "empty"),
        ("features.alpha", "unknown_field"),
        ("features.zeta", "unknown_field"),
    ]
    assert r["request_id"] == "r9" and "features" not in r


# --- Entradas malformadas -----------------------------------------------------

@pytest.mark.parametrize("bad", [None, [], "texto", 42, {"features": {}}, {}])
def test_nunca_lanca_excecao(bad):
    r = v(bad)
    assert r["ok"] is False and r["errors"]


def test_features_ausente_nulo_tipo():
    assert errs(v({"request_id": "r1"})) == [("features", "missing")]
    assert errs(v({"request_id": "r1", "features": None})) == [("features", "null")]
    assert errs(v({"request_id": "r1", "features": ["age"]})) == [("features", "invalid_type")]


def test_chave_nao_string_nao_quebra():
    r = v({"request_id": "r1", "features": {"age": 30, "income": 0, "country": "BR", 1: "x", None: 2}})
    assert r["ok"] is False
    assert all(e["code"] == "unknown_field" for e in r["errors"])


def test_erros_nao_contem_valor_bruto():
    segredo = "valor-secreto-123"
    r = v(req(age=segredo, income=segredo, country=123))
    assert segredo not in repr(r)


def test_nao_modifica_entrada_e_deterministico():
    entrada = {"request_id": "r1", "features": {"age": 20, "income": 1.5, "country": " br "}}
    original = copy.deepcopy(entrada)
    a, b = v(entrada), v(entrada)
    assert entrada == original
    assert a == b


# --- Os 5 casos do enunciado, com a requisição em vários formatos ---------------

from types import MappingProxyType, SimpleNamespace
from collections import UserDict

FORMATOS = {
    "dict": lambda rid, f: {"request_id": rid, "features": f},
    "mappingproxy": lambda rid, f: MappingProxyType({"request_id": rid, "features": MappingProxyType(f)}),
    "userdict": lambda rid, f: UserDict({"request_id": rid, "features": UserDict(f)}),
    "objeto": lambda rid, f: SimpleNamespace(request_id=rid, features=f),
}

CASOS = [
    ("R1", {"age": 34, "income": 2500.5, "country": " br "},
     {"ok": True, "request_id": "R1", "features": {"age": 34, "income": 2500.5, "country": "BR"}}),
    ("R2", {"age": 130, "income": 10, "country": "BR"},
     {"ok": False, "request_id": "R2", "errors": [{"field": "features.age", "code": "out_of_range"}]}),
    ("R3", {"age": 30, "income": float("inf"), "country": "BR"},
     {"ok": False, "request_id": "R3", "errors": [{"field": "features.income", "code": "not_finite"}]}),
    ("R4", {"age": 30, "income": 10, "country": "BR", "device": "ios"},
     {"ok": False, "request_id": "R4", "errors": [{"field": "features.device", "code": "unknown_field"}]}),
    ("R5", {"age": 15, "income": 100, "country": "BR"},
     {"ok": False, "request_id": "R5", "errors": [{"field": "features.income", "code": "consistency"}]}),
]


@pytest.mark.parametrize("formato", FORMATOS)
@pytest.mark.parametrize("rid,features,esperado", CASOS)
def test_casos_do_enunciado(formato, rid, features, esperado):
    assert v(FORMATOS[formato](rid, features)) == esperado
