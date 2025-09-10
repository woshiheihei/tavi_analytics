# TAVI Analytics PDF 渲染服务器

一个轻量级的服务，通过无头 Chromium 浏览器渲染高保真 PDF。适用于服务器端从 HTML 或 URL 生成报告。

## 功能

- FastAPI HTTP API
- 通过 Playwright 无头 Chromium 渲染（最高保真度）
- 支持 HTML 字符串或 URL 输入
- CSS 背景打印和 @page 支持
- 可选页眉/页脚 HTML
- 返回 base64 内联或保存的文件路径

## API

### POST /render/pdf

请求体 (JSON):

- html: string (可选) — 要渲染的 HTML；优先于 url
- url: string (可选) — 要渲染的公共 URL
- format: string (默认: A4)
- margin_top|right|bottom|left: string (默认: 12mm)
- print_background: bool (默认: true)
- prefer_css_page_size: bool (默认: true)
- header_template|footer_template: string (可选)
- inline_base64: bool (默认: false) — 如果为 true，返回 base64 编码的 PDF

响应 (JSON):

- success: bool
- path: string (当 inline_base64=false 时)
- base64: string (当 inline_base64=true 时)
- size_bytes: number
- message: string (出错时)

## 本地运行

1. 安装 Python 3.10+
2. 安装依赖和浏览器

   ```bash
   pip install -r requirements.txt
   python -m playwright install --with-deps
   ```

3. 启动服务器

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8080
   ```

4. 测试

   ```bash
   curl -X POST http://localhost:8080/render/pdf \
     -H "Content-Type: application/json" \
     -d '{"html":"<html><body><h1>Hello PDF</h1></body></html>"}'
   ```

## 部署

你可以使用 Docker 或 Docker Compose 进行部署。Docker 相关文件仅限于 `server` 和 `server/dockers` 目录。

### Docker 单容器

构建并运行：

```bash
docker build -t tavi-analytics/pdf-render:latest .
docker run --rm -p 8080:8080 -e PORT=8080 -e PDF_OUT_DIR=/app/out tavi-analytics/pdf-render:latest
```

### Docker Compose（开发环境）

从 `server/dockers` 目录运行：

```bash
docker compose up -d --build
```

这将：

- 从 `server/Dockerfile` 构建镜像
- 暴露 `http://localhost:8080`

### 生产部署（服务器无 build）

推荐流程：

1. 在 CI 或本地构建并推送镜像

   ```bash
   # 从: c:\code\python\slicer\tavi_analytics\server
   docker build -t <registry>/<namespace>/tavi-analytics-pdf-render:<tag> .
   docker push <registry>/<namespace>/tavi-analytics-pdf-render:<tag>
   ```

2. 在服务器上创建小部署目录并使用拉取版 compose 文件

   ```bash
   # 在服务器上
   mkdir tavi-pdf-deploy
   cd tavi-pdf-deploy

   # 从仓库复制这些文件（或直接创建）:
   # - server/dockers/docker-compose.deploy.yml
   # - server/dockers/.env.example (重命名为 .env 并设置 IMAGE=<your pushed image>)

   # 准备 .env
   cp .env.example .env
   # 编辑 .env -> 设置 IMAGE=<registry>/<namespace>/tavi-analytics-pdf-render:<tag>

   # 运行
   docker compose -f docker-compose.deploy.yml --env-file .env up -d
   ```

这种方法避免在服务器上构建，并且不需要克隆整个仓库。你只需要 compose 文件和一个简单的 .env 文件，其中包含镜像引用和端口。

## 部署到服务器步骤

如果要将本地打包的镜像部署到服务器：

1. 本地保存镜像为 tar：

   ```bash
   docker save -o tavi-pdf-render.tar tavi-analytics/pdf-render:latest
   ```

2. 传输到服务器：

   ```bash
   scp tavi-pdf-render.tar user@server:/path/to/deploy/
   ```

3. 在服务器加载镜像并启动：

   ```bash
   docker load -i tavi-pdf-render.tar
   cp .env.example .env
   # 编辑 .env 设置 IMAGE=tavi-analytics/pdf-render:latest
   docker compose -f docker-compose.deploy.yml --env-file .env up -d
   ```

## 注意事项

- 设置 `PDF_OUT_DIR` 来控制容器内文件写入位置（默认不持久化）。
- Playwright 基础镜像已包含浏览器，无需额外安装步骤。
- 健康检查：GET /health
- 日志：`docker logs -f tavi-pdf-server`
