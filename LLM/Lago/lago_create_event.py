from lago_python_client.client import Client
from lago_python_client.exceptions import LagoApiError
from lago_python_client.models.event import Event
import uuid

LAGO_CLIENT_API_KEY = "lago-api-key"
LAGO_API_BASE = "lago-api-url" # Lago API URL (Default Port:3000)

# Set Lago Client
client = Client(
    api_key=LAGO_CLIENT_API_KEY,
    api_url=LAGO_API_BASE
)

LAGO_EXTERNAL_SUBSCRIPTION_ID="lago-external-subscription-id" # Lago External Subscription ID
LAGO_METRIC_CODE="dcjeon-metric" # Lago Billable Metric Code

# Sample of Properties in Lago's Event
lago_properties = {
    "type": "output",
    "model": "openai/starcoder",
    "tokens": 16376
}

# Make Lago's Event Data
try:
    lago_event = Event(
        transaction_id=str(uuid.uuid4()), # Generate Random Transaction ID
        external_subscription_id=LAGO_EXTERNAL_SUBSCRIPTION_ID,
        code=LAGO_METRIC_CODE,
        properties=lago_properties
    )
except LagoApiError:
    print("Fail to Make Lago Event Format")
    raise LagoApiError()

# Create Lago's Event
try:
    event_output = client.events().create(lago_event)
except LagoApiError:
    print("Fail to Create Lago Event")
    raise LagoApiError()

print(event_output)
