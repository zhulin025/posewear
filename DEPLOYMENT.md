# 这份 fork 的部署

源码仓库：<https://github.com/zhulin025/posewear>。`origin` 指向本 fork，
`upstream` 保留原作者仓库。

主站：<https://posewear.halili.win>（Pages 项目 `posewear-zhulin025`）。
大图和原图：Pages 项目 `posewear-originals-zhulin025`。

## 为什么拆成两个项目

原版全量构建约 25,849 个文件，超过 Pages Free 每站 20,000 文件的限制。
主站保留页面、缩略图和中等尺寸图片；原始 PNG 和服装大图单独上传。
主站用三条静态重定向转到素材站，素材站提供公开图片的 CORS 响应头和
原图下载响应头。浏览图片不会调用 Function，只有 `/api/proxy` 会调用。

当前素材预计主站 17,459 个文件、素材站 8,394 个文件。每次打包都会重新
检查两个站点的文件数及单文件 25 MiB 上限；素材数量增加后以打包结果为准。

## 本地构建和更新

需要 Python 3.12+ 和 Node.js 22.12+。图片及生成目录不会提交到 GitHub。

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm ci

# 首次下载较慢；重跑会跳过已有图片。默认 4 线程，最高允许 8 线程。
python scripts/fetch-assets.py
POSEWEAR_SITE=https://posewear.halili.win python build.py
npm run prepare:pages

# 保留完整 dist，用于本地预览和测试。
npm run serve
# 另一个终端中运行 npm test
```

更新时先上传素材站，再上传主站，避免新页面引用尚未上传的图片：

```bash
source .venv/bin/activate
npx wrangler whoami
npm run deploy:originals
npm run deploy
```

此项目使用本地构建和 Direct Upload；仅向 GitHub 推送代码不会自动更新站点。
`functions/api/proxy.js` 会随主站一起部署，素材站不包含 Functions。
AI 图片生成仍使用访问者自己填写的 API Key，模型调用费用由对应服务商收取。

## 域名与现有服务

本项目只新增 `posewear.halili.win` 的 CNAME，指向
`posewear-zhulin025.pages.dev`。不改变 `halili.win` 的 nameservers、
根域名、`web3`、`ai`、`tts`、`guta` 记录或现有 Worker 路由。
Cloudflare 管理 DNS，与阿里云 VPS 托管项目可以并存；每个主机名按自己的
DNS 记录和 Worker 绑定分别路由。

额度参考：[Pages 限制](https://developers.cloudflare.com/pages/platform/limits/)、
[Functions 计费](https://developers.cloudflare.com/pages/functions/pricing/)。
静态资源请求免费；Free 的 Functions 与同账户其他 Workers 共享每天 100,000
请求的额度。域名续费和模型 API 费用不包含在托管免费额度里。
