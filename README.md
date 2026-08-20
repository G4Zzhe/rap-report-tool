# 说唱音乐行业双周报自动化工具

自动化抓取说唱音乐榜单数据，生成聚合分析与报告初稿（Excel + Markdown + PPT）。

## 功能

- 自动抓取四大平台说唱榜单
  - 网易云音乐中文说唱榜 TOP50
  - 网易云音乐全球说唱榜 TOP10
  - QQ 音乐说唱榜 TOP50
  - 酷狗音乐说唱先锋榜 TOP30
- 跨平台聚合分析
  - 头部艺人上榜曲目数
  - 歌曲跨平台表现
  - 跨平台爆款识别
  - 各平台新歌数量（需历史数据）
  - 排名变化（需历史数据）
- 自动生成多种图表
  - 柱状图、饼图、雷达图、矩形树图、排名变化图
- AI 生成榜单描述文案
- 自动生成报告
  - Excel 多 sheet 数据表
  - Markdown 报告初稿
  - PPT 报告初稿（支持自定义公司模板）
- 本地一键运行 + GitHub Actions 定时运行

## 项目结构

```
rap-report-tool/
├── config.yaml              # 基础配置（可提交 Git）
├── config.local.yaml        # 本地私密配置（不提交 Git）
├── requirements.txt         # Python 依赖
├── run.py                   # 本地主入口
├── run.bat                  # Windows 一键运行脚本
├── .github/workflows/       # GitHub Actions 定时任务
├── docs/
│   └── API_CAPTURE_GUIDE.md # 抓包教程（备用）
├── src/
│   ├── fetchers/            # 各平台榜单/热搜抓取器
│   ├── analysis/            # 数据清洗 + 聚合分析
│   ├── charts/              # 图表生成
│   ├── ai/                  # AI 文案生成
│   └── report/              # Markdown / Excel / PPT 报告生成
└── output/                  # 输出目录
```

## 快速开始

### 1. 环境准备

需要 Python 3.11 或更高版本。

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# Windows 激活虚拟环境
venv\Scripts\activate

# macOS/Linux 激活虚拟环境
# source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 AI 中转站（可选但推荐）

AI 文案生成功能需要配置 OpenAI 兼容接口。复制基础配置文件：

```bash
cp config.yaml config.local.yaml
```

在 `config.local.yaml` 中填写你的 AI 中转站信息：

```yaml
ai:
  enabled: true
  base_url: "https://your-company-gateway.com/v1"
  api_key: "sk-xxxxxxxx"
  model: "gpt-4o-mini"
  temperature: 1.0
```

注意：某些模型（如 Kimi/Kimi-K2.7-code）只支持 `temperature: 1.0`，如果报 400 错误请调整此值。

### 3. 配置 PPT 模板（可选）

如果不配置，工具会使用内置通用版式生成 PPT。如果想使用公司模板，在 `config.local.yaml` 中指定路径：

```yaml
pptx:
  template_path: "D:\\公司文档\\说唱报告模板.pptx"
```

路径使用双反斜杠（Windows）或正斜杠。

### 4. 运行

#### 方式一：Windows 双击运行（最方便）

直接双击 `run.bat`，会生成上一双周周期的报告（需要配置 AI Key）。

如果**没有 AI Key**，双击 `run_no_ai.bat`，会生成完整的报告骨架（Excel + 图表 + PPT），只是 AI 文案位置留空。

#### 方式二：命令行运行

```bash
# 生成上一双周周期的报告
python run.py

# 指定起止日期
python run.py --start 2026-07-16 --end 2026-07-31

# 指定历史数据，计算新歌和排名变化
python run.py --start 2026-07-16 --end 2026-07-31 --history output/raw_20260701_20260715.csv

# 禁用 AI 文案生成（无需 API Key）
python run.py --no-ai

# 指定日期 + 禁用 AI
python run.py --start 2026-07-16 --end 2026-07-31 --no-ai
```

运行时会自动：
1. 抓取各平台榜单数据
2. 抓取抖音/微博热搜（微博需 Cookie）
3. 保存原始数据 CSV
4. 生成聚合分析 Excel
5. 生成多种 PNG 图表
6. 调用 AI 生成文案
7. 输出 Markdown 报告初稿
8. 输出 PPT 报告初稿

### 5. 查看输出

所有输出保存在 `output/` 目录：

- `raw_YYYYMMDD_YYYYMMDD.csv`：原始榜单数据
- `analysis_YYYYMMDD_YYYYMMDD.xlsx`：聚合分析 Excel
- `chart_*.png`：生成的图表
- `report_YYYYMMDD_YYYYMMDD.md`：Markdown 报告初稿
- `report_YYYYMMDD_YYYYMMDD.pptx`：PPT 报告初稿

## 命令行参数说明

| 参数 | 说明 | 示例 |
|---|---|---|
| `--start` | 报告周期开始日期（YYYY-MM-DD） | `--start 2026-07-16` |
| `--end` | 报告周期结束日期（YYYY-MM-DD） | `--end 2026-07-31` |
| `--history` | 上一期原始榜单 CSV 路径 | `--history output/raw_20260701_20260715.csv` |
| `--no-ai` | 禁用 AI 文案生成 | `--no-ai` |

