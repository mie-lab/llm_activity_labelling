import json
import os
from langchain_openai import ChatOpenAI

from llm_privacy.surrounding_poi import SurroundingPOI
from llm_privacy.prompt_design import (
    BASE_PROMPT,
    PROMPT_FORMAT,
    prompt_pois,
    prompt_for_activity,
)


class QueryLLM:
    def __init__(self, poi_finder: SurroundingPOI, model="gpt-4o"):
        self.llm = ChatOpenAI(model=model)
        self.poi_finder = poi_finder
        self.base_prompt = BASE_PROMPT

    def __call__(self, locations):
        results = {}
        for row in locations.iterrows():
            lon = row.geometry.x
            lat = row.geometry.y

            # Find the closest POIs
            closest_pois = self.poi_finder(lon, lat)
            # Prompt defining the surrounding POIs
            pois_prompt = prompt_pois(closest_pois)

            # Basic prompt where and when the activity took place
            time_start = row.time_start
            person_prompt = prompt_for_activity(lon, lat, time_start)

            full_prompt = self.base_prompt + person_prompt + pois_prompt + PROMPT_FORMAT

            response = self.llm.invoke(full_prompt)

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
            results.append(
                {
                    "place_llm": place_res,
                    "label_llm": type_res,
                    "response_llm": full_res,
                    "prompt_llm": full_prompt,
                }
            )

            with open("1les_temps_article/results_llm.json", "w") as outfile:
                json.dump(results, outfile)
                # print(response)
