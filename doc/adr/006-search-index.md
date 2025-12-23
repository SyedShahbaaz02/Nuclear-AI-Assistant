# 006. AI Search Index Design

Date: 06-12-2025

## Status

Complete

## Context

Per the [search ADR](./001-choose-azure-ai-search.md) Azure AI Search is being used for document retrieval. The
documents that are anticpated to be stored in AI Search indexes include but are not limited to:

1. [NUREG 1022, Rev. 3](https://www.nrc.gov/docs/ML1303/ML13032A220.pdf) and it's supplements.
1. Portions of the internal Reportability Manual. Including, but not limited to:
    1. LS-AA-1110 - Safety Reportability (SAF)
    1. LS-AA-1120 - Radiation Reportability (RAD)
    1. LS-AA-1130 - Security Reportability (SEC)
1. Plant Technical Specifications (TS)
1. Plant Updated Final Safety Analysis Report (UFSAR)

There is a small possibility that other documents such as Licensee Event Reports (LER) and/or Event Notification System
reports (ENS) might be ingested in the future as well.

### NUREG-1022

We have decided to start our design with ingesting the NUREG 1022, Rev. 3. Initially the supplements will not be
included in the ingestion process. They present a level of complexity that would cause a delay in getting a baseline
system functioning. These supplements will be ingested in the future.

The ingestion of NUREG was a two phase process. The first phase was a naive chunking of the document using a 2,000
character chunk with a 200 character overlap. We consider this "naive" because at the time that it was implemented an
EDA of the document had not been conducted, so there was no influence on the design by the document itself. The naive
index was implemented to at least provide a searchable index that can be used on the first iteration of the end to end
system. This was considered to be a throwaway index.

The second phase was done after the EDA. A decision was made that for the purpose of recommending whether an incident
is reportable under 10 CFR 50.72 or 10 CFR 50.73 the most relevant part of the NUREG 1022 was section 3.2 and it's
subsections. Each of the 14 subsections of 3.2 addresses the reasons why an incident would be reportable under the CFRs.
The structure of each section is consistent with the following elements:

* Title - This includes the subsection heading level (e.g., 3.2.1, 3.2.2) and a short title for the section (e.g.,
Plant Shutdown Required by Technical Specifications).
* 50.72 and 50.73 reporting requirements - This is a table with the left column listing the subsections of the 10 CFR
50.72 and the right column listing the subsections of 50.73.
* Description - This is the first paragraph after the 50.72/50.73 table that precedes the discussion. Not all
subsections have a Description.
* Discussion - This is the bulk of the content for each subsection and goes into a detailed analysis of the CFR
subsections that an incident would be reportable under, as described by the table preceding the dicussion.
* Examples - The part of the subsection give examples of incidents that would be reportable under the CFRs identified in
the preceding table. Not all subsections have examples.

The elements of the configuration for Azure AI Search include:

* Index with the following fields (related to the above)
  * section - The title of the subsection.
  * lxxii - A `Collection` of relevant 10 CFR 50.72 references.
  * lxxiii - A `Collection` of relevant 10 CFR 50.73 references.
  * description - The Description paragraph.
  * descriptionVector - The embeddings for description.
  * discussion - The Discussion section in it's entirety.
  * discussionVector - The embeddings for discussion.
  * examples - A `Collection` of `ComplexType` objects (title and description fields) from Examples.
  * pageNo - The page that the section starts on.
* DataSource - points to the folder that the NUREG document is in in the `non-eci` container in the Storage Account.
* Custom Web API Skill - Accepts the path to the NUREG document and returns the JSON representation of the data going
  into the index.
* Embedding Skill - Built-in embedding skill that generates the vectors. This is currently using
  `text-embedding-3-large` due to the size of the `discussion` field exceeding, in most cases, the context window of
  `text-embedding-ada-002`.
* Skillset - Combines the two skills to get the final results for the index.
* Indexer - Combines the DataSource, Skillset, and Index to execute the ingestion process.

The NUREG 1022 section 3.2 is extracted via a Azure Function App. Each subsection of 3.2 (e.g., 3.2.1, 3.2.2, etc.) is
extracted as a document in the Azure AI Search index. This is done to keep all context of a subsection in a single
record in the index so that when the document is retrieved all of the relevant data pertaining to that subsection is
available as query results.

### LS-AA-1110, LS-AA-1120, LS-AA-1130

Each of these documents is a part of the Constellation Reportability Manual. The LS-AA-1110 is the Safety Reportability
manual, also called the "SAF" because each section of the document is titled with an SAF number (e.g., SAF 1.1), and
referenced by the SAF number. Similarly, LS-AA-1120 is the Radiation Reportability manual, or RAD. And the LS-AA-1120 is
the Security Reportability manual or SEC. Each of these documents has the same format.

The order that they will be ingested in to Azure AI Search is the order listed, with the SAF first (identified as the
most relevant), RAD second, and SEC last. That is true unless it is easier to group the latter two after the first one
establishes the pattern. In which case we would start with the SAF, and then in a second pass add the RAD and SEC at the
same time.

The documents have a wide range of reportability requirements, many are outside the purview of 10 CFR 50.72 and 10 CFR
50.73. The only sections that will be extracted for the index are those that have references to the 10 CFR 50.72 or the
10 CFR 50.73.

The metadata that are available in these documents include:

* Title - This is the SAF, RAD, or SEC number (e.g., SAF 1.1, RAD 1.5, etc.)
* 50.72 and 50.73 reporting requirements - There is a single list with all related regulations including, but not
  limited to 10 CFR 50.72 and 10 CFR 50.73.
* Required Notifications - This is a table of the required notifications and the timeline that they are required by
  for incidents that are covered under the section.
* Required Reports - This is a table of the required physical reports and the timeline that they are required by for
  incidents that are covered under the section.
* Discussion - This is the bulk of the content for each seciont and goes into a detailed analysis of the reportability
  requirement that an incident would be reportable under.

The elements of the configuration for Azure AI Search include:

* Index with the following fields (related to the above)
  * saf - The title of the SAF.
  * lxxii - A `Collection` of relevant 10 CFR 50.72 references.
  * lxxiii - A `Collection` of relevant 10 CFR 50.73 references.
  * discussion - The Discussion section in it's entirety.
  * discussionVector - The embeddings for discussion.
  * requiredNotifications - A `Collection` of `ComplexType` objects (time limit and required notification fields) from
    the Required Notifications.
  * requiredReports - A `Collection` of `ComplexType` objects (time limit and required report fields) from
    the Required Reports.
  * pageNo - The page that the section starts on.
* DataSource - points to the folder that the reportability manual documents are in in the `non-eci` container in the
  Storage Account.
* Custom Web API Skill - Accepts the path to the reportability manual document and returns the JSON representation of
  the data going into the index.
* Embedding Skill - Built-in embedding skill that generates the vectors. This is currently using
  `text-embedding-3-large` due to the size of the `discussion` field exceeding, in most cases, the context window of
  `text-embedding-ada-002`.
* Skillset - Combines the two skills to get the final results for the index.
* Indexer - Combines the DataSource, Skillset, and Index to execute the ingestion process.

## Decision

Given the disparity in metadata and the purpose for each of these document types, separate indexes will be created for
each document type. The trade offs include:

* Positive Tradeoffs for Multiple Indexes
  * Single Responsibility Principal is maintained - Each index will have a singular purpose; i.e., one index for NUREG
    and one index for Reportability manuals.
  * Simpler Code implementation - Since each index is singular in purpose and design, the code written to retrieve
    documents can be isolated without the need to consider irrelevant fields or provide a filter to restrict the domain
    of the documents retrieved.
  * Simpler index definitions - To flatten the index to accomodate multiple document types would require increasing the
    number of fields in the index for each document type added that doesn't match existing fields. This would increase
    the cognitive load in understanding the index and the purpose of the fields.
  * Smaller footprint - Indexes tailored to the data would not have sparse fields that would take up disk space and
    potentially increase the size of transferred documents regardless of the empty value of the field.
  * Reduces vector search time - The number of documents that we will have in the indexes is small, so this is just
    brought into the discussion as an academic topic more than anything else. HNSW has logarithmic time complexity. This
    essentially means that for extremely large datasets it approaches an asymptote in time to search. However, for
    smaller datasets, before the asymptote is approached, the search time increases at a more significant rate, closer
    to linear at the extreme.
* Negative Tradeoffs for Multiple Idexes
  * Complexity in maintenance - Having multiple indexes potentially requires additional maintenance effort versus a
    single index.
  * Query complexity - Having multiple indexes requires multiple queries. A single index could retrieve many different
    types of documents with a single query. The concern, however, is that AI Search would not be able to guarantee that
    sufficient documents are returned for each document type required by the system in the top `n` documents returned
    from a single index. Or in order to ensure that the system can guarantee it, it would need to retrieve more
    documents than might otherwise be necessary, increasing data transfer sizes and costs. The last option is to conduct
    mulitple queries regardless of it being a single index, with each query filtering the domain of documents returned.
    But this would mean that there is no negative tradeoff because in both cases there would be multiple queries. If we
    could guarantee in a response that we retrieved `n` records in each facet for each query, this point is moot. But
    current research indicates that this isn't possible with AI Search.

## Consequences

Potential consequences are an increase in maintenance effort for the indexes in the future compared to a single index.
This, in and of itself, does not outweigh the benefits of using multiple indexes.
