"""Estrae il testo che il lettore legge dal dizionario C di un edizione.py, senza eseguirlo."""
import ast, sys, json

def val(n):
    if isinstance(n, ast.Constant):
        return n.value
    if isinstance(n, ast.JoinedStr):
        return "".join(str(val(v)) if not isinstance(v, ast.FormattedValue) else "{…}" for v in n.values)
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
        a, b = val(n.left), val(n.right)
        if isinstance(a, str) and isinstance(b, str):
            return a + b
        return a if isinstance(a, str) else b
    if isinstance(n, ast.Dict):
        return {val(k) if k is not None else "**": val(v) for k, v in zip(n.keys, n.values)}
    if isinstance(n, (ast.List, ast.Tuple)):
        return [val(e) for e in n.elts]
    if isinstance(n, ast.UnaryOp) and isinstance(n.operand, ast.Constant):
        return -n.operand.value if isinstance(n.op, ast.USub) else n.operand.value
    return "<%s>" % ast.unparse(n)[:60]

def carica(path):
    t = ast.parse(open(path, encoding="utf-8").read())
    for node in t.body:
        if isinstance(node, ast.Assign) and any(isinstance(x, ast.Name) and x.id == "C" for x in node.targets):
            return val(node.value)
    raise SystemExit("C non trovato in " + path)

if __name__ == "__main__":
    C = carica(sys.argv[1])
    def schema(o, p="", depth=0):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, (dict, list)):
                    print("  " * depth + f"{k}: {type(v).__name__}[{len(v)}]")
                    if depth < 3: schema(v, p + "/" + str(k), depth + 1)
                else:
                    s = str(v)
                    print("  " * depth + f"{k}: {s[:90]!r}" + (f" …({len(s)})" if len(s) > 90 else ""))
        elif isinstance(o, list) and o:
            print("  " * depth + f"[0 di {len(o)}]")
            if isinstance(o[0], (dict, list)): schema(o[0], p, depth + 1)
            else: print("  " * (depth+1) + repr(str(o[0])[:90]))
    schema(C)
