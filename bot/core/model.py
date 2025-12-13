#! python3.13
from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass(frozen=True)
class MSG_TYPE:
    TEXT = "text"
    IMAGE_URL = "image_url"


@dataclass(frozen=True)
class ABILITY:
    DISABLED = "disabled"
    ENABLED = "enabled"
    AUTO = "auto"


@dataclass(frozen=True)
class EFFORT:
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class ROLE_TYPE:
    USER = "user"
    SYSTEM = "system"
    ASSIST = "assistant"
    TOOL = "tool"


@dataclass
class _Bubble:
    """发送出去的一个消息气泡"""

    msg: str
    msg_type: str = MSG_TYPE.TEXT
    """supported values are: `text`, `image_url`"""

    @property
    def export(self) -> Dict[str, str]:
        return {"type": self.msg_type, self.msg_type: self.msg}


@dataclass
class Content:

    msg: str

    @property
    def export(self) -> str:
        return self.msg


@dataclass
class Message:
    """以特定身份发出的消息，包含一个 Content"""

    content: Content
    role: str = ROLE_TYPE.USER
    """supported values are: `system`, `assistant`, `user`, `tool`"""

    @property
    def export(self) -> Dict[str, str | List[Dict[str, str]]]:
        return {"role": self.role, "content": self.content.export}


@dataclass
class FunctionCalling:
    """函数调用定义"""

    name: str
    description: str
    properties: Dict[str, Dict[str, str]]
    """{
            "location": {
                "type": "string",
                "enum": ["北京", "上海"],
                "description": "城市名称，如北京、上海（仅支持国内地级市）",
            }
       }"""
    required_properties: List[str]

    @property
    def export(self) -> Dict[str, str | Dict[str, str | List[str] | Dict[str, Any]]]:
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.properties,
                "required": self.required_properties,
            },
        }


@dataclass
class ApiModel:
    """向火山方舟 API 发送的标准请求模型"""

    model: str
    messages: List[Message]
    previous_response_id: str | None = None
    stream: bool = False
    thinking: str = ABILITY.ENABLED
    caching: bool = False
    store: bool = False
    reasoning: str = EFFORT.MEDIUM
    temperature: float = 1.0  # type: ignore
    tools: List[Dict[str, Any]] = field(default_factory=list)
    max_tokens: int | None = None
    stop: List[str] | None = None
    top_p: float | None = None
    top_k: int | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    response_format: Dict[str, Any] | None = None

    _temperature: float = 1.0

    @property
    def temperature(self) -> float:
        return self._temperature

    @temperature.setter
    def temperature(self, value: float) -> None:
        self._temperature = min(max(value, 0), 2)

    @property
    def export(self) -> Dict[str, Any]:
        ret = {
            "model": self.model,
            "input": [i.export for i in self.messages],
        }
        
        # 添加可选参数（如果提供）
        if self.previous_response_id is not None:
            ret["previous_response_id"] = self.previous_response_id
        
        if self.stream:
            ret["stream"] = self.stream
        
        # 思考过程参数（某些模型支持）
        if self.thinking != ABILITY.ENABLED:
            ret["thinking"] = {"type": self.thinking}
        
        # 缓存参数（某些模型支持）
        if self.caching:
            ret["caching"] = {"type": ABILITY.ENABLED}
        
        # 生成参数
        if self.temperature != 1.0:
            ret["temperature"] = self.temperature
        
        # 推理参数（某些模型支持）
        if self.reasoning != EFFORT.MEDIUM:
            ret["reasoning"] = {"effort": self.reasoning}
        
        # 工具调用参数
        if self.tools:
            ret["tools"] = self.tools
        
        # 火山方舟API不支持以下参数，暂时注释掉
        # if self.max_tokens is not None:
        #     ret["max_tokens"] = self.max_tokens
        # if self.stop is not None:
        #     ret["stop"] = self.stop
        # if self.top_p is not None:
        #     ret["top_p"] = self.top_p
        # if self.top_k is not None:
        #     ret["top_k"] = self.top_k
        # if self.presence_penalty is not None:
        #     ret["presence_penalty"] = self.presence_penalty
        # if self.frequency_penalty is not None:
        #     ret["frequency_penalty"] = self.frequency_penalty
        # if self.response_format is not None:
        #     ret["response_format"] = self.response_format
        
        return ret
