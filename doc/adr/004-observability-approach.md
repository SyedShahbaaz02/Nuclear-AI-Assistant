# 004. Observability Approach

Date: 05-13-2025

## Status

Complete

## Context

The "Ask Licensing" solution will have multiple tiers, including a front-end application, a back-end API implementation,
and a variety of Azure Services.  We need an observability solution that will enable the monitoring and diagnostics of\
the solution.

## Decision

We will use the [Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/fundamentals/overview) family
of services.  These services provide support for:

- Metrics - numerical values that describe an aspect of a system at a particular point in time.
- Logs - Recorded system events. Logs can contain different types of
  data, be structured or free-form text, and they contain a timestamp
- Traces - Distributed tracing allows you to see the path of a request
  as it travels through different services and components.

Tracking of Azure Services can be done simply by configuring the
[Diagnostic Services](https://learn.microsoft.com/en-us/azure/azure-monitor/platform/diagnostic-settings)
for each service.

Metrics, Logs and Traces from application code will be sent to Azure Monitor using
[OpenTelemetry](https://opentelemetry.io) [Language APIs & SDKs](https://opentelemetry.io/docs/languages/)
for the specific languages in use.

Visualization of the data in Azure Monitor can be initially done using:

- [Dashboards](https://learn.microsoft.com/en-us/azure/azure-monitor/visualize/tutorial-logs-dashboards)
  for simpler vizualizations
- [Workbooks](https://learn.microsoft.com/en-us/azure/azure-monitor/visualize/workbooks-overview)
  for more advanced visualization needs
- [Power BI](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/log-powerbi)
  for including external data sources, user feedback captured by the front end.

### Consequences

- Good, because Azure Monitor is ubqiqutous throughout Azure
- Good, because it supports open standards like OpenTelemetry
