# 说唱音乐行业双周报自动化工具

自动化抓取说唱音乐榜单数据，生成聚合分析与报告初稿（Excel + Markdown + PPT）。

## 功能

- 自动抓取四大平台说唱榜单
  - 网易云音乐中文说唱榜 TOP50
  - 网易云音乐全球说唱榜 TOP10
  - QQ 音乐说唱榜 TOP50
  - 酷狗音乐说唱先锋榜 TOP30
- 自动抓取舆情/热搜
  - 抖音热榜（自动筛选说唱关键词）
  - 微博热搜（无需登录）
- 跨平台聚合分析
  - 头部艺人上榜曲目数
  - 歌曲跨平台表现
  - 跨平台爆款识别
  - 各平台新歌数量（需历史数据）
  - 排名变化（需历史数据）
- 自动生成多种图表
  - 柱状图、饼图、雷达图、矩形树图、排名变化图、词云图
- AI 生成榜单描述文案（可选）
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
├── run.bat                  # Windows 一键运行脚本（需要 AI Key）
├── run_no_ai.bat            # Windows 一键运行脚本（无需 AI Key）
├── .github/workflows/       # GitHub Actions 定时任务
├── data/                    # 手动维护的演出/厂牌/行业动态数据
│   ├── events.csv           # 演出信息（自动生成的模板）
│   ├── labels.csv           # 厂牌信息（自动生成的模板）
│   └── industry.csv         # 行业动态（自动生成的模板）
├── docs/
│   └── API_CAPTURE_GUIDE.md # 抓包教程（备用）
├── src/
│   ├── fetchers/            # 各平台榜单/热搜抓取器 + 手动数据读取
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

### 2. 配置 AI 中转站（可选）

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

- **有 AI Key**：双击 `run.bat`
- **没有 AI Key**：双击 `run_no_ai.bat`

两种都会生成完整的报告骨架（Excel + 图表 + PPT），区别只是 AI 文案是否自动生成。

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
2. 抓取抖音/微博热搜
3. 读取 `data/` 目录下的人工补充数据
4. 保存原始数据 CSV
5. 生成聚合分析 Excel
6. 生成多种 PNG 图表
7. 调用 AI 生成文案（如果未禁用）
8. 输出 Markdown 报告初稿
9. 输出 PPT 报告初稿（含演出/厂牌/行业动态）

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

### 默认运行

`run.bat` 是 Windows 一键运行脚本，直接双击即可生成默认上一双周报告（需要 AI Key）。

`run_no_ai.bat` 是无 AI 模式的一键脚本，直接双击即可生成报告骨架（无需 AI Key）。

### 指定日期运行

如果需要指定日期，可以修改 `run.bat` 或 `run_no_ai.bat` 中的命令，例如：

```bat
@echo off
python run.py --start 2026-07-16 --end 2026-07-31 --no-ai
pause
```

## 手动补充数据说明（data/ 目录）

因为演出信息、厂牌动态、行业新闻等内容没有稳定免费的公开 API，工具提供了**手动补充**的方式。你只需在 `data/` 目录的 CSV 文件中填写，运行报告时就会自动读取并写入 Markdown/PPT。

### 第一次使用

首次运行 `run.bat` 或 `run_no_ai.bat` 后，会自动创建 3 个模板文件：

```
data/
├── events.csv      ← 演出信息
├── labels.csv      ← 厂牌信息
└── industry.csv    ← 行业动态
```

### 如何编辑

用 **Excel / WPS / 记事本** 打开 CSV 文件，把示例数据替换成真实数据，保存后再运行 `run.bat`。

#### events.csv（演出信息）

| 字段 | 说明 | 示例 |
|---|---|---|
| `date` | 演出日期 | 2026-07-20 |
| `name` | 演出名称 | 成都说唱之夜 |
| `city` | 城市 | 成都 |
| `venue` | 场地 | 东郊记忆 |
| `artists` | 参演艺人 | GAI/马思唯 |
| `status` | 售票状态 | 已开票/预售中/售罄 |

示例：

```csv
date,name,city,venue,artists,status
2026-07-20,成都说唱之夜,成都,东郊记忆,GAI/马思唯,已开票
2026-07-25,说唱巅峰对决巡演,北京,凯迪拉克中心,杨和苏/法老,预售中
```

#### labels.csv（厂牌信息）

| 字段 | 说明 | 示例 |
|---|---|---|
| `name` | 厂牌名称 | 种梦音乐 |
| `focus` | 厂牌定位 | 主流说唱 |
| `artists` | 代表艺人 | GAI/艾热/布瑞吉 |
| `highlight` | 本周期动态 | 发布新专辑/签约新人 |

示例：

```csv
name,focus,artists,highlight
种梦音乐,主流说唱,GAI/艾热/布瑞吉,本周期发布新专辑
```

#### industry.csv（行业动态）

