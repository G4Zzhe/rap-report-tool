# 说唱音乐行业双周报自动化工具

自动化抓取说唱音乐榜单数据，生成聚合分析与报告初稿。

## 功能

- 抓取三大平台说唱榜单
  - 网易云音乐中文说唱榜
  - 网易云音乐全球说唱榜
  - 酷狗音乐说唱先锋榜
  - QQ 音乐说唱榜
- 跨平台聚合分析：艺人上榜次数、新歌数量、排名变化、跨平台爆款
- 自动生成 Excel 数据表与 PNG 图表
- 接入 AI 生成榜单描述文案（Markdown 初稿）
- 支持本地一键运行与 GitHub Actions 定时运行

## 项目结构

```
rap-report-tool/
├── config.yaml              # 基础配置
├── config.local.yaml        # 本地私密配置（不提交 Git）
├── requirements.txt         # Python 依赖
├── run.py                   # 本地主入口
├── run.bat                  # Windows 一键运行
├── .github/workflows/       # GitHub Actions 定时任务
├── src/
│   ├── fetchers/            # 各平台榜单抓取器
│   ├── analysis/            # 数据聚合分析
│   ├── charts/              # 图表生成
│   ├── ai/                  # AI 文案生成
│   └── report/              # Markdown / Excel 报告生成
└── output/                  # 输出目录
```

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 AI 中转站（可选但推荐）

复制模板配置：

```bash
cp config.yaml config.local.yaml
```

在 `config.local.yaml` 中填写你的公司 AI 中转站地址和 API Key：

```yaml
ai:
  enabled: true
  base_url: "https://your-company-gateway.com/v1"
  api_key: "sk-xxxxxxxx"
  model: "gpt-4o-mini"
```

### 3. 配置酷狗/QQ 音乐 API（可选）

网易云音乐已自动抓取。如需使用酷狗/QQ 音乐，请按 [`docs/API_CAPTURE_GUIDE.md`](docs/API_CAPTURE_GUIDE.md) 抓包获取 API 地址并填入 `config.local.yaml`。

### 4. 运行

```bash
python run.py --start 2026-07-16 --end 2026-07-31
```

Windows 用户也可以直接双击 `run.bat`。

运行时会自动：
1. 抓取各平台榜单
2. 保存原始数据 CSV
3. 生成聚合分析 Excel
4. 生成 PNG 图表
5. 调用 AI 生成文案并输出 Markdown 初稿

### 5. 查看输出

结果保存在 `output/` 目录：

- `raw_榜单数据.csv`：原始榜单数据
- `analysis_聚合分析.xlsx`：聚合分析 Excel
- `chart_*.png`：图表
- `report_*.md`：Markdown 报告初稿

## 输出示例

```
output/
├── raw_20260716_20260731.csv
├── analysis_20260716_20260731.xlsx
├── chart_artist_ranking.png
├── chart_platform_new_songs.png
└── report_20260716_20260731.md
```

## GitHub Actions 定时运行

仓库 `.github/workflows/weekly_report.yml` 已配置每两周周一 09:00 自动运行（UTC+8）。

需要在仓库 Settings → Secrets and variables → Actions 中配置：

- `AI_BASE_URL`：AI 中转站地址
- `AI_API_KEY`：API Key
- `AI_MODEL`：模型名称（如 `gpt-4o-mini`）

配置后，GitHub Actions 会自动运行并上传输出文件到 Artifacts，下载后即可使用。

## 注意事项

- 本工具仅供内部研究使用，请遵守各平台服务条款。
- 网易云音乐榜单已实现自动抓取；酷狗音乐和 QQ 音乐需要抓包获取真实 API 地址，详见 [`docs/API_CAPTURE_GUIDE.md`](docs/API_CAPTURE_GUIDE.md)。
- 榜单页面结构可能变化，如抓取失败请检查并更新对应 `fetcher`。
- AI 生成文案为初稿，发布前请人工审核。

## 开发计划

- [x] 网易云音乐榜单自动抓取
- [x] 酷狗/QQ 音乐榜单框架（需补充 API）
- [x] 聚合分析与图表
- [x] AI 文案生成
- [x] Markdown / Excel 报告输出
- [ ] 微博/抖音热搜抓取
- [ ] 自动 PPT 生成
- [ ] 演出信息抓取
