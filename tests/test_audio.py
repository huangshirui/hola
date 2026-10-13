import importlib.util
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('audio', Path(__file__).parents[1] / 'scripts/generate_audio.py')
audio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audio)
MP3 = b'ID3' + b'a' * 150

class AudioTests(unittest.TestCase):
    def test_credentials_fail_without_leaking_key(self):
        with patch.dict(os.environ, {'AZURE_SPEECH_KEY': 'private', 'AZURE_SPEECH_REGION': 'https://bad.example'}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'region code') as result:
                audio.credentials()
            self.assertNotIn('private', str(result.exception))
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'Configure'):
                audio.credentials()

    def test_ssml_escaping_and_mp3_validation(self):
        self.assertIn(b'A &amp; B &lt;C&gt;', audio.ssml('A & B <C>'))
        self.assertIn(b'es-ES-ElviraNeural', audio.ssml('uno'))
        self.assertTrue(audio.valid_mp3(MP3))
        self.assertFalse(audio.valid_mp3(b'<html>error</html>'))
        self.assertFalse(audio.valid_mp3(b''))

    def test_auth_failure_not_retried_or_printed(self):
        error = urllib.error.HTTPError('https://endpoint',401,'unauthorized',{},None)
        with patch.object(audio.urllib.request, 'urlopen', side_effect=error) as request, patch.object(audio.time,'sleep'):
            with self.assertRaisesRegex(RuntimeError, '401') as result:
                audio.synthesize('uno','secret-key','eastasia',[0])
            self.assertNotIn('secret-key',str(result.exception))
            self.assertEqual(request.call_count,1)
            self.assertEqual(request.call_args.args[0].headers['Ocp-apim-subscription-key'],'secret-key')

    def test_failure_preserves_existing_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); manifest=root/'dist/audio/manifest.json';manifest.parent.mkdir(parents=True);manifest.write_text('{"original":true}')
            with patch.object(audio,'ROOT',root), patch.object(audio,'AUDIO_ROOT',manifest.parent), patch.object(audio,'MANIFEST_PATH',manifest), patch.object(audio,'credentials',return_value=('key','eastasia')), patch.object(audio,'inventory',return_value=([('uno','/audio/1.mp3')],{'1':'/audio/1.mp3'},{})), patch.object(audio,'synthesize',side_effect=RuntimeError('failed')):
                with self.assertRaisesRegex(RuntimeError,'failed'): audio.main()
            self.assertEqual(manifest.read_text(),'{"original":true}')
            self.assertFalse((root/'dist/audio/1.mp3').exists())

    def test_inventory_covers_all_classroom_utterances(self):
        jobs,numbers,phrases=audio.inventory()
        self.assertEqual(len(numbers),101)
        self.assertIn('Me llamo Lucía.',phrases)
        self.assertIn('Se llama Lucía.',phrases)
        self.assertIn('Tengo doce años.',phrases)
        self.assertEqual(phrases['uno'],numbers['1'])
        self.assertEqual(len(jobs),205)

if __name__ == '__main__': unittest.main()
