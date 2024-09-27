import os
import uuid
import litellm
from litellm import embedding, completion
from lago_python_client.client import Client
from lago_python_client.exceptions import LagoApiError
from lago_python_client.models.event import Event
"""
Setting Env variables
"""
# Setting LiteLLM Env
os.environ["LITELLM_LOG"] = "DEBUG"

# Additional Setting about LiteLLM
# litellm.return_response_headers = True
# litellm.set_verbose=True  # Deprecated

LLM_MODEL_API_KEY = "llm-model-api-key" # API Key
LITELLM_API_BASE = "litellm-api-url" # LiteLLM API URL (Default Port:4000)
LAGO_CLIENT_API_KEY = "lago-client-api-key" # Lago Client API Key
LAGO_API_BASE = "lago-api-url" # Lago API URL (Default Port:3000)

# LLM Input Data
DATA = {
    "role": "user",
    "content": "def print_hello_world():"
}

"""
HuggingFace StarCode LLM Model Format
@param model : Public Model Name in LiteLLM
@param messages : Input Value
@param api_base : LiteLLM URL
@param api_key : API Key in LiteLLM
"""
response = litellm.completion(
  model="openai/openai/starcoder",
  messages=[DATA],
  api_base = LITELLM_API_BASE,
  api_key= LLM_MODEL_API_KEY
)

print("# LiteLLM API Usage Response : {}".format(response.usage))

lago_client = Client(
    api_key=LAGO_CLIENT_API_KEY,
    api_url=LAGO_API_BASE
)

LAGO_EXTERNAL_SUBSCRIPTION_ID="lago-external-subscription-id" # Lago External Subscription ID
LAGO_METRIC_CODE="dcjeon-metric" # Lago Billable Metric Code

# Create Event about Input Tokens (Prompt Tokens)
lago_input_properties = {
    "type": "input",
    "model": "openai/starcoder",
    "tokens": response.usage.prompt_tokens
}

try:
    lago_input_event = Event(
        transaction_id=str(uuid.uuid4()),
        external_subscription_id=LAGO_EXTERNAL_SUBSCRIPTION_ID,
        code=LAGO_METRIC_CODE,
        properties=lago_input_properties
    )
except LagoApiError as e:
    print("Fail to Make Lago Event Format : {}".format(lago_input_properties["type"]))
    raise LagoApiError()

try:
    lago_input_event_response = lago_client.events.create(lago_input_event)
except LagoApiError as e:
    print("Fail to Create Lago Input Event...")
    raise LagoApiError()

print("Success to Create Lago Input Event.\n##### LAGO EVENT OUTPUT #####\n{}\n#########################".format(lago_input_event_response))

# Create Event about Output Tokens (Completion Tokens)
lago_output_properties = {
    "type": "output",
    "model": "openai/starcoder",
    "tokens": response.usage.completion_tokens
}

try:
    lago_output_event = Event(
        transaction_id=str(uuid.uuid4()),
        external_subscription_id=LAGO_EXTERNAL_SUBSCRIPTION_ID,
        code=LAGO_METRIC_CODE,
        properties=lago_output_properties
    )
except LagoApiError as e:
    print("Fail to Make Lago Event Format : {}".format(lago_output_properties["type"]))

try:
    lago_output_event_response = lago_client.events.create(lago_output_event)
except LagoApiError as e:
    print("Fail to Create Lago Output Event...")
    raise LagoApiError()

print("Success to Create Lago Output Event.\n##### LAGO EVENT OUTPUT #####\n{}\n#########################".format(lago_output_event_response))
