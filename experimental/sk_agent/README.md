# Agent Exploration

This folder contains an exploration of using a Semantic Kernel based agent approach for acting as a reportability
copilot.

The packages used are outlined in the `pyproject.toml` file within this folder.

To get started, the easiest path is to add `uv` to your development environment. As of writing, you can do this via:

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Once that is installed, navigate to the `experimental/sk_agent` folder, and run `uv sync`. This will install the
appropriate packages in a virtual environment.

## Creating the Search Index

To create the search index, create a `.env` file, based on the `.env.example`, and populate the placeholder values.
Then, run: `uv run create_index.py`. This will define and create an empty search index, with vector search and
semantic search configured.

Once that is complete, run `uv run process_documents.py`, which will connect to the blob store, parse the LER documents,
embed the content, and upload the processed data into the search index.

## Testing the agent

The agent uses Semantic Kernel's agent framework, and the Azure AI Search collection plugin to query the index to help
answer questions about the LER documents.

You ran run the script `uv run run_sk_agent.py` to have a chat conversation with the agent. Currently, it is configured
to use the `LER` dataset and the `NUREG` dataset that has been indexed. You can use one or both to answer your
questions.

Every so often, the program seems to slow to a halt - in these cases, restarting the VDI has seemed to resolve the
performance issues.

## Notebooks

The notebooks found in the `testing_notebooks` folder are the raw experiment notebooks I used while going through
creating the scripts. The notebooks are only there for record keeping, but they are not recommended for use, as
some of the code in there was only partially functional, and then revised during the migration to the python scripts.
