import json
import os
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o")

prompt_dir = "1les_temps_article/prompts"

base_prompt = "You are a system to find out what places a person visited. We only have the raw location data from this person,\
 meaning longitude, latitude and start and end time. We want to know what exactly the person did. To find out, we have\
 list of the ten closest Points of Interest (POIs) from OSM, with their name, category and distance. When classifying,\
 please consider the following considerations: 1. If there is no POI nearby, the label is probably visiting a friend or something similar.\
 2. If there are many shopping-POIs nearby, it might be a shopping mall\
 3. At typical lunch and dinner times  (lunch: 12pm - 2pm, dinner: 6pm - 9pm), a visit to a restaurant or cafe is more likely.\
 4. The person lives in Geneva. All activities in France are thus more likely to be touristy stuff.\
 5. Activities during night hours are most likely to be hotels.\
 Here is the data for the stay point of the person: "

results = {}
for i in range(33):

    with open(os.path.join(prompt_dir, f"prompt_{i}.txt"), "r") as infile:
        prompt = infile.read()

    full_prompt = (
        base_prompt
        + prompt[:-1]
        + '.\nWhat place did the person visit or what activity did they do? Please answer with "Place: <output> Type: <output> Reasoning: <reasoning>" '
    )

    response = llm.invoke(full_prompt)

    print(response)

    full_res = response.content
    try:
        place_res = full_res.split("Place:")[1].split("Type:")[0].replace("\n", "")
    except:
        place_res = "None"
    try:
        type_res = full_res.split("Type:")[1].split("Reasoning:")[0].replace("\n", "")
    except:
        type_res = "None"
    results[i] = {"place_llm": place_res, "label_llm": type_res, "response_llm": full_res, "prompt_llm": full_prompt}

    with open("1les_temps_article/results_llm.json", "w") as outfile:
        json.dump(results, outfile)
        # print(response)
