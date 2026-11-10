"""Square Peg Labs — the builders behind /play/*-lab/.

The Pizza Lab came first and was a page of its own with its own fields baked
into the template. Three more were asked for — sandwiches, salads and the bar
— so the shape is now data: every lab is a list of groups, every group is a
set of chips the visitor picks from, and one template and one event handler
serve all four. Adding a fifth is a dict, not a page.

A group is:
    key       the form field name, and the key in the submitted JSON
    legend    what the visitor sees above the chips
    pick      "one" (radio) or "many" (checkbox)
    max       for "many": how many they may take
    options   a flat list of chips
    sections  instead of options: [(sub-heading, [chips])] for a list too long
              to read flat. The bar's base spirits are sixty-odd bottles, which
              is unreadable as one run of chips.
    default   which chip is pre-checked. Leave it out and nothing is, except
              for "one" groups where the first is checked.
    silent    a chip whose value should not appear in the written-out preview
              ("Nothing — leave it alone" reads badly in a sentence).
    optional  "many" groups only: zero picks is a valid build.

EVERY LIST HERE IS A KITCHEN LIST, NOT A WISH LIST. The point of the whole
thing is that what someone sends us is something the line can actually make.
The pizza lists come off the 10.12.26 menu and are maintained in play.py with
the reasoning attached; the sandwich, salad and bar lists came from Brian on
10.11.26 and are reproduced here as given.

SUBMISSIONS. The lab-submit edge function validates every value against its
own copy of these lists and rejects anything it does not recognise, so a lab
cannot accept entries until that function knows about it. Each lab therefore
carries its own `live` flag and `endpoint`; a lab with no endpoint says so
rather than failing, which is the behaviour the Pizza Lab already had before
its backend existed.
"""
# build.py puts data/ on sys.path and imports these as top-level
# modules, so this is absolute, the same way build.py imports play.
from play import LAB as _PIZZA

HUB = {
    "slug": "labs",
    "eyebrow": "Square Peg Labs",
    "h1": "You build it. We put it on the menu.",
    "lede": "Five benches, five things you can design out of what is actually "
            "in our kitchens and behind our bar. We read every entry, and the "
            "ones we pick go on the menu with your name beside them.",
    "intro_h2": "No vote.",
    "intro": [
        "Nothing here is a contest. Nothing you build gets posted for other "
        "people to pick over or vote on.",
        "Everything on every list is something we already stock. That is the "
        "whole constraint — build the best thing you can out of it.",
    ],
}

# --------------------------------------------------------------- shared lists
# Sandwiches and salads draw on the same kitchen. Where the two lists Brian
# sent differ, they differ here too rather than being quietly merged: the
# sandwich list has fried eggplant and the hot sauces, the salad list does not.
_VEG = ["Red onions", "Cucumbers", "Braised fennel", "Roasted tomatoes",
        "Roasted beets", "Caramelized onions", "Roasted red peppers", "Olives",
        "Candied walnuts", "Croutons"]

_GREENS = ["Romaine lettuce", "Mesclun greens", "Arugula"]

_CHEESE = ["Ricotta", "Shredded mozzarella", "Fresh mozzarella", "Goat cheese",
           "Parmesan"]

_SALAD_PROTEIN = ["Roasted chicken", "Breaded chicken", "Salmon", "Prosciutto",
                  "Meatball", "Fried mozzarella"]

# The sandwich list adds fried eggplant; the salad list does not have it.
_SUB_PROTEIN = _SALAD_PROTEIN + ["Fried eggplant"]

_DRESSINGS = ["Red wine vinaigrette", "Roasted tomato vinaigrette",
              "Honey lemon vinaigrette", "Ranch", "Bleu cheese", "Caesar"]

# Sandwiches get the hot sauces and marinara on top of the dressings.
_SUB_SAUCES = _DRESSINGS + ["BBQ", "Buffalo", "Carolina Gold", "Hot honey",
                            "Marinara sauce"]

NONE_CHEESE = "No cheese"
NONE_PROTEIN = "No protein — keep it vegetarian"
NONE_GREENS = "No greens"


def _lab(slug, name, short, unit, h1, lede, groups, how, rules, nxt,
         placeholder, live=False, endpoint=None, note=None,
         art="margherita-board",
         alt="A wood-fired pizza on the board at Square Peg"):
    return {"slug": slug, "name": name, "short": short, "unit": unit,
            "eyebrow": name, "h1": h1, "lede": lede, "groups": groups,
            "how": how, "rules": rules, "next": nxt, "live": live,
            "endpoint": endpoint, "note": note, "art": art, "alt": alt,
            "placeholder": placeholder}


