# 天气 Agent

一个可以查询天气、空气质量并给出穿衣建议的命令行 Agent。

基于 **Function Calling** 实现：模型自己决定调用哪个工具、传什么参数，程序执行工具后把结果回传给模型，模型再整合成自然语言回答。

## 功能

| 问题示例 | 模型会做什么 |
|---|---|
| 济南天气怎么样 | 调用 `get_weather("济南")` |
| 济南空气怎么样 | 调用 `get_air_quality("济南")` |
| 济南今天穿什么 | 先 `get_weather`，再 `suggest_clothes(temp, weather)` |
| 济南天气和空气怎么样 | 同时调用两个工具 |
| 火星天气怎么样 | 工具校验发现城市无效，返回明确错误 |

## 项目结构

```
weather-agent/
├── main.py              # 入口：读取输入、调用 agent
├── llm.py               # LLM 客户端 + Agent 循环（核心逻辑）
├── tools/
│   ├── __init__.py      # 工具注册表 + 工具 schema
│   └── weather.py       # 三个工具的实现
├── requirements.txt
├── .env.example         # 环境变量模板
├── .gitignore
└── README.md
```

## 快速开始

```powershell
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置 API Key（通义千问）
$env:QWEN_API_KEY = "sk-你的key"

# 3. 运行
python main.py
```

## 核心设计

### 1. Agent 循环（llm.py）

```
while 步数 < max_steps:
    调用模型
    ├─ 模型没要求工具 → 返回最终回答
    └─ 模型要求工具 → 逐个执行 → 结果塞回 messages → 继续循环
```

### 2. 工具三要素

- **name**：和注册表里的 key 完全一致
- **description**：写清楚“什么时候用、什么时候不用”（决定模型选得对不对）
- **parameters**：类型、约束、required

### 3. 边界处理

- 城市无效（如“火星”）→ `get_weather` 校验返回城市名后拒绝
- 工具执行异常 → 捕获后把错误信息回传给模型，不崩溃
- 最大步数限制 → 防止无限循环

## 数据来源

- 天气：`wttr.in`（免费、无需 key）
- 空气质量：`open-meteo.com`（免费、无需 key）
