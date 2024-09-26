import os
import litellm
from litellm import embedding, completion

"""
Setting Env variables
LAGO_API_KEY : LAGO's API Key
LAGO_API_BASE : LAGO API > Call from LiteLLM URL (Default Port:3000)
LAGO_API_EVENT_CODE : Lago's Billable Metric Code
LITELLM_LOG : LiteLLM Log Level
"""
# Setting LiteLLM Env
os.environ["LITELLM_LOG"] = "DEBUG" # LiteLLM Log Level

# Setting LAGO Env
os.environ["LAGO_API_KEY"] = "lago-api-key"
os.environ["LAGO_API_BASE"] = "lago-api-url"
os.environ["LAGO_API_EVENT_CODE"] = "dcjeon-metric"
os.environ["LAGO_API_CHARGE_BY"] = "end_user_id" # end_user_id | user_id | team_id

# Additional Setting about LiteLLM
# litellm.return_response_headers = True
# litellm.set_verbose=True # Deprecated
litellm.success_callback = ["lago"] # Set LiteLLM Success Callback

# LiteLLM's API Key
EMBEDDING_MODEL_API_KEY = "litellm-embedding-model-api-key"
LLM_MODEL_API_KEY = "llm-api-key"

LITELLM_API_BASE = "litellm-api-url" # LiteLLM API URL (Default Port : 4000)
LAGO_EXTERNAL_SUBSCRIPTION_ID = "lago-external-subscription-id" # Lago User's External Subscription ID

# LLM Input Data
DATA = {
    "role": "user",
    "content": "def print_hello_world():"
}

"""
HuggingFace Embedding Model Format
@param model : Public Model Name in LiteLLM
@param api_key : API Key in LiteLLM
@param input : Input Value
@param api_base : LiteLLM URL
"""
# response = embedding(
#     model="openai/kserve/gte-large/v1",
#     api_key=EMBEDDING_MODEL_API_KEY,
#     proxy_server_request={"body": {"user": LAGO_EXTERNAL_SUBSCRIPTION_ID}},
#     input=["Macbook is great laptop computer.", "I love MacBook."],
#     api_base=LITELLM_API_BASE
# )

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
  api_base=LITELLM_API_BASE,
  api_key=LLM_MODEL_API_KEY,
  proxy_server_request={"body": {"user": LAGO_EXTERNAL_SUBSCRIPTION_ID}}
)

print(response)