# =============================================================== THE PIZZA LAB
# Rebuilt from the existing LAB so the menu-tied lists and the reasoning that
# goes with them stay in play.py. Nothing about this lab changes: same URL,
# same fields, same order, same default.
PIZZA = _lab(
    slug="pizza-lab", placeholder="The Meat Monster 3000", name="The Pizza Lab", short="Pizza", unit="pizza",
    h1=_PIZZA["h1"], lede=_PIZZA["lede"],
    groups=[
        {"key": "sauce", "legend": "Sauce", "pick": "one",
         "options": _PIZZA["sauce"]},
        {"key": "cheese", "legend": "Cheese", "pick": "one",
         "options": _PIZZA["cheese"]},
        # field, not key: the input is named "topping" and the live
        # lab-submit function expects "toppings" in the JSON. The Pizza Lab's
        # payload has to stay byte-identical to what is already deployed.
        {"key": "topping", "field": "toppings", "legend": "Toppings",
         "pick": "many", "max": _PIZZA["max_toppings"],
         "options": _PIZZA["toppings"]},
        {"key": "finish", "legend": "Finish", "pick": "one",
         "options": _PIZZA["finish"], "default": _PIZZA["finish_default"],
         "silent": _PIZZA["finish_default"], "prefix": "finished with"},
    ],
    how=_PIZZA["how"], rules=_PIZZA["rules"], nxt=_PIZZA["next"],
    live=True, endpoint="lab_endpoint",
    art="margherita-board",
    alt="A wood-fired pizza on the board at Square Peg")

# =============================================================== THE PASTA LAB
# Brian's list, 11.10.26. Three judgement calls, all of them visible here
# rather than buried:
#
#   * His add-ins had "roasted peppers" and "Roasted Red Peppers" in the same
#     list. A radio or checkbox group cannot carry the same thing twice under
#     two spellings, and the line would not know which one an entry meant, so
#     it is one chip.
#   * Parmesan, chili oil and red pepper flakes were in BOTH the add-ins and
#     the finishes. They are finishes -- they go on at the pass -- so that is
#     the only group they appear in. Otherwise a build reads "...chili oil,
#     finished with chili oil", which is not a thing anyone would order.
#   * The add-ins run to nineteen chips, half of them cheese, so they are
#     sectioned the way the bar's bottles are.
#
# Nothing is pre-checked on the shape, the sauce or the protein. Whatever is
# checked when the page loads is what every half-interested visitor sends, and
# a pasta entry is worth nothing if it only tells us that spaghetti was first.
_PASTA_ADD = [
    ("From the kitchen",
     ["Arugula", "Basil", "Black olives", "Roasted fennel",
      "Caramelized onions", "Fig jam", "Garlic", "Hot cherry peppers",
      "Mushrooms", "Red onion", "Roasted red peppers", "Tomatoes"]),
    ("Cheese",
     ["Ricotta", "Fontina", "Fresh mozzarella", "Shredded mozzarella",
      "Goat cheese"]),
]

NONE_FINISH = "Nothing \u2014 leave it alone"

PASTA = _lab(
    live=True, endpoint="lab_endpoint", slug="pasta-lab", placeholder="The Midnight Rigatoni",
    name="The Pasta Lab", short="Pasta", unit="pasta",
    h1="The next Square Peg pasta could be yours.",
    lede="Three shapes, four sauces and everything our kitchens keep on the "
         "line. Build the plate you would actually order and give it a name.",
    groups=[
        {"key": "base", "legend": "Pasta", "pick": "one", "required": True,
         "options": ["Spaghetti", "Rigatoni", "Gluten-free penne"]},
        {"key": "sauce", "legend": "Sauce", "pick": "one", "required": True,
         "options": ["Marinara", "Bolognese", "Parm cream", "Olive oil"]},
        {"key": "protein", "legend": "Protein", "pick": "one", "required": True,
         "options": ["Roasted chicken", "Fried chicken", "Meatballs",
                     "Sausage", "Salmon", "Prosciutto", "Bacon", "Pepperoni",
                     "Anchovies", NONE_PROTEIN],
         "silent": NONE_PROTEIN},
        {"key": "topping", "legend": "Add-ins", "pick": "many", "max": 4,
         "optional": True, "sections": _PASTA_ADD},
        {"key": "finish", "legend": "Finish", "pick": "one",
         "prefix": "finished with",
         "options": ["Parmesan", "Hot honey", "Chili oil", "Balsamic glaze",
                     "Red pepper flakes", NONE_FINISH],
         "default": NONE_FINISH, "silent": NONE_FINISH},
    ],
    how=[
        ("lab_build", "Build it",
         "Pick a shape, a sauce, a protein, up to four add-ins and a finish. "
         "Everything on the list is something our kitchens already stock."),
        ("lab_name", "Name it",
         "This is the part people remember. Keep it clean \u2014 a person "
         "reads every entry."),
        ("lab_win", "It goes on the menu",
         "The one we choose runs as a special across all ten Square Pegs, "
         "credited to whoever built it."),
    ],
    rules=["Up to four add-ins. Past that the sauce stops being the point.",
           "One entry per person a month, so everyone gets a fair shot."],
    nxt=["Entries come straight to our kitchen team.",
         "We go through them and pick the one we most want to make. It runs "
         "as a special at all ten Square Pegs.",
         "If we picked yours, you\u2019ll see it on the menu with your first "
         "name and last initial beside it."],
    art="lto-eggplant",
    alt="Eggplant fries with marinara at Square Peg")