不指定 `--start` 和 `--end` 时，默认生成上一双周周期：
- 今天 ≥ 16 号：本月 1 日 ~ 15 日
- 今天 < 16 号：上月 16 日 ~ 上月最后一日

## run.bat 用法

`run.bat` 是 Windows 一键运行脚本，直接双击即可生成默认上一双周报告（需要 AI Key）。

`run_no_ai.bat` 是无 AI 模式的一键脚本，直接双击即可生成报告骨架（无需 AI Key）。

如果需要指定日期，可以修改 `run.bat` 或 `run_no_ai.bat` 中的命令，例如：

```bat
@echo off
python run.py --start 2026-07-16 --end 2026-07-31 --no-ai
pause
```

## 配置说明

### config.yaml（可提交 Git）

包含基础配置：
- 报告标题/副标题
- 图表配色
- 平台榜单 ID
- 热搜关键词
- PPT 模板路径占位

### config.local.yaml（不要提交 Git）

包含敏感配置：
- AI 中转站 base_url / api_key / model
- 微博登录 Cookie
- 个人 PPT 模板路径

首次使用时从 `config.yaml` 复制：

```bash
cp config.yaml config.local.yaml
```

然后只修改你需要覆盖的项即可。

## 图表类型

工具会根据数据自动生成以下图表：

| 图表 | 文件名 | 说明 |
|---|---|---|
| 头部艺人上榜曲目数 | `chart_artist_ranking.png` | 横向柱状图 |
| 头部艺人综合表现 | `chart_artist_radar.png` | 雷达图 |
| 跨平台爆款歌曲 | `chart_cross_platform_hits.png` | 横向柱状图 |
| 各平台歌曲分布 | `chart_platform_distribution.png` | 饼图 |
| 歌曲上榜平台数 | `chart_platform_treemap.png` | 矩形树图 |
| 各平台新歌数量 | `chart_platform_new_songs.png` | 柱状图（需历史数据） |
| 排名上升 TOP | `chart_rank_changes.png` | 横向柱状图（需历史数据） |

## GitHub Actions 定时运行

仓库 `.github/workflows/weekly_report.yml` 已配置每月 1 日和 16 日 09:00（北京时间）自动运行。

需要在仓库 **Settings → Secrets and variables → Actions** 中配置：

- `AI_BASE_URL`：AI 中转站地址
- `AI_API_KEY`：API Key
- `AI_MODEL`：模型名称（如 `Kimi/Kimi-K2.7-code`）

配置后，GitHub Actions 会自动运行并上传输出文件到 Artifacts，下载后即可使用。

## 给团队其他人使用

1. 克隆仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 复制配置：`cp config.yaml config.local.yaml`
4. 在 `config.local.yaml` 中配置 AI Key（如需要 AI 文案）
5. 运行：`python run.py --start 开始日期 --end 结束日期`
6. 查看 `output/` 目录输出

如果不需要 AI 文案，不配置 AI Key 也能生成 Excel、图表和 PPT 骨架，运行时使用 `python run.py --no-ai` 或双击 `run_no_ai.bat`。

## 常见问题

### Q1: 没有 AI Key 能运行吗？

可以。使用 `--no-ai` 参数：

```bash
python run.py --no-ai
```

或双击 `run_no_ai.bat`。此时会跳过 AI 调用，生成完整的报告骨架，但平台总结、艺人洞察、爆款分析等文案位置会留空，需要人工填写。

### Q2: 酷狗榜单抓取为空？

酷狗说唱先锋榜详情接口需要 `rankid` 和 `rank_cid` 参数，当前代码会自动从榜单列表接口获取。如果仍然失败，可能是接口结构变化，请检查日志。

### Q2: 微博热搜抓不到？

微博热搜需要登录 Cookie。在浏览器登录微博后，把 Cookie 字符串写入 `config.local.yaml`：

```yaml
hot_search:
  weibo_cookie: "SUB=_2Ak...; login_sid_t=..."
```

注意 Cookie 会过期，且不建议把 Cookie 提交到 Git。

### Q3: PPT 为什么不是公司模板风格？

只有在 `config.local.yaml` 中正确配置 `pptx.template_path` 并且路径存在时，才会使用公司模板。否则使用内置通用版式。

### Q4: 可以自己选择报告周期吗？

可以。使用 `--start` 和 `--end` 参数，例如：

```bash
python run.py --start 2026-07-16 --end 2026-07-31
```

## 注意事项

- 本工具仅供内部研究使用，请遵守各平台服务条款。
- 榜单页面结构可能变化，如抓取失败请检查并更新对应 `fetcher`。
- AI 生成文案为初稿，发布前请人工审核。
- 演出/厂牌/舆情等深度模块目前依赖人工补充，已预留 PPT 章节提示。

## 开发计划

- [x] 网易云音乐榜单自动抓取
- [x] QQ 音乐说唱榜自动抓取
- [x] 酷狗音乐说唱先锋榜自动抓取
- [x] 抖音热榜抓取
- [ ] 微博热搜完整抓取（需 Cookie）
- [x] 聚合分析与多样化图表
- [x] AI 文案生成
- [x] Markdown / Excel / PPT 报告输出
- [x] Git 仓库初始化
- [ ] 演出/厂牌/舆情等深度模块（二期）
