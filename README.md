# Comfyui-Jojoagent-ai

Jojoagent 的 ComfyUI 客户端插件。买家只需要填写你发放的 Jojoagent API 口令，即可在 ComfyUI 中使用提示词、识图和图像生成相关节点。

本版按 SynVow 类插件的工作流重新设计，但没有复制其代码、提示词或节点命名；同类功能被合并成更少但更可操作的节点，参数选项尽量使用中文。

## 安装

把整个文件夹复制到：

```text
你的ComfyUI目录\custom_nodes\Comfyui-Jojoagent-ai
```

安装依赖：

```powershell
cd "你的ComfyUI目录"
.\python_embeded\python.exe -m pip install -r ".\custom_nodes\Comfyui-Jojoagent-ai\requirements.txt"
```

重启 ComfyUI。

## 节点清单

### Jojoagent/API

| 节点 | 功能 |
|---|---|
| Jojo 账号与用量 | 查询余额、查询最近用量。 |
| Jojo AI 图像生成 | 单张文生图，走你的 Jojoagent 中转和额度扣费。 |
| Jojo AI 批量图像生成 | 多提示词批量生图，或单提示词多次生成。 |
| Jojo 扣费详情 | 查看最近扣费记录、成功扣费合计和当前余额。 |

### Jojoagent/Prompt

| 节点 | 功能 |
|---|---|
| Jojo 提示词优化器 | 产品视觉、高级画册、固定场景模特换装、人像摄影视觉、人像视觉系列衍生等模板；可输出单条提示词或多屏 prompts_list。 |
| Jojo 电商详情页提示词 | 支持正面图、背面图、侧面图、风格参考1、风格参考2；可选10种高级风格；可调用识图模型生成多屏详情页提示词。 |
| Jojo 识图提示词反推 | 输入 1-8 张图片，通过 Jojoagent 中转识图模型，输出优化提示词、图片分析和负面提示词。 |

### Jojoagent/Text

| 节点 | 功能 |
|---|---|
| Jojo 文本工具 | 合并文本分割、选择单条、范围选择、重复文本、批次分组、标记提取。 |

### Jojoagent/Image

| 节点 | 功能 |
|---|---|
| Jojo 图片工具 | 合并加载图片、缩放图片、范围选择、预览透传。 |

### Jojoagent/Utils

| 节点 | 功能 |
|---|---|
| Jojo 文件夹扫描 | 扫描图片、文本、视频、音频或全部文件。 |
| Jojo 媒体路径加载 | 输出视频/音频/任意文件路径，方便接后续节点。 |
| Jojo 运行索引 | 每次运行自增，也可重置。 |

## API 配置

`api_base` 默认连接 Jojoagent 额度服务器：

```text
http://124.221.138.114:8001
```

`api_token` 填你给买家生成的口令，例如：

```text
sk_xxxxxxxxx
```

## 当前模型

图像生成模型：

```text
gpt-image-2-all
gemini-3.1-flash-image-preview
```

识图/提示词模型：

```text
gemini-3.1-flash-lite-preview
gemini-3.1-flash-lite-preview-thinking-high
gemini-3-pro-preview
claude-opus-4-6-thinking
```

## 新增图像模型

先在服务器：

```text
ApiCreditGateway/app/main.py
```

修改 `IMAGE_MODEL_PRICES`。

再在插件：

```text
Comfyui-Jojoagent-ai/nodes.py
```

把模型名加入 `IMAGE_MODELS` 和 `MODEL_LABELS`。
