(() => {
  const SDK = window.SpeechSDK;
  const LANGUAGE = 'es-ES';
  const TOKEN_URL = '/api/speech/token';
  const TOKEN_TTL_MS = 8 * 60 * 1000;
  const nativeRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;
  let cachedToken = null;
  let cachedTokenAt = 0;

  function makeError(code, message) {
    const error = new Error(message || code);
    error.code = code;
    return error;
  }

  function mapError(error) {
    if (error?.code) return error.code;
    const text = String(error?.message || error || '').toLowerCase();
    if (text.includes('permission') || text.includes('notallowed') || text.includes('not allowed') || text.includes('denied')) return 'not-allowed';
    if (text.includes('microphone') || text.includes('audio input') || text.includes('audio device')) return 'audio-capture';
    if (text.includes('language')) return 'language-not-supported';
    if (text.includes('abort')) return 'aborted';
    return 'network';
  }

  async function getSpeechToken(signal) {
    if (cachedToken && Date.now() - cachedTokenAt < TOKEN_TTL_MS) return cachedToken;
    const response = await fetch(TOKEN_URL, {
      cache: 'no-store',
      headers: { Accept: 'application/json' },
      signal,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw makeError('network', body.error || `speech_token_${response.status}`);
    }
    const body = await response.json();
    if (!body.token || !body.region) throw makeError('network', 'speech_token_invalid');
    cachedToken = { token: body.token, region: body.region };
    cachedTokenAt = Date.now();
    return cachedToken;
  }

  function patchSpeechCopy() {
    const numberHint = [...document.querySelectorAll('.hint')].find((el) => el.textContent.includes('语音反馈依据浏览器'));
    if (numberHint) {
      numberHint.textContent = '语音反馈使用 Azure Speech（es-ES）识别结果，不是专业发音评分。本站不保存录音或答案。';
    }

    for (const hint of document.querySelectorAll('.hint')) {
      if (hint.textContent.includes('浏览器识别结果仅供练习参考')) {
        hint.textContent = hint.textContent.replace(
          '浏览器识别结果仅供练习参考，不是专业发音评分；语音服务可能处理音频，本站不保存录音或答案。',
          'Azure Speech（es-ES）识别结果仅供练习参考，不是专业发音评分；语音会发送至 Azure 进行识别，本站不保存录音或答案。',
        );
      }
    }
  }

  const observer = new MutationObserver(() => patchSpeechCopy());
  if (document.body) observer.observe(document.body, { childList: true, subtree: true, characterData: true });
  queueMicrotask(patchSpeechCopy);

  class AzureSpeechRecognition {
    constructor() {
      this.lang = LANGUAGE;
      this.interimResults = false;
      this.maxAlternatives = 1;
      this.continuous = false;
      this.onresult = null;
      this.onerror = null;
      this.onend = null;
      this._running = false;
      this._finished = false;
      this._controller = null;
      this._recognizer = null;
      this._audioConfig = null;
    }

    start() {
      if (this._running) throw new DOMException('Speech recognition has already started.', 'InvalidStateError');
      this._running = true;
      this._finished = false;
      this._controller = new AbortController();
      this._startAsync();
    }

    stop() {
      if (!this._running) return;
      this._cancel(false);
    }

    abort() {
      if (!this._running) return;
      this._cancel(true);
    }

    async _startAsync() {
      try {
        if (!SDK) throw makeError('network', 'azure_speech_sdk_not_loaded');
        const { token, region } = await getSpeechToken(this._controller.signal);
        if (!this._running) return;

        const speechConfig = SDK.SpeechConfig.fromAuthorizationToken(token, region);
        speechConfig.speechRecognitionLanguage = LANGUAGE;
        const audioConfig = SDK.AudioConfig.fromDefaultMicrophoneInput();
        const recognizer = new SDK.SpeechRecognizer(speechConfig, audioConfig);
        this._audioConfig = audioConfig;
        this._recognizer = recognizer;

        recognizer.recognizeOnceAsync(
          (result) => this._handleResult(result),
          (error) => this._handleFailure(error),
        );
      } catch (error) {
        if (error?.name === 'AbortError' || !this._running) return;
        this._emitError(mapError(error), String(error?.message || error || 'speech_error'));
        this._finish();
      }
    }

    _handleResult(result) {
      if (!this._running || this._finished) return;
      if (result.reason === SDK.ResultReason.RecognizedSpeech && String(result.text || '').trim()) {
        const alternatives = [{ transcript: String(result.text).trim(), confidence: 1 }];
        this.onresult?.({ results: [alternatives], resultIndex: 0 });
      } else if (result.reason === SDK.ResultReason.NoMatch) {
        this._emitError('no-speech', 'Azure Speech did not recognize speech.');
      } else if (result.reason === SDK.ResultReason.Canceled) {
        const details = SDK.CancellationDetails.fromResult(result);
        if (details.reason === SDK.CancellationReason.Error) cachedToken = null;
        this._emitError(mapError(details.errorDetails || details.reason), details.errorDetails || String(details.reason));
      } else {
        this._emitError('no-speech', 'Azure Speech returned no recognized text.');
      }
      this._finish();
    }

    _handleFailure(error) {
      if (!this._running || this._finished) return;
      cachedToken = null;
      this._emitError(mapError(error), String(error || 'speech_error'));
      this._finish();
    }

    _emitError(code, message) {
      this.onerror?.({ error: code, message });
    }

    _cancel(aborted) {
      this._running = false;
      this._controller?.abort();
      if (aborted) this._emitError('aborted', 'Speech recognition aborted.');
      this._finish();
    }

    _finish() {
      if (this._finished) return;
      this._finished = true;
      this._running = false;
      this._controller = null;
      try { this._recognizer?.close(); } catch {}
      try { this._audioConfig?.close(); } catch {}
      this._recognizer = null;
      this._audioConfig = null;
      queueMicrotask(() => {
        patchSpeechCopy();
        this.onend?.({});
        queueMicrotask(patchSpeechCopy);
      });
    }
  }

  window.__HOLA_SPEECH_PROVIDER__ = Object.freeze({
    provider: 'azure-speech-sdk',
    language: LANGUAGE,
    nativeWebSpeechAvailable: Boolean(nativeRecognition),
  });
  window.__HOLA_NATIVE_SPEECH_RECOGNITION__ = nativeRecognition;
  window.SpeechRecognition = AzureSpeechRecognition;
  window.webkitSpeechRecognition = AzureSpeechRecognition;
})();
