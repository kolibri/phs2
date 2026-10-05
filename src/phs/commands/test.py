from typing import Annotated

from cyclopts import Parameter
from fabric import Connection

from phs.context import AppContext
from phs.inventory.config import load_host
from phs.inventory.config_renderer import TemplateRenderer
from phs.inventory.facts import Facts, OsFacts
from phs.inventory.recipe import RecipeCollection, load_recipes


def test(
    hostname: str,
    *,
    context: Annotated[AppContext, Parameter(parse=False)],
):
    print("Hello world")

    inventory = context.inventory_loader.load(hostname)
    # print(inventory)

    """
    host_file = load_host("tests/hostconfig/hosts/hojo.ko.yaml")

    recipes = load_recipes(
        [
            "tests/hostconfig/recipes/base.yaml",
        ]
    )

    facts = Facts(os=OsFacts(id="arch", version="rolling"))

    renderer = TemplateRenderer()

    recipes = recipes.merge(RecipeCollection(recipes=host_file.recipes))

    rendered_host = renderer.render_host(
        host_file.host,
        host=host_file.host,
        facts=facts,
    )

    renderer._render(
        host_file,
        host=host_file.host,
        facts=facts,
    )

    # print(rendered_host.model_dump_json(indent=2))
    # print(host_file.model_dump_json(indent=2))
    # print(recipes.model_dump_json(indent=2))

    for invocation in host_file.host.recipes:
        recipe = recipes.recipes[invocation.name]

        rendered_recipe = renderer.render_recipe(
            recipe,
            invocation,
            host=host_file.host,
            facts=facts,
        )

        # print(rendered_recipe.model_dump_json(indent=2))
        # print(rendered_recipe)
    c = Connection(
        host=rendered_host.connection.host,
        port=rendered_host.connection.port,
        user="root",
        connect_kwargs={
            "key_filename": "tests/vm/helper/files/id_ed25519",
        },
    )
    result = c.run("uname -s")
    print(result.stdout)
    """