# ============================================================ THE SANDWICH LAB
SANDWICH = _lab(
    live=True, endpoint="lab_endpoint", slug="sandwich-lab", placeholder="The Shelton Slammer", name="The Sandwich Lab", short="Sandwich",
    unit="sandwich",
    h1="The next Square Peg sub could be yours.",
    lede="Ten inches of roll or a wrap, and everything our kitchens keep "
         "behind the line. Build the sandwich you actually want and give it "
         "a name.",
    groups=[
        {"key": "base", "legend": "Roll or wrap", "pick": "one",
         "options": ["10″ sub roll", "Wrap"]},
        {"key": "protein", "legend": "Protein", "pick": "one", "required": True,
         "options": _SUB_PROTEIN + [NONE_PROTEIN], "silent": NONE_PROTEIN},
        {"key": "cheese", "legend": "Cheese", "pick": "one", "required": True,
         "options": _CHEESE + [NONE_CHEESE], "silent": NONE_CHEESE},
        {"key": "greens", "legend": "Greens", "pick": "one", "required": True,
         "options": _GREENS + [NONE_GREENS], "silent": NONE_GREENS},
        {"key": "topping", "legend": "Pile it on", "pick": "many", "max": 4,
         "optional": True, "options": _VEG},
        {"key": "sauce", "legend": "Sauce or dressing", "pick": "one",
         "options": _SUB_SAUCES, "prefix": "with"},
    ],
    how=[
        ("lab_build", "Build it",
         "Pick a roll or a wrap, a protein, a cheese, up to four more things "
         "and a sauce. Everything on the list is something our kitchens "
         "already stock."),
        ("lab_name", "Name it",
         "This is the part people remember. Keep it clean — a person "
         "reads every entry."),
        ("lab_win", "It goes on the menu",
         "The one we choose runs as a special across all ten Square Pegs, "
         "credited to whoever built it."),
    ],
    rules=["Up to four extras. Past that it stops being a sandwich and starts "
           "being a salad in a roll.",
           "One entry per person a month, so everyone gets a fair shot."],
    nxt=["Entries come straight to our kitchen team.",
         "We go through them and pick the one we most want to make. It runs "
         "as a special at all ten Square Pegs.",
         "If we picked yours, you’ll see it on the menu with your first "
         "name and last initial beside it."],
    art="catering-table",
    alt="A spread of food on the table at Square Peg")

# =============================================================== THE SALAD LAB
SALAD = _lab(
    live=True, endpoint="lab_endpoint", slug="salad-lab", placeholder="The Green Peg", name="The Salad Lab", short="Salad", unit="salad",
    h1="The next Square Peg salad could be yours.",
    lede="Greens, the good stuff on top, and a dressing that earns its place. "
         "Build it from what our kitchens already keep and give it a name.",
    groups=[
        {"key": "greens", "legend": "Greens", "pick": "one",
         "options": _GREENS},
        {"key": "protein", "legend": "Protein", "pick": "one", "required": True,
         "options": _SALAD_PROTEIN + [NONE_PROTEIN], "silent": NONE_PROTEIN},
        {"key": "cheese", "legend": "Cheese", "pick": "one", "required": True,
         "options": _CHEESE + [NONE_CHEESE], "silent": NONE_CHEESE},
        {"key": "topping", "legend": "On top", "pick": "many", "max": 5,
         "optional": True, "options": _VEG},
        {"key": "dressing", "legend": "Dressing", "pick": "one",
         "options": _DRESSINGS, "prefix": "with"},
    ],
    how=[
        ("lab_build", "Build it",
         "Pick your greens, a protein, a cheese, up to five things on top and "
         "a dressing. Everything on the list is something our kitchens "
         "already stock."),
        ("lab_name", "Name it",
         "This is the part people remember. Keep it clean — a person "
         "reads every entry."),
        ("lab_win", "It goes on the menu",
         "The one we choose runs as a special across all ten Square Pegs, "
         "credited to whoever built it."),
    ],
    rules=["Up to five things on top. A salad with everything on it is a bin.",
           "One entry per person a month, so everyone gets a fair shot."],
    nxt=["Entries come straight to our kitchen team.",
         "We go through them and pick the one we most want to make. It runs "
         "as a special at all ten Square Pegs.",
         "If we picked yours, you’ll see it on the menu with your first "
         "name and last initial beside it."],
    art="table-spread",
    alt="A table of food at Square Peg")

