#!/usr/bin/env python3
# ============================================================================
# OpenRouter Writing Tools - PopClip extension
# 7 AI writing tasks via OpenRouter (OpenAI + Gemini models).
#
# Reads:   POPCLIP_TEXT, POPCLIP_OPTION_*, JL_TASK
# Writes:  transformed text to stdout (PopClip pastes it via after: paste-result)
# Errors:  to stderr + exit 1 (PopClip shows a failure indicator)
# ============================================================================

import json
import os
import sys
import urllib.error
import urllib.request

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
HTTP_REFERER = "https://github.com/usblsb/popclip-openrouter-writing-tools"
X_TITLE = "OpenRouter Writing Tools (PopClip)"
HTTP_TIMEOUT_SECONDS = 60

# ----------------------------------------------------------------------------
# System prompts (one per task)
# ----------------------------------------------------------------------------
SYSTEM_PROMPTS = {
    "corregir": (
        "Eres un corrector de textos profesional. Recibes texto del usuario y "
        "devuelves SOLO el texto corregido, aplicando estas reglas estrictas:\n"
        "\n"
        "1. Corrige ortografia, gramatica, puntuacion y tildes.\n"
        "2. NO cambies el contenido, ni el tono, ni la estructura.\n"
        "3. NO reformules ni mejores el estilo. Solo corrige errores.\n"
        "4. Conserva el idioma original (a menos que el usuario indique otro idioma de respuesta).\n"
        "5. NO uses Markdown ni HTML.\n"
        "6. Devuelve UNICAMENTE el texto corregido. Sin meta-comentarios."
    ),

    "traducir": (
        "Eres un traductor profesional. Traduce el texto del usuario al idioma "
        "indicado, manteniendo:\n"
        "\n"
        "1. El significado completo y los matices.\n"
        "2. El registro y tono original (formal, informal, tecnico, coloquial...).\n"
        "3. Los nombres propios sin traducir.\n"
        "4. La estructura del texto (parrafos, listas si las hay).\n"
        "\n"
        "Reglas estrictas:\n"
        "- NO uses Markdown ni HTML.\n"
        "- NO incluyas el texto original ni explicaciones.\n"
        "- Devuelve UNICAMENTE la traduccion."
    ),

    "resumir": (
        "Eres un especialista en sintesis de informacion. Resume el texto del "
        "usuario manteniendo:\n"
        "\n"
        "1. Las ideas principales y conclusiones.\n"
        "2. Los datos cuantitativos clave (cifras, fechas, nombres).\n"
        "3. El tono original.\n"
        "\n"
        "Formato:\n"
        "- Si el texto es corto o medio: resumen en 1-3 frases.\n"
        "- Si el texto es largo: resumen en bullets cortos con guiones (- ).\n"
        "\n"
        "Reglas estrictas:\n"
        "- NO incluyas opiniones ni interpretaciones nuevas.\n"
        "- NO anadas introducciones tipo 'El texto trata de...'.\n"
        "- Devuelve UNICAMENTE el resumen."
    ),

    "email": (
        "Eres un editor profesional de textos. Tu tarea es reescribir el texto "
        "del usuario para mejorarlo manteniendo SIEMPRE su intencion original. "
        "Aplica estas reglas estrictas:\n"
        "\n"
        "1. Conserva el significado completo. No omitas informacion sustancial.\n"
        "2. Reordena el contenido si la estructura es confusa, agrupando ideas relacionadas.\n"
        "3. Elimina coletillas, muletillas y expresiones de relleno (ej: 'como ya he comentado', "
        "'por asi decirlo', 'obviamente', 'creo que', 'la verdad es que', 'por cierto', 'en mi opinion personal').\n"
        "4. Detecta repeticiones de la misma idea o conceptos muy similares y consolidalos en una sola exposicion clara.\n"
        "5. Usa frases cortas y directas cuando sea posible, sin perder matices.\n"
        "6. Mantiene el tono original del autor (formal, informal, profesional, coloquial...).\n"
        "7. Conserva el idioma original del texto.\n"
        "8. NO anadas saludos, despedidas o firmas que no esten en el original.\n"
        "9. NO uses Markdown ni HTML. Devuelve solo texto plano.\n"
        "10. NO incluyas explicaciones, comentarios ni introducciones. Devuelve UNICAMENTE el texto reescrito."
    ),

    "contenido": (
        "Eres un editor de contenidos profesional. Recibes varios fragmentos de "
        "texto que el usuario ha pegado juntos (notas sueltas, parrafos copiados "
        "de distintas fuentes, apuntes desordenados) y tu tarea es **unificarlos "
        "en un documento coherente y bien estructurado**, destacando los "
        "elementos importantes.\n"
        "\n"
        "Reglas estrictas:\n"
        "\n"
        "1. Identifica el tema o temas principales del conjunto.\n"
        "2. Reorganiza los fragmentos en un orden logico (introduccion -> desarrollo -> conclusiones, "
        "o por importancia, o por afinidad de tema).\n"
        "3. Fusiona ideas duplicadas y elimina contradicciones evidentes.\n"
        "4. Anade frases de transicion suaves para que la lectura fluya como un solo documento.\n"
        "5. **Destaca los elementos principales en negrita Markdown** (**texto**): "
        "nombres clave, conceptos centrales, decisiones, datos numericos importantes, fechas, entidades.\n"
        "6. Cuando haya enumeraciones naturales, usalas con guiones (- item) o numeradas (1. item).\n"
        "7. Conserva el tono original (tecnico, divulgativo, informal...).\n"
        "8. Conserva el idioma del texto original.\n"
        "9. NO inventes informacion que no este en los fragmentos. Si hay huecos, no los rellenes.\n"
        "10. NO uses HTML ni headings Markdown (#, ##...) - solo texto plano con **bold** y listas.\n"
        "11. Devuelve UNICAMENTE el documento reescrito. Sin introducciones ni meta-comentarios."
    ),

    "html": (
        "Eres un formateador HTML semantico. Recibes texto plano y devuelves "
        "HTML estructurado SOLO con estas etiquetas permitidas:\n"
        "\n"
        "- <h2>, <h3>, <h4> para jerarquia de secciones\n"
        "- <p> para parrafos\n"
        "- <ol> con <li> para listas numeradas\n"
        "- <ul> con <li> para listas no ordenadas\n"
        "- <strong> para negrita\n"
        "- <u> para subrayado\n"
        "\n"
        "Reglas estrictas:\n"
        "\n"
        "1. NO uses ninguna otra etiqueta HTML (ni <html>, <body>, <div>, <span>, "
        "<em>, <i>, <b>, <a>, <code>, <pre>, <br>, <hr>, <h1>, <h5>, <h6>, <blockquote>, <table>...).\n"
        "2. NO uses atributos (ni class, ni id, ni style).\n"
        "3. NO anadas el doctype, <html>, <head> ni <body>.\n"
        "4. NO uses bloques de codigo Markdown (```html). Devuelve HTML puro.\n"
        "5. Detecta la jerarquia natural del texto y aplicala con h2/h3/h4.\n"
        "6. Convierte enumeraciones evidentes (1., 2., 3., o 'primero/segundo/tercero') en <ol><li>.\n"
        "7. Convierte listas con guiones, asteriscos o naturales en <ul><li>.\n"
        "8. Resalta terminos clave o importantes con <strong>.\n"
        "9. Usa <u> solo cuando algo necesite enfasis especial diferente al de negrita.\n"
        "10. Mantén el contenido integro: no resumas, no elimines, no parafrasees.\n"
        "11. Conserva el idioma original.\n"
        "12. Devuelve UNICAMENTE el HTML, sin texto explicativo previo o posterior."
    ),

    "md": (
        "Eres un formateador Markdown. Recibes texto plano y devuelves Markdown "
        "estructurado SOLO con esta sintaxis permitida:\n"
        "\n"
        "- ## para encabezados nivel 2\n"
        "- ### para encabezados nivel 3\n"
        "- #### para encabezados nivel 4\n"
        "- Parrafos como texto plano separado por linea en blanco\n"
        "- Listas numeradas con '1. ', '2. ', '3. '...\n"
        "- Listas con guiones '- '\n"
        "- **texto** para negrita\n"
        "- <u>texto</u> (HTML inline) para subrayado\n"
        "\n"
        "Reglas estrictas:\n"
        "\n"
        "1. NO uses # (H1) ni ##### (H5) ni ###### (H6).\n"
        "2. NO uses tablas, codigo (```), enlaces, imagenes, blockquotes (>), HR (---).\n"
        "3. NO uses cursiva (*texto* o _texto_).\n"
        "4. NO uses ninguna etiqueta HTML excepto <u>...</u> para subrayado.\n"
        "5. Detecta la jerarquia natural del texto y aplicala con ##, ###, ####.\n"
        "6. Convierte enumeraciones numeradas en '1. ', listas naturales en '- '.\n"
        "7. Resalta terminos clave o importantes con **bold**.\n"
        "8. Usa <u>...</u> solo cuando algo necesite enfasis especial diferente al de negrita.\n"
        "9. Mantén el contenido integro: no resumas, no elimines, no parafrasees.\n"
        "10. Conserva el idioma original.\n"
        "11. Devuelve UNICAMENTE el Markdown, sin texto explicativo previo o posterior."
    ),
}

