import math

FIELDS = ("age", "income", "country")


def _err(field, code):
    return {"field": field, "code": code}


def _check(name, v):
    """Valida um campo presente. Devolve (valor_normalizado, codigo_de_erro)."""
    if v is None:
        return None, "null"
    if name == "country":
        if not isinstance(v, str):
            return None, "invalid_type"
        v = v.strip().upper()
        return (v, None) if v else (None, "empty")
    # age só aceita int; income aceita int ou float. bool nunca é número aqui.
    if isinstance(v, bool) or not isinstance(v, int if name == "age" else (int, float)):
        return None, "invalid_type"
    if isinstance(v, float) and not math.isfinite(v):
        return None, "not_finite"
    if v < 0 or (name == "age" and v > 120):
        return None, "out_of_range"
    return v, None


def validate_normalize_request(request):
    rid = None
    try:
        if not isinstance(request, dict):
            return {"ok": False, "request_id": None, "errors": [_err("request", "invalid_type")]}
        rid = request.get("request_id")

        if "features" not in request:
            errors = [_err("features", "missing")]
        elif request["features"] is None:
            errors = [_err("features", "null")]
        elif not isinstance(request["features"], dict):
            errors = [_err("features", "invalid_type")]
        else:
            f, errors, out = request["features"], [], {}
            for name in FIELDS:
                field = "features." + name
                if name not in f:
                    errors.append(_err(field, "missing"))
                    continue
                value, code = _check(name, f[name])
                if code:
                    errors.append(_err(field, code))
                    continue
                out[name] = value
                # regra entre campos: só com age e income válidos, na posição de income
                if name == "income" and "age" in out and out["age"] < 16 and value != 0:
                    errors.append(_err(field, "consistency"))

            unknown = sorted((k for k in f if k not in FIELDS), key=lambda k: (type(k).__name__, str(k)))
            errors += [_err(f"features.{k}", "unknown_field") for k in unknown]
            if not errors:
                return {"ok": True, "request_id": rid, "features": out}

        return {"ok": False, "request_id": rid, "errors": errors}
    except Exception:  # nunca lança exceção
        return {"ok": False, "request_id": rid, "errors": [_err("request", "invalid_type")]}
