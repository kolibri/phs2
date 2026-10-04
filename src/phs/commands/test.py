from pprint import pprint
from typing import Annotated

from cyclopts import Parameter

from phs.context import AppContext
from phs.inventory.config import load_host
from phs.inventory.facts import Facts, OsFacts
from phs.inventory.recipe import RecipeCollection, load_recipes
from phs.inventory.templating import TemplateRenderer, render_recipe


def test(
    *,
    context: Annotated[AppContext, Parameter(parse=False)],
):
    print("Hello world")

    host_file = load_host("tests/hostconfig/hosts/hojo.ko.yaml")

    recipes = load_recipes(
        [
            "tests/hostconfig/recipes/base.yaml",
        ]
    )

    facts = Facts(os=OsFacts(id="arch", version="rolling"))

    renderer = TemplateRenderer()

    recipes = recipes.merge(RecipeCollection(recipes=host_file.recipes))

    rendered_host = renderer.render(
        host_file.host,
        host=host_file.host,
        facts=facts,
    )

    print(rendered_host.model_dump_json(indent=2))
    print(host_file.model_dump_json(indent=2))
    print(recipes.model_dump_json(indent=2))

    for invocation in host_file.host.recipes:
        recipe = recipes.recipes[invocation.name]

        rendered_recipe = render_recipe(
            recipe,
            invocation,
            renderer,
            host=host_file.host,
            facts=facts,
        )

        print(rendered_recipe.model_dump_json(indent=2))
