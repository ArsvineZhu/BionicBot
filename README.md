# Bionic Bot - 智能QQ机器人

## 项目简介

Bionic Bot是一款基于ncatbot框架开发的智能QQ机器人，集成了AI对话功能，支持群聊和私聊场景，能够根据上下文生成连贯、智能的回复。

## 功能特性

### 核心功能
- 🤖 **AI对话**：集成火山方舟AI模型，支持智能对话生成
- 👥 **群聊支持**：支持多群聊管理，可配置目标群组
- 💬 **私聊支持**：支持与指定用户的私聊交互
- 📚 **上下文管理**：智能管理对话上下文，保持对话连贯性
- 🔍 **历史记录获取**：自动获取聊天历史记录，增强上下文理解
- ⏱️ **智能延迟**：根据消息长度生成合理的回复延迟，模拟真实聊天体验
- 📅 **时间标记**：每条消息前添加格式化时间戳，便于上下文理解
- 📝 **AI决策模型**：使用更快、更便宜的模型决定是否应该回复

### 高级功能
- 📝 **多回复模式**：支持多种回复触发模式（关键词、@、AI自主判断等）
- 🔑 **关键词触发**：支持正则表达式关键词匹配，支持"@+关键词"的或关系
- 🎯 **目标对象管理**：可配置目标群组和用户
- 🧠 **记忆系统**：支持短期记忆和长期记忆
- 📋 **对话线程管理**：自动识别和管理不同对话线程
- 🏷️ **话题检测**：智能检测对话话题，保持话题相关性
- 🔧 **可配置性**：所有功能均支持通过模块化YAML配置文件调整
- 🏷️ **昵称-称呼映射**：支持昵称到标准称呼的映射，增强回复的个性化
- 📊 **对话摘要系统**：定期或在获取历史记录后自动生成聊天摘要，优化上下文管理
- 📝 **动态提示词加载**：支持从文件动态加载系统提示词，便于维护和更新

### 优化特性
- 🕵️ **隐私保护**：配置文件和密钥文件集中管理在`bot/data/`目录，保护隐私数据
- 📱 **输入状态模拟**：私聊时显示"输入中"状态，提升用户体验
- ✨ **格式优化**：自动清理AI回复中的冗余信息，确保回复格式规范
- 🚀 **性能优化**：优化状态管理，减少不必要的API调用
- 🔒 **配置安全**：实现了安全的配置加载机制，支持配置文件不存在、解析错误等异常情况的安全处理
- 🧪 **完善测试**：编写了全面的单元测试，确保配置系统的正确性和可靠性
- 📁 **模块化配置**：配置文件拆分为ai.yaml、bot.yaml和system.yaml，便于维护和管理
- 🔍 **配置示例文件**：提供带注释的配置示例文件，便于用户配置

## 技术栈

| 技术/框架 | 版本 | 用途 |
|-----------|------|------|
| Python | 3.13+ | 开发语言 |
| ncatbot | 0.1.0+ | QQ机器人框架 |
| volcenginesdkarkruntime | 0.1.0+ | AI模型接口 |
| pyyaml | 6.0+ | YAML配置管理 |
| aiohttp | 3.8.0+ | HTTP客户端 |
| asyncio | 内置 | 异步编程 |

## 安装部署

### 环境准备

1. **Python环境**：确保安装了Python 3.13或更高版本
2. **虚拟环境**：建议使用虚拟环境隔离项目依赖
3. **QQ账号**：需要一个QQ账号作为机器人账号
4. **ncatbot框架**：项目已集成ncatbot，无需单独安装

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/ArsvineZhu/bionicbot.git
cd bionicbot
```

2. **创建虚拟环境**
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r bot/requirements.txt
```

4. **配置文件设置**
   - 配置文件已拆分为三个模块化文件，位于 `bot/data/config/` 目录：
     - `ai.yaml`：AI模型配置、摘要系统配置、记忆配置等
     - `bot.yaml`：机器人基础配置、回复模式配置、关键词配置等
     - `system.yaml`：系统配置、日志配置、WebUI配置等
   - 每个配置文件都有对应的示例文件（如 `ai.yaml.example`），带有详细注释
   - 复制示例文件并删除 `.example` 后缀，根据需要修改配置项
   - 将API密钥写入 `bot/data/key` 文件

5. **启动机器人**
```bash
# 直接运行脚本
python main.py
```

## 配置说明

