# 005. Azure Resource Deployment

Date: 05-14-2025

## Status

Complete

## Context

The "Ask Licensing" solution depends on specific Azure resources (e.g., Azure OpenAI, Azure AI Search,
Azure Functions, etc.) to be deployed into designated resource groups in the target Constellation Azure Government
Cloud subscription.  These resource groups are used as the "Development", "Staging" and eventually "Production"
environments, and possibly others.

We need to ensure that the deployment of those resources into the target environments is reliable, repeatable, and
consistent and that the deployed resource configurations meet the specific needs of the solution.

That said, Constellation has specific policies that require designated individuals with the appropriate permissions to
deploy network configurations, assign Role Base Access Control policies, etc. and as such those specific activities
may still need to be done manually.  We will make every effort to identify those restrictions, and either provide
scripts to be run, or if need be step-by-step documentation to ensure that those additional configurations can be
completed correctly.

## Decision

![Deployment Architecture](../assets/deployment/deployment_architecture.drawio.png)

We will use:

- Bicep files, committed into the repository for all Azure Resources required by the solution
- Additional python code to perform additional configuration on the resources that can't be done via bicep.
- Azure DevOps Pipelines to:
  - Deploy the Azure resources defined in the bicep files
  - Execute the additional configuration scripts
  - Deploy the application code into the appropriate Azure resources
  - Perform tests against the deployed solution to verify it is functioning correctly
- Azure DevOps Variable Groups to provide access to the configuration values and secrets needed for deployment
- TBD: We may need to provide additional scripts, or worse case step-by-step documentation for manual configuration of
  policy assignments, network endpoints, etc. as required by Constellation policy.

Other options that were considered:

- Manual Deployment via the Azure Portal
- Manual Deployment using the Azure CLI

### Consequences

- Good, because Bicep ensures reliable and repeatable configuration of the Azure Resources needed for the deployment
- Good, because Azure DevOps Pipelines can deploy resources into the target Azure environments
  (e.g., Development, Staging, or Production) using credentials and access to secrets that individual
  developers don't have.
- Bad, because we will likely still require some manual post-deployment configuration via either the portal or via
  manually executed scripts that leverage the Azure CLI to configure Network Endpoints, RBAC, etc. due to Constellation
  policies
