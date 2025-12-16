from mcp_agent.config import Settings
import json

def load_settings_from_json(json_config: str) -> Settings:
    config_data = json.loads(json_config)
    config_data.pop('$schema', None)
    return Settings.model_validate(config_data)
