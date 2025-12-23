# Working with the Chat Service Endpoint Locally

This document explains how to work with the Chat Service endpoint locally in the VSCode Dev Container development
environment. This discussion adds context to the [Application Web documentation](../README.md) and is specific to
the Chat Service endpoint.

## Running (Debugging) the Web App Locally

### Pre-Requisites

Even though you can run the web locally, there are a few dependencies that you need to provide:

- An Azure AI Search Instance with the necessary indexes.
- An Azure OpenAI Instance with the necessary models deployed.
- The Aspire Dashboard running in a container if you want to view the telemetry data. See
  [Using Aspire Dashboard Locally](../README.md#using-aspire-dashboard-locally) for instructions.

### Debugging the Web App Locally

Follow the instructions in the [Web App documentation](../README.md#preparing-to-run-locally)
to prepare the system for debugging the Web App and running the Chat Service endpoint. Then follow the instructions
in the [Web App documentation](../README.md#debugging-the-web-app-locally) for starting the Web App and
getting the endpoint running in debug mode.

#### Using the VSCode "REST Client" Extension

Using the [instructions for the REST client](../README.md#using-the-vscode-rest-client-extension) the
[streaming test](../tests/integration/streaming.rest) file can be used to exercise the endpoint locally.

#### Using Chainlit

[Chainlit](https://docs.chainlit.io/get-started/overview) is an open source front-end application that you can
use for development purposes to test your chat api backend.  The files necessary to use chainlit as a development UI
have been added to this repository.

To run the chainlit UI:

- From a Terminal Window in VSCode, ensure that you are in the `src/web_api/chat_service` directory.
- Install the chainlit python package dependencies:

    ```bash
    pip install -r requirements-dev.txt
    ```

- Then run the following command  and it should open the chainlit UI local browser
  where you can start interacting with it.

    ```bash
    chainlit run chainlit_app.py
    ```

#### Using Aspire Dashboard Locally

In order to view the logs via the Aspire Dashboard follow the
[instructions in the Web App documentation](../README.md#using-aspire-dashboard-locally).
