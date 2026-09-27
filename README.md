# ¡Hola! 西语练习室

面向中国小朋友的西班牙语练习网站。无需注册，不保存个人练习记录。

## 功能

- 数字 0–100：听读、口语识别、拼写和听音辨数。
- 数字应用：看图数蔬果，以及 uno / un / una 练习。
- 适配桌面、平板和手机。

## 本地运行

在项目目录执行 `python -m http.server 8000 --directory dist`，然后打开 http://localhost:8000 。

## Cloudflare Pages

网站为原生 HTML、CSS、JavaScript，无构建依赖、数据库或 OpenAI API。

连接 GitHub 仓库后选择 main 分支，框架选择 None，构建命令留空，输出目录设置为 dist。也可以直接上传 dist 目录中的文件。

自定义域名需要在 Pages 项目内添加并按控制台提示设置 DNS。当前迁移仅准备源码，不修改现有站点的域名或部署。

## 外部依赖

- Google Fonts：字体无法加载时使用系统字体。后续可本地化。
- 固定朗读音频：`dist/audio/manifest.json` 可把数字或固定短句映射到站点内 MP3/Opus。存在映射时优先播放固定音频，以保证 iPhone/Android 发音一致。
- speechSynthesis：仅作为固定音频缺失时的兜底。代码只选择设备提供的西班牙语 voice；找不到西班牙语 voice 时停止播放，不降级到英语或系统默认 voice。
- SpeechRecognition：始终请求 `es-ES`。实际识别仍由浏览器/系统语音服务完成，支持程度、口音模型和网络可用性因设备而异，识别结果不是专业发音评分。

本站不保存录音或答案，不代表浏览器语音服务不处理音频。

## 教学图片

`dist/assets/` 中五张蔬果图片来自用户提供的课堂材料。其权利归原权利人所有，不能视为项目代码许可证授权的素材；重新分发或用于其他用途前应确认相应权限。

## 开源许可

项目代码采用 MIT License；课堂材料图片不属于 MIT 授权范围，详见上方教学图片说明。


## 固定朗读音频

标准音频放在 `dist/audio/` 下，并在 `dist/audio/manifest.json` 中登记。例如：

```json
{
  "numbers": {
    "23": "/audio/es-ES/numbers/23.mp3"
  },
  "phrases": {
    "una naranja": "/audio/es-ES/phrases/una-naranja.mp3"
  }
}
```

播放顺序为：站点固定音频 → 设备上的西班牙语 voice → 无可用西班牙语 voice 时停止并提示。不要配置英语 TTS 作为兜底。
