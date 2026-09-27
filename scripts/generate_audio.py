#!/usr/bin/env python3
import asyncio
import json
import shutil
from pathlib import Path

import edge_tts

VOICE = "es-ES-ElviraNeural"
RATE = "-10%"
ROOT = Path(__file__).resolve().parents[1]
AUDIO_ROOT = ROOT / "dist" / "audio"
LOCALE_ROOT = AUDIO_ROOT / "es-ES"
NUMBERS_ROOT = LOCALE_ROOT / "numbers"
PHRASES_ROOT = LOCALE_ROOT / "phrases"
MANIFEST_PATH = AUDIO_ROOT / "manifest.json"

SPECIAL = [
    "cero","uno","dos","tres","cuatro","cinco","seis","siete","ocho","nueve",
    "diez","once","doce","trece","catorce","quince","dieciséis","diecisiete",
    "dieciocho","diecinueve","veinte","veintiuno","veintidós","veintitrés",
    "veinticuatro","veinticinco","veintiséis","veintisiete","veintiocho","veintinueve",
]
TENS = ["", "", "", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]

PHRASES = {
    "¿Cuántas naranjas hay?": "cuantas-naranjas-hay",
    "¿Cuántas berenjenas hay?": "cuantas-berenjenas-hay",
    "¿Cuántas cerezas hay?": "cuantas-cerezas-hay",
    "¿Cuántas zanahorias hay?": "cuantas-zanahorias-hay",
    "¿Cuántos pepinos hay?": "cuantos-pepinos-hay",
    "Hay nueve.": "hay-nueve",
    "Hay tres.": "hay-tres",
    "Hay ocho.": "hay-ocho",
    "Hay siete.": "hay-siete",
    "un tomate": "un-tomate",
    "una naranja": "una-naranja",
    "un pepino": "un-pepino",
    "una berenjena": "una-berenjena",
    "una zanahoria": "una-zanahoria",
    "una cereza": "una-cereza",
}

def spanish_number(n: int) -> str:
    if n == 100:
        return "cien"
    if n < 30:
        return SPECIAL[n]
    tens = TENS[n // 10]
    return tens if n % 10 == 0 else f"{tens} y {SPECIAL[n % 10]}"

async def synthesize(text: str, target: Path, semaphore: asyncio.Semaphore) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    async with semaphore:
        last_error = None
        for attempt in range(1, 4):
            try:
                communicate = edge_tts.Communicate(text=text, voice=VOICE, rate=RATE)
                await communicate.save(str(target))
                if target.exists() and target.stat().st_size > 0:
                    print(f"generated {target.relative_to(ROOT)} <- {text}")
                    return
            except Exception as exc:
                last_error = exc
            await asyncio.sleep(attempt * 2)
        raise RuntimeError(f"failed to generate {text!r}: {last_error}")

async def main() -> None:
    voices = await edge_tts.list_voices()
    available = {voice.get("ShortName") for voice in voices}
    if VOICE not in available:
        raise RuntimeError(f"required voice {VOICE} is unavailable")

    if LOCALE_ROOT.exists():
        shutil.rmtree(LOCALE_ROOT)
    NUMBERS_ROOT.mkdir(parents=True, exist_ok=True)
    PHRASES_ROOT.mkdir(parents=True, exist_ok=True)

    semaphore = asyncio.Semaphore(4)
    tasks = []
    number_manifest = {}
    phrase_manifest = {}

    for n in range(101):
        path = NUMBERS_ROOT / f"{n}.mp3"
        tasks.append(synthesize(spanish_number(n), path, semaphore))
        number_manifest[str(n)] = f"/audio/es-ES/numbers/{n}.mp3"

    # Reuse the number 1 audio for the standalone "uno" phrase.
    phrase_manifest["uno"] = "/audio/es-ES/numbers/1.mp3"

    for text, slug in PHRASES.items():
        path = PHRASES_ROOT / f"{slug}.mp3"
        tasks.append(synthesize(text, path, semaphore))
        phrase_manifest[text] = f"/audio/es-ES/phrases/{slug}.mp3"

    await asyncio.gather(*tasks)

    manifest = {
        "meta": {
            "locale": "es-ES",
            "voice": VOICE,
            "rate": RATE,
            "generator": "edge-tts 7.2.8",
        },
        "numbers": number_manifest,
        "phrases": phrase_manifest,
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    expected = 101 + len(PHRASES)
    generated = list(LOCALE_ROOT.rglob("*.mp3"))
    if len(generated) != expected:
        raise RuntimeError(f"expected {expected} mp3 files, found {len(generated)}")

    print(f"generated {len(generated)} mp3 files with {VOICE} at {RATE}")

if __name__ == "__main__":
    asyncio.run(main())
