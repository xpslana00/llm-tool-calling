# LLM Tool Calling demo

Python skript, který zavolá LLM API (Google Gemini přes rozhraní kompatibilní s OpenAI), nechá model použít nástroj (výpočetní funkci) a výsledek vrátí zpět LLM, které vytvoří finální odpověď.

## Jak to funguje
1. Skript pošle dotaz uživatele modelu spolu s popisem nástrojů (`calculate`, `get_current_datetime`).
2. Model vrátí `tool_calls`, tedy požadavek na spuštění nástroje s argumenty.
3. Skript nástroj spustí lokálně (bezpečné vyhodnocení výrazu přes `ast`, bez `eval`).
4. Výsledek se pošle zpět modelu jako zpráva s rolí `tool`.
5. Model vrátí finální odpověď.

## Spuštění (Windows)
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env     # doplň svůj Gemini API klíč (https://aistudio.google.com/apikey)
.\.venv\Scripts\python.exe main.py "Kolik je 15 % z 2480 a odmocnina z 2025?"
```

## Ukázkový výstup
```
Otazka: Kolik je 15 % z 2480 a odmocnina z 2025?

[tool] calculate({'expression': '0.15 * 2480'}) -> {'expression': '0.15 * 2480', 'result': 372.0}
[tool] calculate({'expression': 'sqrt(2025)'}) -> {'expression': 'sqrt(2025)', 'result': 45.0}

Odpoved: 15 % z 2480 je 372. Odmocnina z 2025 je 45.
```