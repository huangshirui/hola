# ¡Hola! 西语练习室

面向中国小朋友的西班牙语练习网站。无需注册，不保存个人练习记录。

## 功能

- 主题 01「数字 0–100」：听读、口语识别、拼写和听音辨数。
- 数字应用：看图数蔬果，以及 uno / un / una 练习。
- 电话号码听力：逐位播放 9 位练习号码，保留前导 0，逐位核对答案。
- 主题 02「认识你和我」：虚构人物资料、问答听读、第一/第三人称口语与完整句子练习；覆盖姓名、父姓、母姓、年龄、国家、国籍、居住地与爱好。
- 适配桌面、平板和手机。

## 架构与部署

Hola 使用 Cloudflare Workers + Static Assets：

- `dist/`：浏览器静态页面、JavaScript、样式、图片与固定音频。
- `worker/index.js`：仅处理 `/api/*` 服务端接口，其余请求由 Static Assets 直接提供。
- `wrangler.jsonc`：Worker 与静态资源配置。
- GitHub `main` 分支推送后，由 Cloudflare Workers Builds 自动构建和部署；不使用 GitHub Actions 做 Cloudflare 部署。

Cloudflare Workers Builds 的 build command 为：

```sh
npm install --no-audit --no-fund && npm run build
```

`npm run build` 会把固定版本的 Azure Speech SDK browser bundle 和 `speech-processor.js` 从 npm 包复制到 `dist/vendor/`，因此用户运行时不依赖第三方 CDN。

本地开发先执行：

```sh
npm install
npm run build
python -m http.server 8000 --directory dist
```

然后打开 `http://localhost:8000`。仅测试静态页面时也可直接启动静态服务器，但口语识别需要 Worker 的 `/api/speech/token`。

## 语音识别（STT）

口语识别使用官方 `microsoft-cognitiveservices-speech-sdk` browser SDK，并固定识别语言为 `es-ES`。浏览器原生 `SpeechRecognition` / `webkitSpeechRecognition` 不作为静默 fallback，避免部分 Android/国产浏览器实际落到系统中文识别。

前端通过 `/api/speech/token` 获取 Azure Speech 短期 token；长期 Azure Key 只保存在 Cloudflare Worker Secret 中：

- `AZURE_SPEECH_KEY`
- `AZURE_SPEECH_REGION`

识别链路：浏览器麦克风 → Azure Speech SDK → Azure Speech（`es-ES`）。页面会在语音反馈中显示 `Azure Speech · es-ES`，便于确认当前识别来源。本站不保存录音或答案；语音会发送至 Azure 进行识别。识别结果仅用于练习反馈，不是专业发音评分。

## 固定朗读音频（TTS）

标准音频放在 `dist/audio/`，映射位于 `dist/audio/manifest.json`。播放顺序为：站点固定音频 → 设备上的西班牙语 voice → 无可用西班牙语 voice 时停止；不会降级到英语或系统默认 voice。

仓库使用 `scripts/generate_audio.py` 通过 Azure Speech REST API 生成固定朗读音频，当前使用西班牙女声 `es-ES-ElviraNeural`，语速 `-10%`。这部分仍由 `.github/workflows/generate-audio.yml` 执行，因为它负责生成内容并提交 MP3，不属于 Cloudflare 部署流程。

在 GitHub Actions Repository secrets 中配置：

- `AZURE_SPEECH_KEY`
- `AZURE_SPEECH_REGION`

工作流会复用已有同发音人、同语速且有效的音频，全部生成成功后才更新清单。Key 不写入网站或生成文件。

## 教学内容与图片

`dist/assets/` 中五张蔬果图片来自用户提供的课堂材料。其权利归原权利人所有，不属于项目 MIT 许可证授权的素材；重新分发或用于其他用途前应确认相应权限。

个人信息句型的数据位于 `dist/people-content.js`。练习人物均为虚构资料，不要求填写真实个人信息。

## 测试

```sh
node --check dist/app.js
node --check dist/azure-speech-recognition.js
npm test
```

## 开源许可

项目代码采用 MIT License；课堂材料图片不属于 MIT 授权范围。
