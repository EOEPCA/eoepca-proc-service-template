import os
import unittest

import requests
import pystac
from cookiecutter.main import cookiecutter
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


class TestExecutionHandler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # UMA
        # Client (e.g. Portal) authenticates user and calls the ADES
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")

        # Get Token Endpoint from OIDC Configuration
        # Get OIDC Configuration
        oidc_config_endpoint = os.getenv("OIDC_ENDPOINT")

        headers = {"accept": "application/json"}
        oidc_config = requests.get(oidc_config_endpoint, headers=headers).json()

        # Extract the token endpoint
        token_endpoint = oidc_config["token_endpoint"]
        username = os.getenv("USER_NAME")
        password = os.getenv("PASSWORD")

        headers = {"cache-control": "no-cache"}
        data = {
            "scope": "openid user_name is_operator",
            "grant_type": "password",
            "username": username,
            "password": password,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        token_response = requests.post(
            token_endpoint, headers=headers, data=data
        ).json()

        id_token = token_response["id_token"]
        token_response["access_token"]
        token_response["refresh_token"]

        cls.conf = {}
        cls.conf["auth_env"] = {"jwt": id_token}
        cls.conf["lenv"] = {"message": ""}
        cls.conf["lenv"] = {
            "Identifier": "water-bodies",
            "usid": "cool-collection-2",
        }
        cls.conf["tmpPath"] = "/tmp"
        cls.conf["main"] = {
            "tmpPath": "/tmp",
            "tmpUrl": "http://localhost:8080",
        }

        cls.conf["additional_parameters"] = {}
        cls.service_name = "water_bodies"
        cls.workflow_id = "water-bodies"

        cls.base_domain = "demo.eoepca.org"
        cls.workspace_prefix = "demo-user-eric"

        cookiecutter_values = {
            "service_name": cls.service_name,
            "workflow_id": cls.workflow_id,
        }

        os.environ[
            "WRAPPER_STAGE_IN"
        ] = f"{os.path.dirname(__file__)}/assets/stagein.yaml"
        os.environ[
            "WRAPPER_STAGE_OUT"
        ] = f"{os.path.dirname(__file__)}/assets/stageout.yaml"
        os.environ["WRAPPER_MAIN"] = f"{os.path.dirname(__file__)}/assets/main.yaml"
        os.environ["WRAPPER_RULES"] = f"{os.path.dirname(__file__)}/assets/rules.yaml"

        os.environ["DEFAULT_VOLUME_SIZE"] = "10000"
        os.environ["STORAGE_CLASS"] = "standard"

        template_folder = f"{os.path.dirname(__file__)}/.."

        service_tmp_folder = "tests/"

        cookiecutter(
            template_folder,
            extra_context=cookiecutter_values,
            output_dir=service_tmp_folder,
            no_input=True,
            overwrite_if_exists=True,
        )

        cls.inputs = {
            "aoi": {"value": "-121.399,39.834,-120.74,40.472"},
            "bands": {"value": ["green", "nir"]},
            "epsg": {"value": "EPSG:4326"},
            "stac_items": {
                "value": [
                    "https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/S2A_10TFK_20210708_0_L2A",  # noqa
                ]
            },
        }

        cls.outputs = {}
        cls.outputs["stac"] = {"value": ""}

    def test_runner(self):
        from tests.water_bodies.service import water_bodies

        water_bodies(self.conf, self.inputs, self.outputs)

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.conf['auth_env']['jwt']}",
        }

        workspace_endpoint = f'https://resource-catalogue.{self.workspace_prefix}.{self.base_domain}/collections/{self.conf["lenv"]["usid"]}/items'

        r = requests.get(workspace_endpoint, headers=headers)

        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["numberMatched"], 1)
        self.assertIsInstance(pystac.read_dict(r.json()["features"][0]), pystac.Item)

        logger.info("Test passed")