# ----------------------------------------------------------------------------
# Per-task settings (model + temperature + max_tokens)
# ----------------------------------------------------------------------------
TASKS = {
    "corregir":  {"model": "openai/gpt-4o-mini",       "temperature": 0.1, "max_tokens": 800},
    "traducir":  {"model": "google/gemini-2.5-flash",  "temperature": 0.2, "max_tokens": 2000},
    "resumir":   {"model": "openai/gpt-4o-mini",       "temperature": 0.3, "max_tokens": 800},
    "email":     {"model": "google/gemini-2.5-pro",    "temperature": 0.4, "max_tokens": 2000},
    "contenido": {"model": "openai/gpt-4o",            "temperature": 0.5, "max_tokens": 4000},
    "html":      {"model": "openai/gpt-4o",            "temperature": 0.2, "max_tokens": 8000},
    "md":        {"model": "openai/gpt-4o",            "temperature": 0.2, "max_tokens": 8000},
}

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def fail(msg, code=1):
    sys.stderr.write(msg + "\n")
    sys.exit(code)

def build_user_prompt(task, text, idioma_respuesta, idioma_traducir):
    """Wrap the selected text with task-specific instructions."""
    if task == "traducir":
        return (
            f"Translate the following text into {idioma_traducir}. "
            f"Return only the translation, nothing else.\n\n"
            f"---\n{text}\n---"
        )

    # All other tasks: respect language preference
    if idioma_respuesta and idioma_respuesta.lower() != "auto":
        lang_clause = (
            f"Importante: la respuesta debe estar en {idioma_respuesta} "
            f"independientemente del idioma del texto original.\n\n"
        )
    else:
        lang_clause = ""

    return f"{lang_clause}{text}"

