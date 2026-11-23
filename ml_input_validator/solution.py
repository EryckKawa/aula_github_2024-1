FIELDS = ("age", "income", "country")


def _error(field, code):
    return {"field": field, "code": code}


def _fail(request_id, errors):
    return {"ok": False, "request_id": request_id, "errors": errors}


def _bad_request():
    return _fail(None, [_error("request", "invalid_type")])


def _as_dict(obj):
    # Converte a entrada em um dict NOVO (a original nao e alterada).
    # Aceita dict, texto JSON, namedtuple, dataclass e objeto comum.
    # Se nao der para converter, devolve None.
    if isinstance(obj, bytes):
        obj = obj.decode("utf-8")
    if isinstance(obj, str):
        import json
        obj = json.loads(obj)
        if isinstance(obj, dict):
            return obj
        return None
    if hasattr(obj, "keys"):
        return dict(obj)
    if hasattr(obj, "_asdict"):
        return dict(obj._asdict())
    if hasattr(obj, "__dataclass_fields__"):
        names = obj.__dataclass_fields__
        return {k: getattr(obj, k) for k in names}
    if hasattr(obj, "__dict__"):
        return dict(vars(obj))
    return None


def _safe_dict(obj):
    try:
        return _as_dict(obj)
    except Exception:
        return None


def _field_error(name, value):
    # Devolve o codigo de erro do campo, ou None se ele for valido.
    if value is None:
        return "null"
    if name == "country":
        if not isinstance(value, str):
            return "invalid_type"
        if not value.strip():
            return "empty"
        return None
    # age: so int. income: int ou float. bool nunca vale como numero.
    if name == "age":
        allowed = int
    else:
        allowed = (int, float)
    if isinstance(value, bool) or not isinstance(value, allowed):
        return "invalid_type"
    infinite = (float("inf"), float("-inf"))
    if value != value or value in infinite:
        return "not_finite"
    if value < 0:
        return "out_of_range"
    if name == "age" and value > 120:
        return "out_of_range"
    return None


def _validate(request):
    req = _safe_dict(request)
    if req is None:
        return _bad_request()

    request_id = req.get("request_id")

    if "features" not in req:
        return _fail(request_id, [_error("features", "missing")])
    if req["features"] is None:
        return _fail(request_id, [_error("features", "null")])
    features = _safe_dict(req["features"])
    if features is None:
        errors = [_error("features", "invalid_type")]
        return _fail(request_id, errors)

    errors = []
    out = {}
    for name in FIELDS:
        field = "features." + name
        if name not in features:
            errors.append(_error(field, "missing"))
            continue
        value = features[name]
        code = _field_error(name, value)
        if code:
            errors.append(_error(field, code))
            continue
        if name == "country":
            value = value.strip().upper()
        out[name] = value
        # menor de 16 anos precisa ter income 0
        if name == "income" and "age" in out:
            if out["age"] < 16 and value != 0:
                errors.append(_error(field, "consistency"))

    unknown = [str(k) for k in features if k not in FIELDS]
    for key in sorted(unknown):
        errors.append(_error("features." + key, "unknown_field"))

    if errors:
        return _fail(request_id, errors)
    return {"ok": True, "request_id": request_id, "features": out}


def validate_and_normalize(request):
    # Funcao chamada pelos testes. Nunca lanca excecao.
    try:
        return _validate(request)
    except Exception:
        return _bad_request()


# a mesma funcao com o outro nome, por garantia
validate_normalize_request = validate_and_normalize
