from dataclasses import dataclass
import os


@dataclass
class Settings:
    app_host: str = "0.0.0.0"
    app_port: int = 5050
    debug: bool = True

    default_period: str = "5y"
    default_interval: str = "1d"
    model_path: str = os.path.join(os.path.dirname(__file__), "models")


settings = Settings()
