#!/usr/bin/env python3
"""Generate static Spanish audio via authenticated Azure Speech REST API."""
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

VOICE = "es-ES-ElviraNeural"
RATE = "-10%"
FORMAT = "audio-24khz-160kbitrate-mono-mp3"
GENERATOR = "azure-speech-rest-v1"
ROOT = Path(__file__).resolve().parents[1]
AUDIO_ROOT = ROOT / "dist" / "audio"
MANIFEST_PATH = AUDIO_ROOT / "manifest.json"
REQUEST_INTERVAL = 3.2  # Stay under the F0 rate of 20 requests per minute.

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

def classroom_phrases() -> dict[str, str]:
    # Use the exact question/answer data displayed by the website.
    source = ROOT / "dist" / "people-content.js"
    program = source.read_text(encoding="utf-8") + "\nconsole.log(JSON.stringify(peopleProfiles.flatMap(p => [false,true].flatMap(t => peopleQuestions(p,t).flatMap(q => [q.question, q.alternative, ...q.answers.filter(a => !/[0-9]/.test(a))]).filter(Boolean)))));"
    result = subprocess.run(["node", "-e", program], check=True, capture_output=True, text=True)
    texts = json.loads(result.stdout)
    texts.append("¿Cuál es su número de teléfono?")
    return {text: "people-" + hashlib.sha256(text.encode()).hexdigest()[:20] for text in texts}

def credentials() -> tuple[str, str]:
    key = os.environ.get("AZURE_SPEECH_KEY", "").strip()
    region = os.environ.get("AZURE_SPEECH_REGION", "").strip().lower()
    if not key or not region:
        raise RuntimeError("Configure AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in GitHub Actions Secrets.")
    if not re.fullmatch(r"[a-z0-9-]+", region):
        raise RuntimeError("AZURE_SPEECH_REGION must be an Azure region code, not a URL or display name.")
    return key, region


def ssml(text: str) -> bytes:
    return (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="es-ES">'
            f'<voice name="{VOICE}"><prosody rate="{RATE}">{escape(text)}</prosody></voice></speak>').encode("utf-8")


def valid_mp3(data: bytes) -> bool:
    return len(data) > 100 and (data.startswith(b"ID3") or (data[0] == 0xff and data[1] & 0xe0 == 0xe0))


def synthesize(text: str, key: str, region: str, pace: list[float]) -> bytes:
    endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    for attempt in range(3):
        time.sleep(max(0, pace[0] - time.monotonic()))
        pace[0] = time.monotonic() + REQUEST_INTERVAL
        request = urllib.request.Request(endpoint, data=ssml(text), method="POST", headers={
            "Ocp-Apim-Subscription-Key": key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": FORMAT,
            "User-Agent": "hola-static-audio-generator",
        })
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read()
            if not valid_mp3(data):
                raise RuntimeError("Azure returned invalid or empty MP3 audio.")
            return data
        except urllib.error.HTTPError as error:
            status = error.code
            # Do not log response bodies or credentials.
            if status in (401, 403):
                raise RuntimeError(f"Azure Speech HTTP {status}: check the Speech resource key, matching region and network access settings.") from None
            if status != 429 and status < 500:
                raise RuntimeError(f"Azure Speech HTTP {status}: verify SSML and voice availability in this region.") from None
            if attempt == 2:
                raise RuntimeError(f"Azure Speech HTTP {status} after three attempts.") from None
            retry = error.headers.get("Retry-After", "") if error.headers else ""
            delay = max(10 * (attempt + 1), min(float(retry), 120)) if retry.isdigit() else 10 * (attempt + 1)
            time.sleep(delay)
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise RuntimeError("Azure Speech connection failed after three attempts.") from None
            time.sleep(10 * (attempt + 1))
    raise RuntimeError("Audio generation did not complete.")


def inventory() -> tuple[list[tuple[str, str]], dict, dict]:
    numbers = {str(n): f"/audio/es-ES/numbers/{n}.mp3" for n in range(101)}
    phrases = {text: f"/audio/es-ES/phrases/{slug}.mp3" for text, slug in {**PHRASES, **classroom_phrases()}.items()}
    jobs = [(spanish_number(n), numbers[str(n)]) for n in range(101)] + list(phrases.items())
    phrases["uno"] = numbers["1"]
    return jobs, numbers, phrases


def main() -> None:
    key, region = credentials()
    prior = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) if MANIFEST_PATH.exists() else {}
    meta = prior.get("meta", {})
    # Retain existing good Elvira recordings rather than spend quota regenerating them.
    reuse = meta.get("voice") == VOICE and meta.get("rate") == RATE and meta.get("generator") in ("edge-tts 7.2.8", GENERATOR)
    prior_urls = set(prior.get("numbers", {}).values()) | set(prior.get("phrases", {}).values())
    jobs, numbers, phrases = inventory()
    AUDIO_ROOT.mkdir(parents=True, exist_ok=True)
    generated, reused = 0, 0
    pace = [0.0]
    with tempfile.TemporaryDirectory(prefix="hola-audio-") as temporary:
        pending = []
        for text, url in jobs:
            target = ROOT / "dist" / url.lstrip("/")
            if reuse and url in prior_urls and target.is_file() and valid_mp3(target.read_bytes()):
                reused += 1
                continue
            data = synthesize(text, key, region, pace)
            stage = Path(temporary) / f"{generated}.mp3"
            stage.write_bytes(data)
            pending.append((stage, target))
            generated += 1
            print(f"generated {generated}: {text}", flush=True)
        # Publish the manifest only after every requested clip has succeeded.
        for stage, target in pending:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(stage.read_bytes())
    for url in set(numbers.values()) | set(phrases.values()):
        if not valid_mp3((ROOT / "dist" / url.lstrip("/")).read_bytes()):
            raise RuntimeError(f"Missing or invalid audio: {url}")
    manifest = {"meta": {"locale": "es-ES", "voice": VOICE, "rate": RATE, "generator": GENERATOR,
                         "reused_audio_generator": meta.get("reused_audio_generator", meta.get("generator")) if reused else None},
                "numbers": numbers, "phrases": phrases}
    staged_manifest = MANIFEST_PATH.with_suffix(".tmp")
    staged_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    staged_manifest.replace(MANIFEST_PATH)
    print(f"Completed: {generated} Azure clips generated, {reused} existing clips reused; all manifest files verified.")


if __name__ == "__main__":
    main()
