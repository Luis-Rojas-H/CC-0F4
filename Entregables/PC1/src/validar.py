from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

RAIZ = Path(__file__).resolve().parents[1]
SCHEMA_PATH = RAIZ / "schema" / "salida_elegibilidad.json"
PRUEBAS_PATH = RAIZ / "schema" / "pruebas_a_mano.json"

def cargar_schema(path: Path = SCHEMA_PATH) -> Draft202012Validator:
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)

def evaluar_salida(
    texto: str,
    gold: str,
    validador: Draft202012Validator,
) -> dict[str, Any]:
    try:
        parsed = json.loads(texto)
    except json.JSONDecodeError:
        return {
            "parseable": False,
            "schema_valido": False,
            "etiqueta_correcta": None,
            "label": None,
        }

    schema_valido = validador.is_valid(parsed)
    if not schema_valido:
        return {
            "parseable": True,
            "schema_valido": False,
            "etiqueta_correcta": None,
            "label": parsed.get("label") if isinstance(parsed, dict) else None,
        }

    return {
        "parseable": True,
        "schema_valido": True,
        "etiqueta_correcta": parsed["label"] == gold,
        "label": parsed["label"],
    }

def correr_pruebas_a_mano(
    validador: Draft202012Validator,
    path: Path = PRUEBAS_PATH,
) -> list[dict[str, Any]]:
    pruebas = json.loads(path.read_text(encoding="utf-8"))
    informe = []
    for prueba in pruebas:
        obtenido = evaluar_salida(prueba["texto"], prueba["gold"], validador)
        esperado = prueba["esperado"]
        coincide = all(obtenido[clave] == esperado[clave] for clave in esperado)
        informe.append(
            {
                "nombre": prueba["nombre"],
                "caso": prueba["caso"],
                "gold": prueba["gold"],
                "obtenido": obtenido,
                "esperado": esperado,
                "coincide": coincide,
            }
        )
    return informe

def main() -> int:
    validador = cargar_schema()
    informe = correr_pruebas_a_mano(validador)
    fallos = 0
    for item in informe:
        marca = "ok" if item["coincide"] else "fallo"
        if not item["coincide"]:
            fallos += 1
        print(
            f"{marca}  {item['nombre']}"
            f"  parseable={item['obtenido']['parseable']}"
            f"  schema_valido={item['obtenido']['schema_valido']}"
            f"  etiqueta_correcta={item['obtenido']['etiqueta_correcta']}"
        )
    if fallos:
        print(f"{fallos} prueba(s) no coinciden con lo esperado")
        return 1
    print(f"{len(informe)} pruebas a mano coinciden con lo esperado")
    return 0

if __name__ == "__main__":
    sys.exit(main())