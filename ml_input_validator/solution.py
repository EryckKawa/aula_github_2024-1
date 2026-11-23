CAMPOS = ("age", "income", "country")


def falha(rid, erros):
    return {"ok": False, "request_id": rid, "errors": erros}


def erro(campo, codigo):
    return {"field": campo, "code": codigo}


def checar(nome, v):
    if v is None:
        return "null"
    if nome == "country":
        if type(v) != str:
            return "invalid_type"
        if v.strip() == "":
            return "empty"
        return None
    if nome == "age" and type(v) != int:
        return "invalid_type"
    if type(v) not in (int, float):
        return "invalid_type"
    if v != v or v in (float("inf"), float("-inf")):
        return "not_finite"
    if v < 0 or (nome == "age" and v > 120):
        return "out_of_range"
    return None


def validate_and_normalize(request):
    rid = None
    try:
        rid = request.get("request_id")
        if "features" not in request:
            return falha(rid, [erro("features", "missing")])
        f = request["features"]
        if f is None:
            return falha(rid, [erro("features", "null")])
        if type(f) != dict:
            return falha(rid, [erro("features", "invalid_type")])
        erros = []
        out = {}
        for nome in CAMPOS:
            campo = "features." + nome
            if nome not in f:
                erros.append(erro(campo, "missing"))
                continue
            cod = checar(nome, f[nome])
            if cod:
                erros.append(erro(campo, cod))
                continue
            out[nome] = f[nome]
            if nome == "country":
                out[nome] = f[nome].strip().upper()
            if nome == "income" and "age" in out:
                if out["age"] < 16 and f[nome] != 0:
                    erros.append(erro(campo, "consistency"))
        for k in f:
            if k not in CAMPOS:
                erros.append(erro("features." + str(k), "unknown_field"))
        if erros:
            return falha(rid, erros)
        return {"ok": True, "request_id": rid, "features": out}
    except Exception:
        return falha(rid, [erro("request", "invalid_type")])
