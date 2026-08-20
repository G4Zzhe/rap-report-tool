# 如何获取酷狗/QQ音乐真实榜单 API

本工具目前对网易云音乐榜单已实现自动抓取，酷狗音乐和 QQ 音乐由于页面使用 JS 渲染或接口需要加密参数，需要使用者自行抓包获取真实 API 地址后填入 `config.yaml` 或 `config.local.yaml`。

## 酷狗音乐说唱先锋榜

### 步骤

1. 用 Chrome/Edge 打开酷狗音乐榜单页面，例如：
   `https://www.kugou.com/yy/rank/home/1-6666.html?from=rank`
2. 按 `F12` 打开开发者工具，切换到 **Network（网络）** 标签。
3. 刷新页面，找到类似以下地址的请求：
   ```
   https://gateway.kugou.com/api/v3/rank/song?version=9108&ranktype=0&plat=0&pagesize=100&id=6666&page=1
   ```
4. 右键该请求 → Copy → Copy link address。
5. 将链接填入 `config.yaml`：
   ```yaml
   platforms:
     kugou:
       name: "酷狗说唱先锋榜"
       list_id: "6666"
       api_url: "https://gateway.kugou.com/api/v3/rank/song?version=9108&ranktype=0&plat=0&pagesize=100&id=6666&page=1"
   ```

### 常见问题

- 如果接口返回 502/403，可能需要带上 Cookie 或 Referer，请更新 `src/fetchers/kugou.py` 中的 headers。
- 如果返回 JSON 结构与当前解析逻辑不符，请根据实际结构修改 `_parse_tracks` 方法。

## QQ 音乐说唱榜

### 步骤

1. 用 Chrome/Edge 打开 QQ 音乐榜单页面，例如：
   `https://y.qq.com/n/yqq/toplist/62.html`
2. 按 `F12` 打开开发者工具，切换到 **Network（网络）** 标签。
3. 刷新页面，过滤 `musicu.fcg` 或 `toplist` 相关请求。
4. 找到返回榜单歌曲数据的请求，通常类似：
   ```
   https://u.y.qq.com/cgi-bin/musicu.fcg?g_tk=...&uin=0&format=json&inCharset=utf-8&outCharset=utf-8&notice=0&platform=h5&needNewCode=1&data=...
   ```
5. 右键 → Copy → Copy link address。
6. 将链接填入 `config.yaml`：
   ```yaml
   platforms:
     qq_music:
       name: "QQ音乐说唱榜"
       list_id: "62"
       api_url: "https://u.y.qq.com/cgi-bin/musicu.fcg?..."
   ```

### 常见问题

- QQ 音乐的 `data` 参数通常是 URL 编码后的 JSON，直接复制完整链接即可。
- 如果链接过期（含 `g_tk`、`sign` 等动态参数），需要重新抓包。
- 返回结构复杂时，请根据实际 JSON 修改 `src/fetchers/qq_music.py` 中的 `_parse_tracks`。

## 验证是否配置成功

配置完成后运行：

```bash
python run.py --start 2026-07-16 --end 2026-07-31
```

查看控制台输出，若酷狗/QQ音乐抓取成功会显示：

```
[INFO] rap_report: 酷狗《酷狗说唱先锋榜》抓取完成，共 XX 首
[INFO] rap_report: QQ 音乐《QQ音乐说唱榜》抓取完成，共 XX 首
```

若仍失败，请检查日志中的错误信息，并确认 API 地址是否可在浏览器中直接访问。

## 安全与合规提示

- 抓包获取的 API 仅供内部研究使用，请勿高频请求，避免对平台服务器造成压力。
- 请勿将含个人 Cookie 或登录态的链接提交到公共仓库。
- 建议将含敏感信息的配置放到 `config.local.yaml`，该文件已被 `.gitignore` 忽略。
