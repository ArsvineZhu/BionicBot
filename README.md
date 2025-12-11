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

### 高级功能
- 📝 **多回复模式**：支持多种回复触发模式（关键词、@、AI自主判断等）
- 🔑 **关键词触发**：支持正则表达式关键词匹配，支持"@+关键词"的或关系
- 🎯 **目标对象管理**：可配置目标群组和用户
- 🧠 **记忆系统**：支持短期记忆和长期记忆
- 📋 **对话线程管理**：自动识别和管理不同对话线程
- 🏷️ **话题检测**：智能检测对话话题，保持话题相关性
- 🔧 **可配置性**：所有功能均支持通过YAML配置文件调整
- 🏷️ **昵称-称呼映射**：支持昵称到标准称呼的映射，增强回复的个性化

### 优化特性
- 🕵️ **隐私保护**：配置文件和密钥文件集中管理在`bot/data/`目录，保护隐私数据
- 📱 **输入状态模拟**：私聊时显示"输入中"状态，提升用户体验
- ✨ **格式优化**：自动清理AI回复中的冗余信息，确保回复格式规范
- 🚀 **性能优化**：优化状态管理，减少不必要的API调用
- 🔒 **配置安全**：实现了安全的配置加载机制，支持配置文件不存在、解析错误等异常情况的安全处理
- 🧪 **完善测试**：编写了全面的单元测试，确保配置系统的正确性和可靠性

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
git clone https://github.com/yourusername/bionic-bot.git
cd bionic-bot
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
   - 复制 `bot/data/config/config.yaml.example` 为 `bot/data/config/config.yaml`
   - 根据需要修改配置项
   - 将API密钥写入 `bot/data/key` 文件

5. **启动机器人**
```bash
# 使用模块方式启动（推荐）
python -m bot.main

# 或直接运行脚本
python bot/main.py
```

## 配置说明

配置文件位于 `bot/data/config/config.yaml`，采用YAML格式，支持动态调整，无需重启机器人即可生效。配置系统实现了安全可靠的加载机制，当配置文件不存在、解析错误或权限问题时，会使用合理的默认值继续运行。

### 配置项分类

#### 1. 目标对象配置
```yaml
# 机器人需要响应的目标群组ID列表（字符串类型）
target_groups: ["123456789"]
# 机器人需要响应的目标用户ID列表（私聊场景，字符串类型）
target_users: ["987654321"]
```

#### 2. AI模型配置
```yaml
# AI模型名称，用于指定使用哪个模型进行对话生成
model: "doubao-seed-1-6-lite-251015"
```

#### 3. 机器人基础配置
```yaml
# 机器人名称，用于在对话中标识自己
bot_name: "Yuki"
```

#### 4. 记忆系统配置
```yaml
# 短期记忆最大消息数，超过该数量的旧消息将被自动清理
short_term_memory_limit: 50
# 长期记忆存储路径
long_term_memory_path: "data/long_term_memory.json"
```

#### 5. 灵魂文档配置
```yaml
# 灵魂文档路径，包含机器人的身份、性格、知识背景等核心定义
soul_doc_path: "config/soul_doc/yuki.md"
```

#### 6. 回复模式配置
```yaml
# 支持的回复模式
response_modes:
  none: "无回复"
  keyword: "关键词触发"
  at: "@触发"
  at_and_keyword: "@+关键词"  # 被@或包含关键词就回复（或关系）
  ai_decide: "AI自主判断"
  random: "随机回复"

# 默认回复模式
default_response_mode: "at_and_keyword"
```

#### 7. 触发配置
```yaml
# 触发机器人回复的关键词列表
trigger_keywords: ["yuki", "Yuki"]
# 随机回复模式下的触发概率（0-1之间）
random_threshold: 0.1
# 是否启用正则表达式关键词匹配
enable_regex_keywords: true
```

#### 8. 消息处理配置
```yaml
# 单条消息的最大长度限制
max_message_length: 2000
# 是否在回复时@原发送者
enable_at_reply: true
```

#### 9. 上下文管理配置
```yaml
# 上下文超时时间（小时）
context_timeout_hours: 2
# 上下文切换阈值（0-1之间）
context_switch_threshold: 0.2
# 上下文切换的最小消息数阈值
context_switch_min_messages: 50
# 上下文切换时分析的最近消息数量
context_switch_analyze_count: 20
```

#### 10. 话题检测配置
```yaml
# 话题相关性阈值（0-1之间）
topic_relevance_threshold: 0.3
# 话题检测间隔（消息数）
topic_detection_interval: 50
```

#### 11. 对话线程配置
```yaml
# 对话线程超时时间（分钟）
thread_timeout_minutes: 60
# 对话线程清理间隔（分钟）
thread_cleanup_interval: 60
```

#### 12. 响应优化配置
```yaml
# 是否启用上下文关联响应
context_related_response_enabled: true
# 上下文关联响应的超时时间（分钟）
context_related_timeout_minutes: 20
```

#### 13. 历史记录配置
```yaml
# 是否启用历史记录获取功能
enable_history_retrieval: true
# 历史记录获取数量限制
history_retrieval_limit: 50
# 历史记录最大总长度（字符数）
history_retrieval_max_length: 1000
# 是否在收到首条消息时获取历史记录
history_retrieval_on_first_message: true
# 是否在新会话开始时获取历史记录
history_retrieval_on_new_session: true
```

#### 14. 长期记忆配置
```yaml
# 构建系统提示时获取的长期记忆数量
long_term_memory_limit: 50
# 长期记忆的重要性默认值
long_term_memory_default_importance: 1.0
```

#### 15. 昵称-称呼映射表配置
```yaml
# 昵称-称呼映射表，用于在系统提示中注入用户昵称和对应的称呼信息
nickname_address_mapping:
  "Texas": "A酱"
  "Arsvine": "A酱"
  "Yuki": "Yuki"

# 是否启用昵称-称呼映射表注入
enable_nickname_address_injection: true
# 昵称-称呼映射表在系统提示中的注入位置
nickname_address_injection_position: "bottom"
```

## 项目结构

```
bot/
├── config/             # 配置相关
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
│   └── key             # API密钥文件
├── handlers/           # 事件处理器
│   ├── group_handler.py  # 群聊消息处理
│   └── private_handler.py  # 私聊消息处理
├── utils/              # 工具函数
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

### 配置系统 (settings.py)
- 安全可靠的配置加载机制
- 支持YAML格式配置文件
- 独立的默认配置体系，确保配置项完整性
- 敏感数据的掩码处理
- 配置文件不存在、解析错误等异常情况的安全处理

### 记忆系统 (memory.py)
- 短期记忆：管理近期对话记录
- 长期记忆：存储重要信息
- 上下文管理：维护对话上下文
- 上下文切换检测：根据消息主题变化自动切换上下文
- 话题关联：判断消息与上下文的相关性
- 长期记忆获取和管理

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
- GitHub Issues：https://github.com/yourusername/bionic-bot/issues
- 邮箱：your.email@example.com

---

**Bionic Bot - 让QQ聊天更智能！** 🚀