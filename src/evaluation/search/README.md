# Search Evaluation

## Executing the Notebooks

In order to execute the notebooks the `.dev.env` file must be copied and saved as a `.env` file (this file has been
added to `.gitignore`). The enviroment variables in the new file must then be filled out.

### Generate Synthetic Data

The first notebook to execute is the [generate synthetic data notebook](./nureg-generate-synth-data.ipynb). This
notebook uses an LLM to generate three questions for each entry that it retrieves from AI Search. The document that
generated the question is assumed to be the document that is expected to be returned when the question is submitted to
AI Search. Additionally, 100 questions unrelated to nuclear power generation or licensing are generated as expected
negative results. These questions are then saved to the `./output/` folder.

### Updated Search Index Evaluation Notebooks

New search evaluation notebooks have been created. One for Nureg Index that holds 14 subsection from the NUREG Manual
and another one for the Reportability Manual that contains RAD, SAF, SEC docs. Each notebook tests the retrieval of the
documents and contains code to assist with determing threshold and optimal K. As the project progresses, ensure to
either update the current index configuration such as the doc number or add new notebooks to evaluate the search index.

### Evaluate Search

The next notebook to execute is the [evaluation notebook](./search_eval.ipynb). This notebook uses the generated
synthetic questions to query AI Search. The document with the highest search score is then evaluated to determine if it
was the expected document. Note that for negative results a threshold is used such that any results with a search score
below the threshold are ignored. All three methods of querying AI Search are evaluated: text, vector, and hybrid. The
results are saved to the `./output/` folder.

## Logging the Results

The results of any experiments conducted should be added to the [experimentation log](./experimentation_log.md). Record
in that log the date of the experiment, the index that was evaluated, the context of the experiment, the source of the
ground truth data, the metrics that were captured, and a narrative that interprets the results of the experiment.
