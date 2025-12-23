# Ask Licensing Infrastructure as Code

## Manually Running IaC from Local

1. Ensure that you are running from within the `.devcontainer`.

1. Log into your Azure suscription:

    > **Note**: You can use these links to get the
      [Tenant ID](https://portal.azure.us/#view/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/~/Overview) and
      [Subscription ID](https://portal.azure.us/#view/Microsoft_Azure_Billing/SubscriptionsBladeV2)

    ```bash
    az cloud set --name AzureUSGovernment
    az login --tenant <tenant_id_or_name>
    az account set --subscription <subscription_id_or_name>
    ```

1. "What if?" the deployment:

    > **Note**: The `what-if` deployment will return a warning about the streamingapi deployment validation being
    skipped, you can ignore it.
    <!-- markdownlint-disable MD028 -->

    > **Note**: The following command assumes you are deploying to the development environment,
    and references the `dev.bicepparam` file.  If you are deploying into stage, or
    prod instead, make sure to update the command to point to the correct bicep
    parameters file, e.g. `stage.bicepparam`

    ```bash
    az deployment group what-if \
      --resource-group <resource_group_id> \
      --name test_deployment \
      --template-file ./infra/main.bicep \
      --parameters ./infra/dev.bicepparam
    ```

1. Execute the deployment:

    ```bash
    az deployment group create \
      --resource-group <resource_group_id> \
      --name test_deployment \
      --template-file ./infra/main.bicep \
      --parameters ./infra/dev.bicepparam
    ```

### Deployed Resources

- Ingestion/AI Search
  - Storage Containers
  - Log Analytics Workspace
  - Application Insights
  - Search Service
  - Azure OpenAI
  - App Service Plan
  - Web App

### Configuration of Deployed Resources

There is a single file `configure.py` that will deploy all necessary configurations of resources that are deployed by
bicep above. It is intended that this be the single entry point for configuration based deployments. So, as new
configurations are added for new resources, the code and structure should be updated to accomodate the additions.

#### The `.env` File

The .env file will store all environment variables that are needed by the configuration script.

In order to run the configuration script locally, create a copy of the `.env.*.example` file that best fits your needs
(currently only the dev file exists) and rename it to `.env`. Fill in the values for the keys that are appropriate for
your deployment.

#### Using the Proper Credentials

There are two methods to setting up the credentials for configuration execution.

1. A Service Principal can be used by uncommenting the environment variables in the `.env` file that are associated with
the Service Principal configuration.

1. Log into Azure using the steps [above](#manually-running-iac-from-local). The code will automatically create an
AzureCliCredential.

If both methods are used, the Service Principal will take precedence when the script creates and uses the credentials.

#### The Deployment Script

The deployment script is idempotent and can run multiple times. Note that at the end of the configuration deployment the
indexer will run automatically if this is the first time that it is deployed.

If modifications are made to the configuration files after initial deployment, it is likely that the indexer will need
to be manually executed to capture the updates.

From the project root:

```bash
cd infra/config
pip install -r requirements.txt
python configure.py
```

#### Deployed Configurations

##### AI Search

The configuration script will create the following resources in the AI Search instance:

1. Index - `nureg-index`

1. Data Source - `nureg-datasource`

1. Skillset - `nureg-skillset`

1. Indexer - `nureg-indexer`