配置文件已拆分为三个模块化文件，位于 `bot/data/config/` 目录，采用YAML格式，支持动态调整，无需重启机器人即可生效。配置系统实现了安全可靠的加载机制，当配置文件不存在、解析错误或权限问题时，会使用合理的默认值继续运行。

### 配置文件结构

```
bot/data/config/
├── ai.yaml          # AI模型、摘要系统、记忆配置等
├── bot.yaml         # 机器人基础配置、回复模式、关键词等
├── system.yaml      # 系统配置、日志、WebUI等
└── *.yaml.example   # 配置示例文件，带有详细注释
```

### 1. AI配置 (ai.yaml)

包含AI模型配置、摘要系统配置、记忆配置等。

```yaml
# AI基础配置
base_url: https://ark.cn-beijing.volces.com/api/v3
api_key_path: ../key

# 模型配置 - Main model
model: "doubao-seed-1-6-251015"
temperature: 0.8
reasoning: MEDIUM  # 可用值: MINIMAL, LOW, MEDIUM, HIGH
reasoning_available: true
cache: true

# Decision model (用于AI决策是否回复)
decision_model: "doubao-seed-1-6-flash-250828"
decision_temperature: 0.0
decision_reasoning: MINIMAL
decision_reasoning_available: false
decision_cache: false

# 摘要系统配置
summary_enabled: true
summary_model: "doubao-seed-1-6-flash-250828"
summary_temperature: 0.1
summary_min_messages: 10
summary_max_messages: 50
summary_interval_hours: 1
summary_short_interval_minutes: 30
summary_check_frequency: 10

# 记忆配置
short_term_memory_limit: 50
long_term_memory_path: "data/long_term_memory.json"
long_term_memory_limit: 50
long_term_memory_default_importance: 1.0

# 历史记录配置
enable_history_retrieval: true
history_retrieval_limit: 50
history_retrieval_max_length: 1000
history_retrieval_on_first_message: true
history_retrieval_on_new_session: true

# 高级模型配置
# 这些配置用于更精细地控制模型生成
max_tokens: 2048
stop: null
top_p: 0.9
presence_penalty: 0.0
frequency_penalty: 0.0

# Decision model 高级配置
decision_max_tokens: 100
decision_stop: ["\n"]
decision_top_p: null
decision_top_k: null
```

### 2. 机器人配置 (bot.yaml)

包含机器人基础配置、回复模式配置、关键词配置等。

```yaml
# 机器人基础配置
bot_name: "Yuki"
soul_doc_path: "config/soul_doc/yuki.md"

# 目标配置
target_groups: ["1044284401"]
target_users: ["2162371684"]

# 回复模式
response_modes:
  none: "无回复"
  keyword: "关键词触发"
  at: "@触发"
  at_and_keyword: "@+关键词"
  ai_decide: "AI自主判断"
  random: "随机回复"

default_response_mode: "at_and_keyword"

# 关键词配置
trigger_keywords: ["yuki", "Yuki", "YUKI", "YKTS"]
enable_regex_keywords: true

# 随机回复
random_threshold: 0.1

# 消息处理
max_message_length: 2000
enable_at_reply: true

# 昵称-称呼映射
nickname_address_mapping:
  "Texas": "A酱"
  "Arsvine": "A酱"
enable_nickname_address_injection: true
nickname_address_injection_position: "bottom"
```

### 3. 系统配置 (system.yaml)

包含系统配置、日志配置、WebUI配置等。

```yaml
# 系统配置
log_level: "INFO"
debug: false

# 插件配置
enable_plugins: true

# NAPCat配置
napcat_enabled: true
napcat_ws_uri: "ws://localhost:3001"

# WebUI配置
webui_enabled: false
webui_port: 6099
```

### 配置加载顺序

1. 加载默认配置 `DEFAULT_CONFIG`
2. 依次加载 `ai.yaml`、`bot.yaml`、`system.yaml`
3. 后面加载的配置会覆盖前面的同名配置
4. 所有配置项都有合理的默认值，确保系统正常运行

### 配置验证

配置系统会在初始化时验证配置的有效性，包括：
- 模型名称不能为空
- 灵魂文档必须存在
- 随机阈值必须在0-1之间
- 默认回复模式必须是有效模式
- 触发关键词必须是列表类型
- 昵称-称呼映射表必须是字典类型

### 配置示例文件

每个配置文件都有对应的示例文件（如 `ai.yaml.example`），带有详细注释和默认值，便于用户参考和配置。示例文件不会被机器人加载，您需要复制示例文件并删除 `.example` 后缀才能使用。

