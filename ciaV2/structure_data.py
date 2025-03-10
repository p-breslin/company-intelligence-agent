import json
import ollama
import logging
from utils.config import ConfigLoader
from arango_pipeline import GraphDBHandler


class StructureData:
    def __init__(self):
        cfg = ConfigLoader("llmConfig")
        self.model = cfg.get_section("models")["granite-instruct"]
        self.template = cfg.get_value("instruct_prompt")
        self.graph_handler = GraphDBHandler()

    def call_llm(self, company, context):
        prompt = self.template.format(company=company, context=context)
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
            options={"keep_alive": "1m"},
        )
        data = response["message"]["content"]

        # Parse JSON from the LLM response
        try:
            json.loads(data)
            self.graph_storage(data)
        except Exception as e:
            logging.warning(f"LLM returned invalid JSON. Error: {str(e)}")
            return

    def graph_storage(self, data):
        try:
            company = data.get("company", None)
            if not company:
                logging.error("Company name not extracted.")
                return
            company_key = self.graph_handler.insert_company(company)

            # Create edges for each competitor
            competitors = data.get("competitors", [])
            if not competitors:
                logging.error("competitors not extracted.")
                return
            for c in competitors:
                competitor_key = self.graph_handler.insert_company(c)

                # Create 'CompetesWith' edge
                self.graph_handler.create_relationship(
                    "CompetesWith",
                    f"Companies/{company_key}",
                    f"Companies/{competitor_key}",
                )

            logging.info(
                f"Stored {len(competitors)} competitor relationships for {company}."
            )

            # # Have yet to handle products
            # products = data.get("products", [])
            # for product_name in products:
            #     product_key = self.graph_handler.insert_product(product_name)
            #     # Create 'Produces' edge
            #     self.graph_handler.create_relationship(
            #         "Produces",
            #         f"Companies/{company_key}",
            #         f"Products/{product_key}"
            #     )
            # logging.info(f"Stored {len(products)} product relationships for {company}.")

        except Exception as e:
            logging.error(f"Error while inserting data into ArangoDB: {e}")
