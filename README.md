# Adoption Slack Alerts

### A serverless Azure Function for Application Insights monitoring and alerts
This project was forked from [et-slack-alerts](https://github.com/hmcts/et-slack-alerts)

## Overview

This is a timer-trigger based Azure Function App written in Python to monitor an Azure-based application for any given event (in our case, we focused on exceptions). If events have occurred, it will send alerts to a given slack channel. 

It was *deliberately designed* to be easily reusable and extendable by other teams. The code should be extremely easy to read and work with, even with little or no Python understanding.

### Functionality
The function is scheduled to run every 5 minutes (customisable) and performs the following tasks:
- Authenticates with an Azure Key Vault to retrieve relevant environment variables.
- Queries application insights to capture all log entries returned for a given query and timescale (both customisable).
- Filters unique operations (some log entries cover multiple operations, which can clutter up the returned logs.)
- Sends a second query to application insights to get the entire log history of a given operation.
- Builds a slack message containing a formatted table of unique event triggering operations in the given timeframe, with generated inline links to the relevant log histories.
- Sends a slack alert (via an environment variable-defined webhook url)

### Prerequisites
- [Azure Functions Core Tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=macos%2Cisolated-process%2Cnode-v4%2Cpython-v2%2Chttp-trigger%2Ccontainer-apps&pivots=programming-language-csharp#install-the-azure-functions-core-tools)
- [Python 3.7+](https://www.python.org/downloads/)
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
- [Azurite (for local development)](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite?tabs=npm%2Cblob-storage)
- An Azure account/subscription
- An [Azure Key Vault](https://azure.microsoft.com/en-gb/products/key-vault)
- An [Application Insights](https://learn.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview?tabs=net) instance you want to monitor

## Environment Variables
This function requires several environment variables (defined within the given keyvault)
- `app-insights-workspace-id` - The workspace ID of the Application Insights instance. This can be found in the Properties section of your Application Insights resource.
- `slack-webhook-url` - A slack webhook URL for you to send messages to. For this part you will likely need to contact myself (@Danny on Slack) or a Slack administrator to get a custom slack 'app' set up. This is much more trivial than it sounds, a few clicks at most.
- `tenant-id` - Standard for the entire organisation.
- `resource-group-name` - The resource group name that the Application Insights instance is stored within.
- `app-insights-resource-name` - The name of the Application Insights instance.
- `subscription-id` - The subscription id that the Application Insights instance is stored within.

**Note:** This application uses Azure AD authentication via managed identity to query Application Insights. API keys are deprecated and will be retired by March 31, 2026.

## Slack Setup
- Create a new Slack channel that will be destination for alerts.
- Create a new Slack App from https://api.slack.com/apps (ensure you set the workspace to 'HMCTS DTS').
- Create an Incoming Webhook for your new app. Note this action will trigger an approval request before it can be completed.

## Azure Installation
### Create Azure resources
```
az group create --name "adop-slack-alerts" --location "uksouth"
 
az keyvault create --name "adop-slack-alerts" --resource-group "adop-slack-alerts"
 
az storage account create --name "adopslackalertsstorage" --location "uksouth" --resource-group "adop-slack-alerts" --sku Standard_LRS
 
az functionapp create --resource-group "adop-slack-alerts" --consumption-plan-location "uksouth" --runtime python --runtime-version 3.11 --functions-version 4 --name "adop-slack-alerts" --os-type linux --storage-account "adopslackalertsstorage"
```

See [here](https://github.com/hmcts/adoption-shared-infrastructure/blob/master/application-insights-access.tf)
for infrastructure required for Application Insights access.

### Add Managed Identity to the function app
From the Azure portal:
- Navigate to the adop-slack-alerts function app
- Settings -> Identity
- Select System Assigned
- Toggle Status on
- Save

### Add function app to the key vault
From the Azure portal:
- Navigate to the adop-slack-alerts key vault
- Access policies
- Create
- If this option is not available then you will need platops to create the access

### Add tags to function app
From the Azure portal:
- Navigate to the adop-slack-alerts function app
- Add tags

```
environment: staging
Application: adoption
businessArea: CFT
ExpiresAfter: 3000-01-01
builtFrom: https://github.com/hmcts/adop-slack-alerts
```

## Development
### Setup
#### Install Azurite
```
npm install -g azurite
```

## Installation
1. Clone the repository
```
git clone https://github.com/hmcts/adop-slack-alerts.git
```
2. Open the folder and install dependencies
```
cd [wherever you cloned it]

<optionally install a virtual environment using e.g. venv>
python3 -m venv .venv
source .venv/bin/activate
</optionally>

pip install -r requirements.txt
```
3. Follow the [instructions here](https://learn.microsoft.com/en-us/azure/azure-functions/functions-get-started?pivots=programming-language-python) to get it running locally and published to a given resource group. If you need any help, feel free to reach out.
4. You will also need to ensure that the Function App has the proper access:
- Assign a managed identity to your Function App.
- Navigate to `Key Vault` -> `Access Policies` -> `Add Access Policy`. Select `Get` for secrets.
- For `Select principal`, choose your Function App's identity.
- Navigate to your Application Insights resource -> `Access Control (IAM)` -> `Add role assignment`.
- Select the `Monitoring Reader` role and assign it to your Function App's managed identity.
  - This allows the function to query Application Insights using Azure AD authentication.

## Deployment

To deploy the function to Azure:

```bash
# From the alerts directory
cd alerts
func azure functionapp publish <your-function-app-name>
```

### Todo
- Investigate whether it's worth adding a slight delay on log checking to compensate for [Azure's logging latency](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/data-ingestion-time).
- Use the same link generation approach for [Azure Monitor Transaction Logs](https://learn.microsoft.com/en-us/azure/azure-monitor/app/transaction-diagnostics).

### Contributing

Feel free to send a PR with any possible improvements.