## 项目结构

```
bot/
├── config/             # 配置相关
│   ├── prompt/         # 提示词文件目录
│   │   └── should_respond_prompt.txt  # AI决策提示词
│   ├── soul_doc/       # 灵魂文档目录
│   └── settings.py     # 配置加载和管理
├── core/               # 核心功能模块
│   ├── ai_client.py    # AI客户端，处理AI模型调用
│   ├── api_key.py      # API密钥管理
│   ├── conversation_manager.py  # 对话线程管理
│   ├── memory.py       # 记忆系统，处理短期和长期记忆
│   ├── model.py        # 数据模型定义
│   ├── topic_detector.py  # 话题检测
│   └── tracker.py      # 目标对象追踪和触发判断
├── data/               # 数据目录（隐私数据）
│   ├── config/         # YAML配置文件
│   │   ├── ai.yaml     # AI配置
│   │   ├── bot.yaml    # 机器人配置
│   │   ├── system.yaml # 系统配置
│   │   └── *.example   # 配置示例文件
│   └── key             # API密钥文件
├── handlers/           # 事件处理器
│   ├── group_handler.py  # 群聊消息处理
│   └── private_handler.py  # 私聊消息处理
├── utils/              # 工具函数
│   └── unit_test/      # 单元测试脚本
├── __init__.py         # 模块初始化
├── main.py             # 项目入口
└── requirements.txt    # 依赖列表
```

## 核心模块说明

### AI客户端 (ai_client.py)
- 负责与火山方舟AI模型交互
- 管理对话上下文和历史记录
- 处理AI回复的提取和格式化
- 实现对话历史记录的自动获取
- 支持根据消息长度生成智能回复延迟
- 添加消息时间标记，增强上下文理解
- 实现AI决策模型，判断是否应该回复
- 集成对话摘要系统，定期生成聊天摘要
- 支持动态提示词加载，便于维护和更新
- 支持模块化配置，根据配置文件调整AI行为
- 实现记忆系统，管理短期和长期记忆
- 支持多种AI模型配置，包括主模型和决策模型

### 配置系统 (settings.py)
- 安全可靠的配置加载机制
- 支持模块化YAML配置文件（ai.yaml、bot.yaml、system.yaml）
- 独立的默认配置体系，确保配置项完整性
- 敏感数据的掩码处理
- 配置文件不存在、解析错误等异常情况的安全处理
- 支持动态配置加载，无需重启机器人
- 配置项验证机制，确保配置值的有效性
- 支持配置示例文件，便于用户参考和配置
- 模块化配置结构，便于维护和扩展

### 记忆系统 (memory.py)
- 短期记忆：管理近期对话记录
- 长期记忆：存储重要信息
- 上下文管理：维护对话上下文
- 上下文切换检测：根据消息主题变化自动切换上下文
- 话题关联：判断消息与上下文的相关性
- 长期记忆获取和管理
- 对话摘要系统：定期或在获取历史记录后生成聊天摘要
- 支持配置摘要生成的频率和条件
- 支持不同模型用于生成摘要
- 实现记忆重要性评估机制
- 智能历史消息构建：当有摘要时使用摘要+最近消息来减少tokens消耗，优化API调用效果

### 对话管理器 (conversation_manager.py)
- 对话线程识别和创建
- 线程话题分析和更新
- 活跃线程管理和清理
- 支持配置的话题检测间隔

### 目标追踪器 (tracker.py)
- 判断消息是否需要响应
- 关键词匹配和正则表达式支持
- 支持"@+关键词"的或关系
- 上下文相关性判断
- 昵称-称呼映射表管理

### 消息处理器
- **GroupHandler**：处理群聊消息，支持@回复、多群管理
- **PrivateHandler**：处理私聊消息，支持输入状态模拟
- 消息格式优化和清理
- 智能延迟计算，模拟真实聊天体验

## 使用示例

### 群聊场景

#### 关键词触发
```
用户: yuki，你好
机器人[25年22:45]: 你好呀！有什么可以帮助你的吗？
```

#### @触发
```
用户: @Yuki 今天天气怎么样？
机器人[25年22:46]: @用户 今天天气晴朗，温度适宜，适合外出活动！
```

#### 昵称-称呼映射
```
用户: Texas: 你好
机器人[25年22:47]: A酱，你好呀！有什么可以帮助你的吗？
```

### 私聊场景

