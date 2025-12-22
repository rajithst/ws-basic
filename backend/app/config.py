from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AzureOpenAISettings(BaseModel):
    endpoint: str = Field(default="https://your-azure-openai-endpoint.openai.azure.com")
    deployment: str = Field(default="your-deployment")
    api_key: str = Field(default="your-key")


class AzureSpeechSettings(BaseModel):
    key: str = Field(default="your-speech-key")
    region: str = Field(default="your-region")


class STTSettings(BaseModel):
    endpoint: str = Field(default="https://your-stt-endpoint")
    api_key: str = Field(default="your-stt-key")


class Settings(BaseSettings):
    azure_openai: AzureOpenAISettings = AzureOpenAISettings()
    azure_speech: AzureSpeechSettings = AzureSpeechSettings()
    stt: STTSettings = STTSettings()

    class Config:
        env_nested_delimiter = "__"
        env_prefix = ""
        extra = "ignore"


def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
