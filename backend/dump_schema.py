from app.modules.auth.schemas import RegisterRequest
import json
print(json.dumps(RegisterRequest.model_json_schema(), indent=2))
