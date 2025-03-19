# LLM-based Activity recognition 

This code base uses a language model to infer human activities from raw location data. 
The LLM reasons based on the location, start and end time of the visit to the location, and surrounding POIs. 

Based on Overpass API (overpy package) and ChatGPT-o4.

#### Installation:

```
git clone https://github.com/mie-lab/llm_activity_labelling.git
cd llm_activity_labelling
pip install -e .
```

For using ChatGPT, you require an API key that must be exported to the environment variable `OPENAI_API_KEY`.

#### Test example: KML data

Download KML data from your Google timeline, and put it in a folder.
Adapt the test case [here](tests/run_test_kml.py):

```
python tests/run_test_kml.py
```