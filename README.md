# Adoption Slack Alerts

### A serverless Azure Function for Application Insights monitoring and alerts
This project was forked from [et-slack-alerts](https://github.com/hmcts/et-slack-alerts)

## Overview

This is a timer-trigger based Azure Function App written in Python to monitor an Azure-based application for any given event (in our case, we focused on exceptions). If events have occurred, it will send alerts to a given slack channel. 

It was *deliberately designed* to be easily reusable and extendable by other teams. The code should be extremely easy to read and work with, even with little or no Python understanding.

### Functionality
The function is scheduled to run every X minutes (customisable) and performs the following tasks:
- Authenticates with an Azure Key Vault to retrieve relevant environment variables.
- Queries application insights to capture all log entries returned for a given query and timescale (both customisable).
- When alert condition meets:
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

## recommend to create the key vault on Azure portal, and choose Permission model = "Vault access policy" and grant yourself with all permission, otherwise you won't able to make any changes after creation
az keyvault create --name "adop-slack-alerts" --resource-group "adop-slack-alerts"
 
az storage account create --name "adopslackalertsstorage" --location "uksouth" --resource-group "adop-slack-alerts" --sku Standard_LRS
 
az functionapp create --resource-group "adop-slack-alerts" --consumption-plan-location "uksouth" --runtime python --runtime-version 3.11 --functions-version 4 --name "adop-slack-alerts" --os-type linux --storage-account "adopslackalertsstorage"
```

Notes: add tagging if needed
```
--tags expiresAfter=3000-01-01 application=adoption BuiltFrom=https://github.com/hmcts/adoption-slack-alerts businessArea=CFT environment=staging
```

See [here](https://github.com/hmcts/adoption-shared-infrastructure/blob/master/application-insights-access.tf)
for infrastructure required for Application Insights access.

### Add Managed Identity to the function app
From the Azure portal:
- Navigate to the adop-slack-alerts function app
- Settings -> Identity
- Select System Assigned
- Toggle Status on
- Copy the ID for later use
- Save

### Add function app to the key vault
From the Azure portal:
- Navigate to the adop-slack-alerts key vault
- Access policies
- Create and add the function ID
- If this option is not available then you can either: 
  - ask platops to create the access 
  - **OR** Recreate the key vault with "Permission model = Vault access policy" and grant yourself with all permission.
- You will also need to ensure that the Function App has the proper access:
   - Assign a managed identity to your Function App.
   - Navigate to `Key Vault` -> `Access Policies` -> `Add Access Policy`. Select `Get` for secrets.
   - For `Select principal`, choose your Function App's identity.
   - Navigate to your Application Insights resource -> `Access Control (IAM)` -> `Add role assignment`.
   - Select the `Monitoring Reader` role and assign it to your Function App's managed identity.
   - This allows the function to query Application Insights using Azure AD authentication.

## Development
### Local Setup
1. Clone the repository
```bash
git clone https://github.com/hmcts/adop-slack-alerts.git
```
2. Open the folder and install dependencies
```bash
cd <wherever you cloned it>

# (optional) install a virtual environment using e.g. venv>
python3 -m venv .venv
source .venv/bin/activate
# end of optional

pip install -r requirements.txt
```

3. Install Azurite
```bash
npm install -g azurite
```
(Optional) if you don't have permission to install globally, you can change the directory npm global to somewhere you have permission, e.g. ~/

```bash
# check your npm global directory
npm config get prefix
# change it to somewhere you have permission, e.g. ~/npm
npm config set prefix ~/npm
# check your npm global directory has been changed
npm config get prefix     
```

4. Create local.settings.json file in alerts folder
```json
{
    "IsEncrypted": false,
    "Values": {
      "FUNCTIONS_WORKER_RUNTIME": "python",
      "AzureWebJobsFeatureFlags": "EnableWorkerIndexing",
      "AzureWebJobsStorage": "UseDevelopmentStorage=true"
    }
}
```

### Local Testing
First start Azurite in another tab (with npx if needed)
```bash
azurite --silent .azurite
````

To install azure functions core tools, follow the instructions [here](https://learn.microsoft.com/en-us/azure/azure-functions/functions-core-tools-reference).

To learn Azure function [here](https://learn.microsoft.com/en-us/azure/azure-functions/functions-get-started?pivots=programming-language-python) 

To test function locally:
```bash
# From the alerts directory
cd alerts
func start
```

## Deployment

To deploy the function to Azure:

```bash
# From the alerts directory
cd alerts
func azure functionapp publish adop-slack-alerts
```

### Contributing

Feel free to send a PR with any possible improvements.
