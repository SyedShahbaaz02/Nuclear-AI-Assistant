# 005. Search Evaluation

Date: 06-19-2025

## Status

Complete

## Context

End to end evaluation of the system is intended to replicate user behavior and predict the outcome of that interaction.
To such end, the ideal end state will use labeled queries that were captured by the system from actual user
interactions. The labels to the queries will be the expected subsections of the 10 CFR 50.72 and the 10 CFR 50.73 that
the query would be reportable under.

However, that end state is not possible early in the development cycle, before users can actually use the system for
reportability recommendations. To get to that end state, an approach will need to be developed that can evaluate the
system, not only when it is in use by the end user in production, but while it is in development before that point.

The ground truth that is available for evaluation will be different early in development compared to later in
development. The data that is available early in development includes ENS, LER (Form 366), and IR (AS9 DB) data. ENS and
LER data also includes under which subsections of the 10 CFR 50.72 (ENS) or 10 CFR 50.73 (LER) the incident was
reportable.

The metrics that are captured must also be evolutionary in practice. The early metrics should be the low hanging fruit
that can result in a measurable system, but also has some meaning for the purposes of feedback as the system grows.
Ideally, the metrics used will result in feedback that can provide insights into whether features, updates, or changes
to the system are improving the final results of the system.

## Decision

### Ground Truth

The ground truth for an evaluation of the end to end system will consist of, at a minimum, three phases.

The first phase will use the raw narrative from ENS and LER documents. It has been determined that there is no missing
information from Form 366 documents that are provided to the NRC that would preclude the system from making a positive
determination. The same can be said for the ENS notifications. In the case of an LER, the Form 366 has check boxes that
determine under which subsection of the 10 CFR 50.73 the incident is reportable. For ENS reports, the text of the report
contains the references to the subsections that the incident is reported under. A cleansing step in both cases will need
to be done to remove references in the narrative that is provided to the system so that the answer isn't in the
question.

The second phase will attempt to use AS9 data that can be connected to ENS reports or LERs. There is no direct mapping
of keys between the systems, so a heuristic approach will need to be taken to identify the relationships. Once that is
done and the IRs in AS9 are found and linked to the ENS report or LER, the first narrative, before any assignments, is
potentially the closest verbiage that we can get out of the system that would mirror what a user would query the system
for. The mapping back to the ENS report and LER is necessary to determine the reportable subparagraphs.

The final phase of the ground truth will use actual user queries, once the system is deployed. Both positive and
negative ground truth can be extracted this way. In order to get the relevant subections for reporting, initially, a
manual process could be done by Operators to identify the correct labels. In the longer term, any ENS reports or LERs
submitted based on the incident being queried by the system could provide a path to a more automated labelling system.
In the case of LERs, this mapping couldn't happen until 60 days after the incident (the timeframe that an LER must be
submitted).

### Metrics

A true positive for the class being analyzed would be a result from the system indicating the label that the incident
is a member of. For example, if an incident is reportable under 10 CFR 50.72(a)(b)(c)(d), the system recommends
reportability under 10 CFR 50.72(a)(b)(c)(d).

A false positive for the class being analyzed would be a result from the system indicating a label that the incident is
not a member of. For example, if an incident is not reportable under 10 CFR 50.72(a)(b)(c)(d), but the system recommends
reportability under 10 CFR 50.72(a)(b)(c)(d).

A true negative for the class being analyzed would be a result from the system that does not indicate the label that the
incident was not a member of. For example, the incident is not reportable under 10 CFR 50.72(a)(b)(c)(d) and the system
does not recommend reportability under 10 CFR 50.72(a)(b)(c)(d).

A false negative for the class being analyzed woulld be a result from the system that does not indicate the label that
the incident is a member of. For example, the incident is reportable under 10 CFR 50.72(a)(b)(c)(d) and the system
does not recommend reportability under 10 CFR 50.72(a)(b)(c)(d).

Every possible subsection that any given incident could be reportable under is a class and is evaluated independently.
Any incident is a member of one or more classes, as more than one subsection can apply to an incident.

The initial metrics will consist of multiclass measurements. The first metrics put in place will include, at a minimum,
accuracy, micro averaged precision, micro averaged recall, and micro averaged F1 score. The latter three are all
multiclass metrics.

Unlike ground truth, there's no phases to the metrics. This is a constantly evolving space that does not limit the
possibilities. Any relevant metric should be considered and added to the evaluation.

### Consequences

Positive consequences of this approach are that an evaluation system is put in place early in development so that the
system can be measured as changes are made.

Negative consequences are that the early metrics are less meaningful, both from the perspective of which metrics, but
also in the context of the ground truth. Both will become more meaningful, relevant, and actionable over time.
