# 001. Choose Azure AI Search as Search Technology

Date: 03-12-2025

## Status

Complete

## Context

For the first iteration of the AskLicensing solution, we must decide what search technology option should be used for
the project. The chosen option should support the following as a bare minimum:

- ability to store vector embeddings
- multiple indexes
- incremental reindexing
- availability in Gov Cloud

Some nice-to-haves for the chosen options are the following:

- Python SDK
- built-in support for hybrid search
- ease of integration with Azure AI Services

## Decision

We will use **Azure AI Search** because it meets the minimum requirements of support for vector embeddings, multiple
indexes, and incremental reindexing. It is also supported in Gov Cloud with the nice-to-have of IL4 and IL5 compliance.
Outside of the minimum requirements, it has a plethora of additional benefits like built-in hybrid search,
semantic reranker, ease of integration with other Azure AI Services, and customizable indexing using Skills (which can
be backed by Azure Functions for added customization).

Other options that were considered:

- Azure Cosmos DB
- Azure SQL Database
- Self-Hosted Chroma DB

### Consequences

- Good, because meets minimum requirements of vector embedding, multiple index, and incremental reindexing support
- Good, because has nice-to-haves like built-in hybrid search, semantic reranking, Azure AI Services integration, Python
  SDK that does not require knowledge of specific query language and further ingestion customization through Skills +
  Azure Functions
- Good, because reduced operational overhead due to it being a managed Azure service
- Bad, because can be pricier than options like Azure SQL or self-hosted options
