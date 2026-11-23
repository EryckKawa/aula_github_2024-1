FIELDS = ("age", "income", "country")


def _error(field, code):
    return {"field": field, "code": code}


def _fail(request_id, errors):
    return {"ok": False, "request_id": request_id, "errors": errors}


def _as_dict(obj):
    """Converte a entrada em um dict novo (a original nunca é alterada). Se não der, None.

    Aceita: dict (ou parecido), texto JSON de um objeto, namedtuple,
    dataclass (inclusive com slots) e objeto com atributos.
    """
    if isinstance(obj, bytes):
        obj = obj.decode("utf-8")
    if isinstance(obj, str):  # texto JSON, ex.: '{"request_id": "r1", ...}'
        import json
        obj = json.loads(obj)
        return obj if isinstance(obj, dict) else None
    if hasattr(obj, "keys"):  # dict, MappingProxy, UserDict...
        return dict(obj)
    if hasattr(obj, "_asdict"):  # namedtuple
        return dict(obj._asdict())
    if hasattr(obj, "__dataclass_fields__"):  # dataclass (com ou sem slots)
        return {k: getattr(obj, k) for k in obj.__dataclass_fields__}
    if hasattr(obj, "__dict__"):  # objeto comum com atributos
        return dict(vars(obj))
    return None


def _field_error(name, value):
    """Devolve o código de erro do campo, ou None se ele for válido."""
    if value is None:
        return "null"
    if name == "country":
        if not isinstance(value, str):
            return "invalid_type"
        return "empty" if not value.strip() else None
    # age: só int. income: int ou float. bool nunca vale como número.
    allowed = int if name == "age" else (int, float)
    if isinstance(value, bool) or not isinstance(value, allowed):
        return "invalid_type"
    if value != value or value in (float("inf"), float("-inf")):  # NaN, inf, -inf
        return "not_finite"
    if value < 0 or (name == "age" and value > 120):
        return "out_of_range"
    return None


def _validate(request):
    try:
        req = _as_dict(request)
    except Exception:  # ex.: texto que não é JSON
        req = None
    if req is None:
        return _fail(None, [_error("request", "invalid_type")])

    request_id = req.get("request_id")  # repassado sem validar

    if "features" not in req:
        return _fail(request_id, [_error("features", "missing")])
    if req["features"] is None:
        return _fail(request_id, [_error("features", "null")])
    try:
        features = _as_dict(req["features"])
    except Exception:
        features = None
    if features is None:
        return _fail(request_id, [_error("features", "invalid_type")])

    errors, out = [], {}
    for name in FIELDS:
        field = "features." + name
        code = "missing" if name not in features else _field_error(name, features[name])
        if code:
            errors.append(_error(field, code))
            continue
        value = features[name]
        out[name] = value.strip().upper() if name == "country" else value
        # menor de 16 anos precisa ter income 0 (só se age e income forem válidos)
        if name == "income" and "age" in out and out["age"] < 16 and value != 0:
            errors.append(_error(field, "consistency"))

    for key in sorted(str(k) for k in features if k not in FIELDS):
        errors.append(_error("features." + key, "unknown_field"))

    if errors:
        return _fail(request_id, errors)
    return {"ok": True, "request_id": request_id, "features": out}


DEBUG = True  # mude para False quando os testes passarem


def validate_normalize_request(request):
    try:
        result = _validate(request)
    except Exception:  # a função nunca lança exceção
        result = _fail(None, [_error("request", "invalid_type")])
    if DEBUG and not result["ok"]:
        # o pytest mostra isso em "Captured stdout" quando um teste falha
        print("DEBUG tipo recebido:", type(request).__name__, "| erros:", result["errors"])
    return result
