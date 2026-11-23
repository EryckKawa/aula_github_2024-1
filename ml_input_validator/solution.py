"""Validador determinístico de requisições para o modelo de inferência.

A função pública é ``validate_normalize_request(request)``.

Contrato:
- Pura: não chama o modelo, não acessa rede, não usa estado global, não
  modifica a entrada.
- Nunca lança exceção.
- Sucesso: {"ok": True, "request_id": ..., "features": {age, income, country}}
- Falha:   {"ok": False, "request_id": ..., "errors": [{"field", "code"}, ...]}
- Os erros nunca incluem o valor bruto de um campo.
"""

from collections.abc import Mapping
import math

# Códigos de erro possíveis
MISSING = "missing"            # campo ausente
NULL = "null"                  # campo presente com valor None
INVALID_TYPE = "invalid_type"  # tipo incorreto (inclui bool em campo numérico)
OUT_OF_RANGE = "out_of_range"  # número fora da faixa permitida
NOT_FINITE = "not_finite"      # NaN, inf ou -inf
EMPTY = "empty"                # texto vazio após remover espaços das pontas
UNKNOWN_FIELD = "unknown_field"  # chave não prevista em features
CONSISTENCY = "consistency"    # combinação inválida entre campos válidos

# Ordem do esquema: define a ordem da saída e a ordem dos erros.
SCHEMA_ORDER = ("age", "income", "country")

_ABSENT = object()  # sentinela para distinguir "ausente" de "None"


def _error(field, code):
    return {"field": field, "code": code}


def _is_number(value):
    # bool é subclasse de int em Python, mas aqui é tipo incorreto.
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# --- Validadores por campo -------------------------------------------------
# Cada um devolve (valor_normalizado, codigo_de_erro_ou_None).
# Só são chamados quando o campo está presente e não é None.

def _validate_age(value):
    if not isinstance(value, int) or isinstance(value, bool):
        return None, INVALID_TYPE  # "34" e 34.0 não são inteiros
    if not 0 <= value <= 120:
        return None, OUT_OF_RANGE
    return value, None


def _validate_income(value):
    if not _is_number(value):
        return None, INVALID_TYPE
    # int em Python é sempre finito; math.isfinite estoura (OverflowError)
    # com inteiros gigantes, então só checamos float.
    if isinstance(value, float) and not math.isfinite(value):
        return None, NOT_FINITE
    if value < 0:
        return None, OUT_OF_RANGE
    return value, None


def _validate_country(value):
    if not isinstance(value, str):
        return None, INVALID_TYPE
    normalized = value.strip()
    if not normalized:
        return None, EMPTY
    return normalized.upper(), None


_VALIDATORS = {
    "age": _validate_age,
    "income": _validate_income,
    "country": _validate_country,
}


# --- Função principal ------------------------------------------------------

def _validate(request):
    if not isinstance(request, Mapping):
        return None, None, [_error("request", INVALID_TYPE)]

    # request_id não é validado: é repassado exatamente como recebido.
    request_id = request.get("request_id")

    features = request.get("features", _ABSENT)
    if features is _ABSENT:
        return request_id, None, [_error("features", MISSING)]
    if features is None:
        return request_id, None, [_error("features", NULL)]
    if not isinstance(features, Mapping):
        return request_id, None, [_error("features", INVALID_TYPE)]

    errors = []
    normalized = {}

    for name in SCHEMA_ORDER:
        field = "features." + name
        value = features.get(name, _ABSENT)

        if value is _ABSENT:
            errors.append(_error(field, MISSING))
            continue
        if value is None:
            errors.append(_error(field, NULL))
            continue

        clean, code = _VALIDATORS[name](value)
        if code is not None:
            errors.append(_error(field, code))
            continue
        normalized[name] = clean

        # Regra entre campos: avaliada só quando age e income são válidos
        # individualmente; o erro fica na posição de income.
        if name == "income" and "age" in normalized:
            if normalized["age"] < 16 and clean != 0:
                errors.append(_error(field, CONSISTENCY))

    # Chaves desconhecidas, depois dos campos do esquema, em ordem
    # determinística (independe da ordem de inserção do dict de entrada).
    unknown = [k for k in features.keys() if k not in _VALIDATORS]
    for key in sorted(unknown, key=lambda k: (type(k).__name__, str(k))):
        errors.append(_error("features." + str(key), UNKNOWN_FIELD))

    return request_id, normalized, errors


def validate_normalize_request(request):
    try:
        request_id, normalized, errors = _validate(request)
    except Exception:  # rede de segurança: a função nunca lança exceção
        return {
            "ok": False,
            "request_id": None,
            "errors": [_error("request", INVALID_TYPE)],
        }

    if errors:
        return {"ok": False, "request_id": request_id, "errors": errors}

    return {
        "ok": True,
        "request_id": request_id,
        "features": {name: normalized[name] for name in SCHEMA_ORDER},
    }
