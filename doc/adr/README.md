# Architecture Decision Record (ADR)

## Discussion

An ADR is designed to capture decisions that have been made with respect to the system that affect the architecture,
design, or implementation. A discussion on ADRs can be found
[here](https://github.com/joelparkerhenderson/architecture-decision-record?tab=readme-ov-file#adr-example-templates).

## Files

### ADR History

The ADR decision log is a running history of the ADRs that have been recorded. This history includes the decision that
was made, the date it was made, alternatives that were considered, the reasoning for the decision given the
alternatives, a link to the markdown file for the full discussion, who made the decision, and a link to the work to be
done in Azure DevOps.

### ADR

For every architectural decision made an ADR must be generated to capture the decision making process.

Each ADR must be prefaced with a three digit "0" left-padded sequence number (e.g., 001-infra.md, 002-database.md). This
makes it easier to reflect on the order of decisions that were made and also keeps the sequence in line with the ADR
History.

The simplified ADR template includes three sections:

* Header information - information in the header will include the title of the ADR, the date, and the author.
* Status - statuses can include, but are not limited to: In Progress, Decision Made, Complete, and Superceded (to
include by what is superceding). This is not a strict enum, but the status should reflect the current state of the ADR.
* Context - any important context that drives the reason for making the decision. This is a narrative that should
include the historical necessity for creating the ADR.
* Decision - this section is the discussion on the decision that was made to include alternatives and why they were
rejected.
* Consequences - there is always a tradeoff when architectural decisions are made. Those tradeoffs are to be described
here. This is not for only negative consequences, but also for positive consequences.
