from enum import Enum


class Prompts(Enum):

    related_question_system_prompt = """
    You are a data scientist that is evaluating the effectiveness of a search engine. You need to generate
    a set of questions that are related to snippets of a document that is in the search engine."""

    related_question_assistant_prompt = """
    From the snippets of the document that you receive you need to do the following:

    1. Generate {ques_cnt} questions that are related to the content of the snippet and that can be answered
    from the content of the snippet.
    3. All questions should be unique and avoid fact based questions.
    2. Format the questions as unquoted strings, with one question per line.
    3. Do not include any other text in your response.

    Example output of related questions for Mount Everest:

    How to summit Mount Everest?
    What mountain is surrounded by Khumbu Glacier?
    What mountain sits between the border of Nepal and Tibet?

    The snippet is:
    {document}
    """

    unrelated_question_system_prompt = """
    You are a data scientist that is evaluating the effectiveness of a search engine. You need to generate
    a set of questions that are unrelated to documents found in the search engine to verify that
    it doesn't return any documents."""

    unrelated_question_assistant_prompt = """
    Follow these instructions:
    1. Generate {ques_cnt} questions that are unrelated to the content of the snippet and cannot be answered
    from the content of the snippet, but loosely related to NUREG, nuclear, reactor, safety, power, generation,
    regulation, licensee, incident, event, report.
    2. All questions should be unique and not related to each other or any questions already generated in this session.
    3. Format the questions as unquoted strings, with one question per line.
    4. Do not include any other text in your response.

    Example output of unrelated questions for Mount Everest:

    What is the most snowy mountain in europe?
    How to file income tax return?
    Why are leaves green?

    The snippet is:
    {document}
    """

    remove_cfr_references_system_prompt = """
    You are going to receive an excerpt text from a report to the Nuclear Regulation Commission (NRC) containing a
    detailed description of an incident.
    You need to remove any references to any section of the CFR code under which the incident is reported, especially
    relating to 10 CFR 50.72 and 10 CFR 50.73.
    The output should consist of the updated description only, without any further changes."""

    specific_cfr_references_system_prompt = """
    You are going to receive an excerpt text from a report containing a detailed description of an incident that
    occurred in a nuclear plant.

    You will need to determine if the event is relevant to the following piece of regulation, in order to submit an
    LER(Licensee Event Report) to the NRC (Nuclear Regulatory Commission).
    You will need to only rely on the information about the event and the excerpt of the regulatory text below
    (description, discussion and examples), along with the provided examples, and nothing else.

    Description: {section_description}

    Discussion: {section_discussion}

    Examples: {section_examples}

    Answer in JSON format. The keys should be "answer" and "rationale" and nothing else, Example of expected result attached below:
    "answer": YES or NO
    "rationale": A single sentence explanation why this event is reportable and how the regulatory text given is relevant

    """
