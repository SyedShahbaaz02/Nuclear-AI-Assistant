# Search Evaluation

## Executing the Notebooks

In order to execute the notebooks the `.dev.env` file must be copied and saved as a `.env` file (this file has been
added to `.gitignore`). The enviroment variables in the new file must then be filled out. Note that the
ASK_LICENSING_ENDPOINT is the API using streaming.rest but instead of local host use the web_app domain so it
should be <https://web-app-domain/chat/stream>. Run the entire notebook and user should see the output json file.
To get insight into the logging, go into Application Insights in the Azure portal and under Monitoring locate Logs with
the resource filtered to our web app.

### Generate Ground Truth

The first notebook is the [data generation notebook](./main.ipynb). Only run this if the ground truth must be
regenerated. This notebook will download LERs from the NRC's website and store them in blob storage. After the LERs are
retrieved, a custom Document Intelligence resource is used to extract the narrative of the LER, the subsections of the
10 CFR 50.73 that the LER was submitted under, and other metadata that is relevant to the LER. The results are our
labeled ground truth with the subsections of 10 CFR 50.73 being the labels for the narrative.

The results are stored in the [output](./output/) folder. The output folder is persisted to ensure that the LER
retrieval process is done rarely (we don't want to make enemies of the NRC). The evaluation notebook can be executed
from the data persisted in the [output](./output/) folder without regenerating the ground truth.

### Updated System Evaluation Notebook

New updated notebook has been created named as system_evaluation. This notebook allows the evaluation of the entire
system. To test the system against different search configurations, make sure to update the search_configuration.json
file and retrieve the configuration numbers from the search index evaluation. To test different orchestration patterns,
modify the endpoint accordingly in your .env file.

### Evaluate Search

To evaluate the system execute the [evaluation notebook](./recommendation-eval.ipynb). This notebook uses the narrative
from the ground truth as input to the API to get a recommendation from the system. A multiclass evaluation is done, such
that the expected labels (10 CFR 50.73 subsections) are verified against the results from the system. Various metrics
are calulated from the results and then output in the notebook.

## Logging the Results

The results of any experiments conducted should be added to the [experimentation log](./experimentation_log.md). Record
in that log the date of the experiment, the endpoint that was evaluated, the context of the experiment, the source of
the ground truth data, the metrics that were captured, and a narrative that interprets the results of the experiment.