| 字段 | 说明 | 示例 |
|---|---|---|
| `category` | 类别 | 综艺/政策/资本/市场 |
| `title` | 事件标题 | 《说唱巅峰对决2026》热播 |
| `summary` | 简要说明 | 本周期节目话题量持续增长 |

示例：

```csv
category,title,summary
综艺,《说唱巅峰对决2026》热播,本周期节目话题量持续增长
```

### 可以不填吗？

可以。不填时，报告中对应章节会显示"暂无数据"，其他自动抓取的内容（榜单、图表、热搜）都正常生成。

### 注意

`data/*.csv` 已加入 `.gitignore`，不会提交到 GitHub，避免每个人的本地数据互相覆盖。

## 配置说明

### config.yaml（可提交 Git）

包含基础配置：
- 报告标题/副标题
- 图表配色
- 平台榜单 ID
- 热搜关键词
- PPT 模板路径占位
- 手动数据文件路径

### config.local.yaml（不要提交 Git）

包含敏感配置：
- AI 中转站 base_url / api_key / model
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
| 热搜话题词云 | `chart_hot_search_wordcloud.png` | 词云图 |
| 各平台新歌数量 | `chart_platform_new_songs.png` | 柱状图（需历史数据） |
| 排名上升 TOP | `chart_rank_changes.png` | 横向柱状图（需历史数据） |

## GitHub Actions 定时运行

仓库 `.github/workflows/weekly_report.yml` 已配置每月 1 日和 16 日 09:00（北京时间）自动运行。

当前 workflow 默认使用 `--no-ai` 模式，因此**不需要配置 Secrets 也能成功运行**，只是生成的报告中 AI 文案位置为空。

### 启用 AI 文案（可选）

如果后续有了共享 AI Key，可以启用：

1. 在仓库 **Settings → Secrets and variables → Actions** 中配置：
   - `AI_BASE_URL`：AI 中转站地址
   - `AI_API_KEY`：API Key
   - `AI_MODEL`：模型名称（如 `Kimi/Kimi-K2.7-code`）
2. 编辑 `.github/workflows/weekly_report.yml`
3. 把 `python run.py --no-ai` 和 `python run.py --start ... --end ... --no-ai` 中的 `--no-ai` 去掉
4. 提交并推送

## 给团队其他人使用

1. 克隆仓库
2. 安装依赖：`pip install -r requirements.txt`
3. （可选）复制配置：`cp config.yaml config.local.yaml`
4. （可选）在 `config.local.yaml` 中配置 AI Key
5. （可选）在 `data/` 目录补充演出/厂牌/行业动态
6. 运行：
   - 有 AI Key：双击 `run.bat` 或运行 `python run.py`
   - 无 AI Key：双击 `run_no_ai.bat` 或运行 `python run.py --no-ai`
7. 查看 `output/` 目录输出

## 常见问题

### Q1: 没有 AI Key 能运行吗？

可以。使用 `--no-ai` 参数或双击 `run_no_ai.bat`。此时会跳过 AI 调用，生成完整的报告骨架，只是平台总结、艺人洞察、爆款分析等文案位置会留空，需要人工填写。

### Q2: 可以自己选择报告周期吗？

可以。使用 `--start` 和 `--end` 参数，例如：

```bash
python run.py --start 2026-07-16 --end 2026-07-31
```

### Q3: PPT 为什么不是公司模板风格？

只有在 `config.local.yaml` 中正确配置 `pptx.template_path` 并且路径存在时，才会使用公司模板。否则使用内置通用版式。

### Q4: data/ 里的 CSV 必须填吗？

不是必须。不填时报告仍然生成，只是演出/厂牌/行业动态章节显示"暂无数据"。

### Q5: GitHub Actions 需要配置 Secrets 吗？

当前不需要。workflow 默认使用 `--no-ai`，不依赖 AI Key。如果需要 AI 文案，再按上面"启用 AI 文案"的步骤配置。

## 注意事项

- 本工具仅供内部研究使用，请遵守各平台服务条款。
- 榜单页面结构可能变化，如抓取失败请检查并更新对应 `fetcher`。
- AI 生成文案为初稿，发布前请人工审核。
- 演出/厂牌/舆情等深度模块目前部分依赖人工补充，已提供 CSV 模板和报告章节。

## 开发计划

- [x] 网易云音乐榜单自动抓取
- [x] QQ 音乐说唱榜自动抓取
- [x] 酷狗音乐说唱先锋榜自动抓取
- [x] 抖音热榜抓取
- [x] 微博热搜抓取（无需登录）
- [x] 聚合分析与多样化图表
- [x] AI 文案生成
- [x] Markdown / Excel / PPT 报告输出
- [x] Git 仓库初始化并推送到 GitHub
- [x] 演出/厂牌/行业动态手动补充模块
- [ ] 演出/厂牌/舆情等模块的自动抓取（需稳定数据源，二期）