# ================================================================= THE BAR LAB
# Sixty-odd bottles is unreadable as one run of chips, so the base is sectioned
# by category the way a back bar is actually organised.
#
# Still wines are deliberately not a base. You do not build a cocktail on a
# Merlot, and offering the varietal list here would produce entries the bar
# cannot make. Prosecco is in, because a spritz is a real drink.
#
# The fruit purees carry Brian's own caveat that they vary by location, which
# is on the page rather than left for someone to discover at the bar.
_SPIRITS = [
    # Brian's list has New Amsterdam under vodka and "Amsterdam" under gin.
    # Two different bottles, and a radio group cannot carry the same value
    # twice, so both are spelled out -- which also saves the bar guessing
    # which one an entry meant.
    ("Vodka", ["Grey Goose", "Ketel One", "Ketel One Citroen", "Tito’s",
               "New Amsterdam Vodka", "Smirnoff Vanilla", "Svedka Raspberry",
               "Deep Eddy Grapefruit"]),
    ("Gin", ["Hendrick’s", "Bombay Sapphire", "Tanqueray",
             "New Amsterdam Gin"]),
    ("Rum", ["Bacardi White", "Captain Morgan Spiced", "Captain Morgan White",
             "Malibu"]),
    ("Tequila & mezcal", ["Casamigos Blanco", "Casamigos Reposado",
                          "Casamigos Añejo", "Patrón Silver",
                          "Espolòn Blanco", "Espolòn Reposado",
                          "Montezuma Silver", "Banhez"]),
    ("Whiskey", ["Jameson", "Jameson Black Barrel", "Jameson Orange",
                 "Jack Daniel’s", "Jack Daniel’s Apple", "Crown",
                 "Fireball"]),
    ("Bourbon & rye", ["Maker’s Mark", "Woodford Bourbon", "Woodford Rye",
                       "Knob Creek Bourbon", "Knob Creek Rye", "Basil Hayden",
                       "Eagle Rare", "Elijah Craig", "Angel’s Envy",
                       "Heaven’s Door", "WhistlePig Rye"]),
    ("Scotch", ["Dewar’s White Label", "Glenlivet 12",
                "Johnnie Walker Double Black"]),
    ("Liqueur", ["Aperol", "Averna", "Bailey’s", "Campari",
                 "Chambord", "Cynar", "Elderflower liqueur", "Fernet-Branca",
                 "Gozio Amaretto", "Grand Marnier", "Jägermeister",
                 "Kahlúa", "Peach schnapps", "RumChata", "Rumple Minze",
                 "Sambuca"]),
    ("Bubbles", ["Prosecco"]),
]

_MIXERS = ["Cranberry juice", "Orange juice", "Apple juice", "Pineapple juice",
           "Lime juice", "Lemon juice", "Grapefruit juice", "Bloody Mary mix",
           "Coke", "Diet Coke", "Sprite", "Orange soda", "Root beer",
           "Lemonade", "Iced tea", "Cold brew coffee", "Club soda", "Tonic",
           "Red Bull"]

NONE_MIXER = "Straight up — no mixer"
NONE_FRUIT = "No fruit"
NONE_RIM = "No rim"

