FIELDS = ("age", "income", "country")


def _error(field, code):
    return {"field": field, "code": code}


def _fail(request_id, errors):
    return {"ok": False, "request_id": request_id, "errors": errors}


def _as_dict(obj):
    """Converte dict (ou parecido) ou objeto com atributos em um dict novo. Senão, None."""
    if isinstance(obj, (str, bytes)):
        return None
    if hasattr(obj, "keys"):
        return dict(obj)
    if hasattr(obj, "__dict__"):
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
    req = _as_dict(request)
    if req is None:
        return _fail(None, [_error("request", "invalid_type")])

    request_id = req.get("request_id")  # repassado sem validar

    if "features" not in req:
        return _fail(request_id, [_error("features", "missing")])
    if req["features"] is None:
        return _fail(request_id, [_error("features", "null")])
    features = _as_dict(req["features"])
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


def validate_normalize_request(request):
    try:
        return _validate(request)
    except Exception:  # a função nunca lança exceção
        return _fail(None, [_error("request", "invalid_type")])