```
用户: 你能做什么？
机器人[25年22:48]: 我是Yuki，一个智能QQ机器人，可以陪你聊天、回答问题、提供各种帮助。
用户: 那你知道今天是星期几吗？
机器人[25年22:49]: 今天是2025年12月11日，星期四。
```

## 开发指南

### 扩展开发

1. **添加新的配置项**
   - 在 `config/settings.py` 的 `DEFAULT_CONFIG` 中添加默认值
   - 在 `BotSettings` 类中添加对应的配置项
   - 在 `config.yaml.example` 中添加配置项说明

2. **添加新的回复模式**
   - 在 `core/tracker.py` 中添加新的回复模式逻辑
   - 更新 `should_respond` 方法中的判断逻辑

3. **添加新的功能模块**
   - 在 `core/` 目录下创建新的模块文件
   - 在对应的 `__init__.py` 中导出模块
   - 在需要的地方导入使用

4. **添加新的消息处理逻辑**
   - 在 `handlers/` 目录下扩展现有的处理器
   - 或创建新的处理器类

### 测试指南

1. **配置系统测试**
   - 使用 `core/test_config_system.py` 测试配置加载和管理
   - 运行 `python -m bot.core.test_config_system`

2. **功能单元测试**
   - 使用 `utils/unit_test/` 目录下的测试脚本进行单元测试
   - 编写新的测试用例覆盖新增功能

3. **配置值验证**
   - 使用 `test_config_value.py` 验证配置文件中的值是否正确加载
   - 运行 `python test_config_value.py`

### 调试建议

1. **日志查看**：查看 `logs/` 目录下的日志文件，了解机器人运行状态
2. **配置调试**：修改配置文件中的配置项，实时查看效果
3. **单元测试**：使用 `utils/unit_test/` 目录下的测试脚本进行单元测试
4. **配置验证**：使用 `test_config_value.py` 验证配置加载是否正确
5. **代码调试**：使用IDE的调试功能，设置断点查看变量值和执行流程

## 常见问题

### Q: 机器人为什么不回复消息？
A: 请检查以下几点：
   1. 机器人是否已加入目标群组
   2. 群组ID是否已添加到配置文件的 `target_groups` 中
   3. 回复模式是否设置正确
   4. 关键词是否匹配
   5. 回复模式是否支持当前触发方式（@+关键词的或关系）

### Q: 如何修改机器人的名称？
A: 修改配置文件中的 `bot_name` 字段，替换为你想要的机器人名称。

### Q: 如何修改机器人的AI模型？
A: 修改配置文件中的 `model` 字段，替换为可用的火山方舟模型名称。

### Q: 如何保护我的隐私数据？
A: 所有隐私数据（QQ号、群号、API密钥）均存储在 `bot/data/` 目录下，建议：
   1. 将该目录添加到 `.gitignore` 中
   2. 不要将包含隐私数据的配置文件提交到版本控制
   3. 使用 `bot/data/config/config.yaml.example` 作为模板，不包含真实数据

### Q: 如何配置昵称-称呼映射？
A: 在配置文件的 `nickname_address_mapping` 字段中添加昵称到标准称呼的映射，例如：
   ```yaml
   nickname_address_mapping:
     "Texas": "A酱"
     "Arsvine": "A酱"
   ```

### Q: 机器人回复延迟过高怎么办？
A: 可以调整配置文件中的延迟计算参数，或修改 `handlers/group_handler.py` 和 `handlers/private_handler.py` 中的延迟逻辑。

### Q: 如何测试配置系统是否正常工作？
A: 可以使用以下命令测试配置系统：
   ```bash
   # 运行配置系统测试
   python -m bot.core.test_config_system
   
   # 验证配置值是否正确加载
   python test_config_value.py
   ```

### Q: 配置文件不存在时机器人能正常工作吗？
A: 是的，机器人实现了安全可靠的配置加载机制，当配置文件不存在、解析错误或权限问题时，会使用合理的默认值继续运行。

## 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 致谢

- [ncatbot](https://github.com/liyihao1110/ncatbot) - QQ机器人框架
- [火山方舟](https://www.volcengine.com/product/ark) - AI模型服务
- 所有为本项目做出贡献的开发者

## 联系方式

如有问题或建议，欢迎通过以下方式联系：
- GitHub Issues：https://github.com/ArsvineZhu/BionicBot/issues
- 邮箱：2162371684@qq.com

---

**Bionic Bot - 让QQ聊天更智能！** 🚀
