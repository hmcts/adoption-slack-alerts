import logging
import azure.functions as func
from datetime import timedelta
# import requests
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.monitor.query import LogsQueryClient, LogsQueryStatus

# Replace with your Azure Key Vault URL
key_vault_url = "https://adop-slack-alert.vault.azure.net/"

# Authenticates using azure
credential = DefaultAzureCredential()

# Create a SecretClient to interact with the Azure Key Vault
secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

# Create a LogsQueryClient for Application Insights queries using Azure AD auth
logs_client = LogsQueryClient(credential)

# Get secrets from Azure Key Vault
try:
    workspace_id = secret_client.get_secret('app-insights-workspace-id').value
    slack_webhook_url = secret_client.get_secret('slack-webhook-url').value.strip()
    tenant_id = secret_client.get_secret('tenant-id').value
    resource_group_name = secret_client.get_secret('resource-group-name').value
    app_insights_resource_name = secret_client.get_secret('app-insights-resource-name').value
    subscription_id = secret_client.get_secret('subscription-id').value

    # Validate webhook URL format
    if not slack_webhook_url.startswith('https://hooks.slack.com/services/'):
        logging.error(f"Invalid Slack webhook URL format: {slack_webhook_url[:50]}...")
    logging.info(f"Loaded webhook URL: {slack_webhook_url[:40]}...")
except Exception as e:
    logging.error(f"Issue communicating with keyvault: {e}")
    exit(1)

def query_application_insights(query: str, timsSpan: int):
    try:
        response = logs_client.query_workspace(
            workspace_id=workspace_id,
            query=query,
            timespan=timedelta(minutes=timsSpan)
        )

        if response.status == LogsQueryStatus.SUCCESS:
            # Convert the response to match the old format
            result = {
                'tables': [{
                    'rows': []
                }]
            }

            # Extract rows from the response
            if response.tables:
                table = response.tables[0]
                for row in table.rows:
                    result['tables'][0]['rows'].append(list(row))

            logging.info(result)
            return result
        else:
            logging.error(f"Query failed with status: {response.status}")
            return {'tables': [{'rows': []}]}
    except Exception as e:
        logging.error(f"Error querying Application Insights: {e}")
        return {'tables': [{'rows': []}]}


# Function to query Application Insights using Azure AD authentication
def query_application_insights_proxy_count():
    query = """union(
    traces 
    | where message has '/la-portal/kba-case-ref 429: x-forwarded-for Header contains ' 
    | parse message with '/la-portal/kba-case-ref 429: x-forwarded-for Header contains ' noOfProxy ' IP addresses' 
    | where toint(noOfProxy) != 3 
    | project TimeGenerated = timestamp, noOfProxy
    """
    return query_application_insights(query, 5)

app = func.FunctionApp()

@app.function_name(name="proxyAlert")
@app.schedule(schedule="0 */5 * * * *", arg_name="AzureTrigger", run_on_startup=True, use_monitor=False)
def proxyAlert(AzureTrigger: func.TimerRequest) -> None:
    if AzureTrigger.past_due:
        logging.info('The timer is past due!')

    query_data = query_application_insights_proxy_count()
    logging.info(query_data)
    logging.info('Python timer trigger function executed.')
    return