def call_openrouter(api_key, model, system_prompt, user_prompt, temperature, max_tokens):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    req = urllib.request.Request(
        OPENROUTER_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
            "HTTP-Referer":  HTTP_REFERER,
            "X-Title":       X_TITLE,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        fail(f"OpenRouter HTTP {e.code}: {body[:500]}")
    except urllib.error.URLError as e:
        fail(f"Network error: {e.reason}")
    except Exception as e:
        fail(f"Unexpected error: {e}")

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        fail(f"Unexpected response shape: {json.dumps(data)[:500]}")

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    task = (os.environ.get("JL_TASK") or "").strip()
    if task not in TASKS:
        fail(f"Unknown JL_TASK '{task}'. Expected one of: {', '.join(TASKS)}")

    api_key = (os.environ.get("POPCLIP_OPTION_APIKEY") or "").strip()
    if not api_key:
        fail("Missing OpenRouter API Key. Configure it in PopClip > Extensions > OpenRouter Writing Tools.")

    text = os.environ.get("POPCLIP_TEXT") or ""
    if not text.strip():
        fail("No text selected.")

    idioma_respuesta = (os.environ.get("POPCLIP_OPTION_IDIOMA_RESPUESTA") or "auto").strip()
    idioma_traducir  = (os.environ.get("POPCLIP_OPTION_IDIOMA_TRADUCIR")  or "spanish").strip()

    cfg = TASKS[task]
    system_prompt = SYSTEM_PROMPTS[task]
    user_prompt   = build_user_prompt(task, text, idioma_respuesta, idioma_traducir)

    result = call_openrouter(
        api_key=api_key,
        model=cfg["model"],
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=cfg["temperature"],
        max_tokens=cfg["max_tokens"],
    )

    sys.stdout.write(result.rstrip("\n"))

if __name__ == "__main__":
    main()
