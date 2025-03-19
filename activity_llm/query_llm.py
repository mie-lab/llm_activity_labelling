import json
import os
import pandas as pd
from langchain_openai import ChatOpenAI

from activity_llm.surrounding_poi import SurroundingPOI
from activity_llm.prompt_design import (
    BASE_PROMPT,
    PROMPT_FORMAT,
    prompt_pois,
    prompt_for_activity,
)


class QueryLLM:
    def __init__(self, poi_finder: SurroundingPOI, model="gpt-4o", max_pois=15):
        self.llm = ChatOpenAI(model=model)
        self.poi_finder = poi_finder
        self.base_prompt = BASE_PROMPT

        self.max_pois = max_pois

    def __call__(self, locations, output_dir: str = None):
        llm_results = []
        for sp_id, row in locations.iterrows():
            lon = row.geometry.x
            lat = row.geometry.y

            # Find the closest POIs
            closest_pois = self.poi_finder(lon, lat).sort_values("distance").head(self.max_pois)
            # Prompt defining the surrounding POIs
            pois_prompt = prompt_pois(closest_pois)

            # Basic prompt where and when the activity took place
            person_prompt = prompt_for_activity(lon, lat, row["started_at"], row["finished_at"])

            full_prompt = self.base_prompt + person_prompt + pois_prompt + PROMPT_FORMAT

            # Query the LLM
            response = self.llm.invoke(full_prompt)

            # handle the response
            full_res = response.content
            try:
                place_res = full_res.split("Place:")[1].split("Type:")[0].replace("\n", "").strip()
            except:
                place_res = "None"
            try:
                type_res = full_res.split("Type:")[1].split("Reasoning:")[0].replace("\n", "").strip()
            except:
                type_res = "None"

            # add to dictionary
            llm_results.append(
                {
                    "sp_id": sp_id,
                    "place_llm": place_res,
                    "label_llm": type_res,
                    "response_llm": full_res,
                    "prompt_llm": full_prompt,
                }
            )
            print(f"RESULT FOR SP {sp_id}:", llm_results[-1])
            print()

            if output_dir is not None:
                with open(os.path.join(output_dir, "results_llm.json"), "w") as outfile:
                    json.dump(llm_results, outfile)
        return pd.DataFrame(llm_results)