BAR = _lab(
    live=True, endpoint="lab_endpoint", slug="bar-lab", placeholder="The Vernon Sunset", name="The Bar Lab", short="Drink", unit="drink",
    h1="The next Square Peg cocktail could be yours.",
    lede="Everything behind our bar, and a blank glass. Build the drink you "
         "wish we served and give it a name — the one we pick goes on the "
         "cocktail list.",
    groups=[
        {"key": "base", "legend": "Base", "pick": "one", "sections": _SPIRITS},
        {"key": "mixer", "legend": "Mixer", "pick": "one", "required": True,
         "options": _MIXERS + [NONE_MIXER], "silent": NONE_MIXER},
        {"key": "fruit", "legend": "Fruit", "pick": "one",
         "options": ["Strawberry", "Raspberry", "Watermelon", "Passion fruit",
                     "Dragon fruit", "Coconut", "Jalapeño", NONE_FRUIT],
         "default": NONE_FRUIT, "silent": NONE_FRUIT},
        {"key": "garnish", "legend": "Garnish", "pick": "many", "max": 2,
         "optional": True, "prefix": "garnished with",
         "options": ["Lemon", "Lime", "Orange", "Cherry", "Pineapple",
                     "Olives", "Mint", "Jalapeños"]},
        {"key": "rim", "legend": "Rim", "pick": "one",
         "prefix": "rimmed in",
         "options": ["Sugar", "Salt", "Caramel", "Chocolate", NONE_RIM],
         "default": NONE_RIM, "silent": NONE_RIM},
    ],
    how=[
        ("lab_build", "Build it",
         "Pick a base, a mixer, a fruit, a garnish and a rim. Every bottle on "
         "the list is one we actually pour."),
        ("lab_name", "Name it",
         "This is the part people remember. Keep it clean — a person "
         "reads every entry."),
        ("lab_win", "It goes on the list",
         "The one we choose goes on the cocktail list, credited to whoever "
         "built it."),
    ],
    rules=["You have to be 21 or over to enter this one.",
           "Up to two garnishes. It is a drink, not a fruit salad.",
           "One entry per person a month, so everyone gets a fair shot."],
    nxt=["Entries come straight to our bar team.",
         "We go through them and pick the one we most want to pour. It goes "
         "on the cocktail list at all ten Square Pegs.",
         "If we picked yours, you’ll see it there with your first name "
         "and last initial beside it."],
    note="21+. The fruit purees vary a little by location — if the one "
         "you picked isn’t in that night, the bar will say so.",
    art="sp-drinks",
    alt="Cocktails on the bar at Square Peg")

# Order matters: it is the order of the cards on the hub and of the tabs.
BUILDERS = [PIZZA, PASTA, SANDWICH, SALAD, BAR]
BY_SLUG = {b["slug"]: b for b in BUILDERS}


def spec(b):
    """What the browser needs to run this lab, as JSON-ready data.

    `kind` is present for every lab except the Pizza Lab. That is deliberate:
    the Pizza Lab's payload is already accepted by a deployed function and
    nothing about it changes here, extra keys included. The new labs identify
    themselves so one function can serve all four.
    """
    out = {"unit": b["unit"], "groups": []}
    if b["slug"] != "pizza-lab":
        out["kind"] = b["slug"]
    for g in b["groups"]:
        out["groups"].append({
            "key": g["key"],
            "field": g.get("field", g["key"]),
            "pick": g["pick"],
            "max": g.get("max", 0),
            "silent": g.get("silent", ""),
            "prefix": g.get("prefix", ""),
            "optional": bool(g.get("optional")),
        })
    return out


# --------------------------------------------------------------------- checks
# These run at import, which means a bad list fails the build rather than
# shipping a lab nobody can submit to.
for _b in BUILDERS:
    _keys = [g["key"] for g in _b["groups"]]
    assert len(_keys) == len(set(_keys)), \
        f"{_b['slug']}: two groups share a key: {_keys}"
    for _g in _b["groups"]:
        _opts = ([o for _, xs in _g["sections"] for o in xs]
                 if "sections" in _g else _g["options"])
        assert _opts, f"{_b['slug']}/{_g['key']}: no options"
        assert len(_opts) == len(set(_opts)), \
            f"{_b['slug']}/{_g['key']}: duplicate option"
        for _k in ("default", "silent"):
            if _g.get(_k) is not None:
                assert _g[_k] in _opts, (
                    f"{_b['slug']}/{_g['key']}: {_k} is {_g[_k]!r}, "
                    f"which is not one of its options")
        if _g["pick"] == "many":
            assert _g.get("max"), f"{_b['slug']}/{_g['key']}: many needs a max"
            assert _g["max"] <= len(_opts), \
                f"{_b['slug']}/{_g['key']}: max is more than the list holds"
        else:
            assert "max" not in _g, \
                f"{_b['slug']}/{_g['key']}: max means nothing on a one-pick"
