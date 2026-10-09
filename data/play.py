"""The Playground — the interactive pages at /play/.

Three rules this file exists to enforce.

1. Every wheel item is something you can actually order. A wheel that lands on
   a pizza we don't make is a worse experience than no wheel.
2. Nothing here takes free text from the public. The confession page is a fixed
   checklist, not a submission box, because a word filter does not catch
   harassment, defamation, a slur spelled sideways or someone typing their own
   phone number — and this is our own domain.
   The one exception is the Pizza Lab, which is why every Lab submission goes
   to a moderation queue and nothing publishes without a human approving it.
3. Each debate carries real written commentary, not just a vote widget. A page
   that is a widget and forty words is thin, and thin pages drag the site down.

Vote tallies are baked into the build and refreshed nightly, so the numbers are
in the server-rendered HTML where Google can read them. See POLLS in build.py
and .github/workflows/refresh-polls.yml.
"""

# ---------------------------------------------------------------- the hub

PLAY = {
    "eyebrow": "The Square Peg Playground",
    "h1": "Because pizza shouldn’t be so serious.",
    "lede": "A wheel for when nobody can decide, the arguments our dining rooms "
            "have been having for twenty years, and the confessions you were "
            "never going to say out loud.",
    "intro": [
        "We run ten pizzerias. A thing you learn running ten pizzerias is that "
        "most of the time at a table isn’t spent eating — it’s spent deciding. "
        "Who wants what, whether to get two or three, whether the person who "
        "suggested pineapple should be allowed to order at all.",
        "So we built the arguments a website. No sign-up, no email, nothing to "
        "download. Settle it, order, get on with your night.",
    ],
}

# ---------------------------------------------------------------- the wheels
#
# Every item is on the menu right now. When the menu changes, these change.

WHEELS = [
    {
        "slug": "pizza",
        "name": "What pizza should I order?",
        "short": "Pick my pizza",
        "prompt": "Six pies. One spin. No further discussion.",
        "items": [
            ("Spicy Margherita", "Cherry peppers, spicy capicola, fresh mozzarella, basil."),
            ("Margherita", "Fresh mozzarella, tomato sauce and basil. The one we’re judged on."),
            ("Prince of Paramus", "House pork meatballs, mushrooms, mozzarella, tomato sauce."),
            ("Bianco", "Goat cheese, ricotta, garlic, maple and Calabrian chili oil."),
            ("Detroit-style", "Thick, crispy-edged pan pizza. Corner slice or it didn’t happen."),
            ("Build your own", "Fine. Do it your way. We’ll still make it properly."),
        ],
    },
    {
        "slug": "dinner",
        "name": "What’s for dinner tonight?",
        "short": "Decide dinner",
        "prompt": "You’ve been staring at the menu for nine minutes. Let go.",
        "items": [
            ("A large pizza", "Whatever’s on it, there’ll be leftovers. That’s tomorrow’s lunch sorted too."),
            ("Pasta alla Vodka", "Rigatoni, garlic tomato cream, basil, Calabrian chili oil."),
            ("Chicken Parm", "The sandwich or over pasta. Both are correct."),
            ("Wood-fired wings", "Start here. Decide the rest later."),
            ("The Hot Honey Eggplant", "The sub people come back for and then can’t remember the name of."),
            ("Spaghetti &amp; Meatballs", "House-made pork meatballs. Nobody has ever regretted this."),
        ],
    },
    {
        "slug": "table",
        "name": "What should we order for the table?",
        "short": "Feed the table",
        "prompt": "For when there are six of you and no leader has emerged.",
        "items": [
            ("Wings and a large pie", "The default for a reason."),
            ("Two pies, one red one white", "The diplomatic answer."),
            ("Meatballs, a Caesar, and a Detroit", "Order of operations matters here."),
            ("Calamari and the Prince of Paramus", "Somebody at your table will be very pleased."),
            ("Fried mozzarella, garlic bread, and whatever else", "Carbs first, questions later."),
            ("Three pies. Just get three.", "You know how this ends. Get three."),
        ],
    },
    {
        "slug": "date-night",
        "name": "Date night roulette",
        "short": "Date night",
        "prompt": "Take the decision off the table so you can talk about something else.",
        "items": [
            ("Split a Bianco", "Goat cheese and hot honey. Reads as thoughtful. Costs the same as everything else."),
            ("Margherita and a bottle", "Half-price bottles on Fridays, which is worth knowing."),
            ("Wings, a salad, and one pie", "The order of someone with their life together."),
            ("Two cocktails first, decide after", "Happy hour runs every day from 2 to 6."),
            ("Spicy Margherita, and don’t warn them", "A test, really."),
            ("Whatever they want. Just agree.", "The universe has read the room."),
        ],
    },
]

# ---------------------------------------------------------------- the debates
#
# Each one needs a real answer under it. The vote is the hook; the writing is
# what makes the page worth indexing and worth linking to.

DEBATES = [
    {
        "slug": "pineapple-on-pizza",
        "q": "Does pineapple belong on pizza?",
        "title": "Does Pineapple Belong on Pizza? | The Great Pizza Debate",
        "desc": "The oldest argument in pizza, settled by vote. See how Connecticut "
                "and Florida disagree, and what a wood-fired pizzeria actually thinks.",
        "options": [("yes", "Yes, and you’re all cowards"), ("no", "Absolutely not")],
        "take": "Where we land",
        "prose": [
            "Hawaiian pizza was invented in 1962 in Chatham, Ontario, by a Greek "
            "immigrant named Sam Panopoulos, who put canned pineapple on a pie "
            "because he was bored. It is, by any honest reading, not Italian and "
            "not Hawaiian, which is part of why people enjoy being angry about it.",
            "The actual culinary argument is less dramatic than the internet "
            "version. Sweet and salty is a combination nobody objects to anywhere "
            "else — prosciutto and melon, hot honey on a spicy pie, maple on our "
            "Bianco. The genuine problem with pineapple is water. Canned pineapple "
            "on a pizza that goes into a 700-degree oven releases liquid onto the "
            "crust, and a soggy centre is a real defect rather than a matter of "
            "taste.",
            "So our position is narrow: the flavour is defensible, the execution "
            "usually isn’t. If you want it, we’ll make it, and we’ll tell the "
            "kitchen to go easy so you get a crust instead of a swamp.",
        ],
    },
    {
        "slug": "ranch-with-pizza",
        "q": "Ranch dressing with pizza: yes or no?",
        "title": "Ranch With Pizza: Yes or No? | The Great Pizza Debate",
        "desc": "Ranch on pizza divides every table in Connecticut. Vote, see the "
                "results, and read where a wood-fired pizzeria actually stands.",
        "options": [("yes", "Yes, obviously"), ("no", "It’s a crust, not a crudité")],
        "take": "Where we land",
        "prose": [
            "This one splits almost perfectly along regional lines, and the split "
            "is older than most people arguing about it. Ranch arrived at the pizza "
            "table through chain delivery in the 1980s, as a dip for the crust ends "
            "nobody was eating, and in large parts of the country it simply became "
            "part of how pizza is served.",
            "The case against is that a good crust is already seasoned and already "
            "has char on it, and drowning that in buttermilk and dried herb is "
            "covering up the part we spent two days fermenting. The case for is "
            "that people like it, and a pizzeria that lectures its customers about "
            "dipping sauce has lost sight of the job.",
            "We keep ranch behind the counter. We will bring it to you without "
            "making a face. We would gently suggest trying the first slice without "
            "it, because if the crust needs ranch, that’s our failure and we’d "
            "rather know.",
        ],
    },
    {
        "slug": "fold-or-flat",
        "q": "Fold your slice, or eat it flat?",
        "title": "Fold Your Pizza or Eat It Flat? | The Great Pizza Debate",
        "desc": "The fold is structural engineering, not a personality trait. Vote "
                "on how a slice should be held and see what everyone else does.",
        "options": [("fold", "Fold it"), ("flat", "Flat, like a civilised person")],
        "take": "Where we land",
        "prose": [
            "The fold isn’t an affectation, it’s structural. Folding a slice "
            "along its centre line turns a floppy triangle into a beam — the same "
            "reason corrugated cardboard holds weight and a flat sheet doesn’t. "
            "On an 18-inch pie with a thin centre, the fold is the only thing "
            "between you and toppings in your lap.",
            "Which tells you when each side is right. A big thin round wants the "
            "fold. A Detroit-style square, with a thick base and a crisp cheese "
            "edge, does not fold and shouldn’t be asked to. A 12-inch "
            "neo-Neapolitan is firm enough to hold itself flat if you support it "
            "near the crust.",
            "So the honest answer is that this is an argument about pizza sizes "
            "disguised as an argument about character. Both camps are describing "
            "the last slice they ate.",
        ],
    },
    {
        "slug": "cold-leftover-pizza",
        "q": "Cold leftover pizza: better than hot?",
        "title": "Is Cold Pizza Better Than Hot? | The Great Pizza Debate",
        "desc": "Cold pizza from the fridge has genuine defenders and a real "
                "explanation. Vote and find out whether you’re in the majority.",
        "options": [("cold", "Cold, straight from the fridge"), ("hot", "Reheat it like an adult")],
        "take": "Where we land",
        "prose": [
            "There is something real underneath this one. Chilling changes how the "
            "fat in the cheese behaves and firms up the crumb, so a cold slice "
            "tastes saltier and more concentrated than the same slice hot. People "
            "who prefer cold pizza aren’t being contrary; they’re tasting a "
            "different thing.",
            "What nobody should defend is the microwave, which steams the crust "
            "from the inside and produces something with the texture of a damp "
            "towel. If you want it hot, a dry pan on a medium hob with a lid for "
            "two minutes will give you a crisp base and melted cheese, and takes "
            "about as long as the microwave.",
            "Our position: cold pizza at 7am standing at the fridge is a legitimate "
            "breakfast and we will not hear otherwise. Cold pizza when you had the "
            "option of a pan is a waste of a good crust.",
        ],
    },
    {
        "slug": "is-a-calzone-a-pizza",
        "q": "Is a calzone just a folded pizza?",
        "title": "Is a Calzone Just a Folded Pizza? | The Great Pizza Debate",
        "desc": "A question that sounds like a joke and has an actual answer. Vote, "
                "then read why the dough disagrees with you.",
        "options": [("yes", "Yes, it’s a pizza taco"), ("no", "No, it’s its own thing")],
        "take": "Where we land",
        "prose": [
            "No, and the reason is heat. An open pizza cooks by radiation from "
            "above and conduction from the deck, which is why the top chars and "
            "the base crisps. Seal the dough and the inside becomes a steam oven: "
            "the filling poaches in its own moisture rather than roasting.",
            "That changes what you can put in it. Wet mozzarella and raw vegetables "
            "that would be fine spread across an 18-inch round will flood a sealed "
            "pocket, which is why calzones traditionally use ricotta — a drier "
            "cheese that holds its shape when it heats.",
            "So the shapes are related and the cooking isn’t. Calling a calzone a "
            "folded pizza is like calling a dumpling a folded sandwich. You can see "
            "how you got there, and you are still wrong.",
        ],
    },
    {
        "slug": "fork-and-knife",
        "q": "Should pizza ever be eaten with a fork?",
        "title": "Should You Eat Pizza With a Fork? | The Great Pizza Debate",
        "desc": "There is exactly one situation where cutlery is correct, and most "
                "people guess wrong. Vote and see the split.",
        "options": [("never", "Never. Use your hands."), ("sometimes", "Sometimes it’s the only way")],
        "take": "Where we land",
        "prose": [
            "The purists lose this one on a technicality. A true Neapolitan pizza "
            "comes out of a 900-degree oven in ninety seconds with a deliberately "
            "wet centre, and in Naples it is normally eaten with a knife and fork, "
            "or folded into quarters as a <i>portafoglio</i>. Cutlery is not an "
            "American affectation; it’s closer to the original.",
            "Where the purists are right is everything else. A slice firm enough to "
            "pick up should be picked up. Attacking a reheated square of Detroit "
            "with a steak knife is not refinement, it’s a man avoiding joy.",
            "Our rule, such as it is: if the slice holds, use your hands. If it’s "
            "straight out of the oven and the middle is still moving, give it two "
            "minutes or use the fork and let nobody shame you.",
        ],
    },
]

# ---------------------------------------------------------------- confessions
#
# A fixed list. No submission box, no free text, no moderation queue, no way for
# this page to publish something we did not write. Visitors tick what they have
# done and see what share of everyone else admitted the same.

CONFESSIONS = {
    "eyebrow": "The confession booth",
    "h1": "Forgive us, for we have sinned against pizza.",
    "lede": "Tick the ones you’ve done. Nobody is watching, nothing is saved to "
            "your name, and you’ll find out how alone you really are.",
    "note": "Anonymous. We count the ticks, nothing else — no names, no accounts, "
            "no way back to you.",
    "items": [
        ("car", "Eaten an entire pizza in the car so nobody at home would know."),
        ("ketchup", "Put ketchup on a slice."),
        ("frozen", "Secretly preferred a frozen pizza to a restaurant one."),
        ("toppings", "Picked the toppings off and eaten them separately."),
        ("breakfast", "Had cold pizza for breakfast standing at the open fridge."),
        ("crust", "Left the crusts. All of them. In the box."),
        ("box", "Eaten out of the box over the sink and called it dinner."),
        ("last-slice", "Taken the last slice knowing full well whose it was."),
        ("ordered-twice", "Ordered a second pizza because the first one was taking too long."),
        ("microwave", "Microwaved leftover pizza and pretended it was fine."),
        ("pineapple", "Secretly enjoyed pineapple on pizza."),
        ("lied", "Said you were full and then kept eating."),
        ("hid", "Hidden the leftovers behind something so nobody else would find them."),
        ("floor", "Applied the five-second rule to a dropped slice."),
        ("whole-thing", "Ordered a large “for the family” with no intention of sharing."),
    ],
}

# ---------------------------------------------------------------- pizza lab
#
# NOT LINKED FROM THE SITE and noindex until Brian confirms kitchen and GM
# buy-in — he's sharing the URL with the kitchen first. See LAB_LIVE in
# data/content.py. Every ingredient here must be something the kitchen already
# stocks, or the winning pizza can't be made.

LAB = {
    "eyebrow": "The Square Peg Pizza Lab",
    "h1": "The next Square Peg pizza could be yours.",
    "lede": "Build it from what’s actually in our kitchens, give it a name, and "
            "put it in front of everyone else. The winner goes on the menu as a "
            "limited-time special.",
    "how": [
        ("Build it", "Pick a sauce, a cheese, up to four toppings and a finish. "
                     "Everything on the list is something our kitchens already "
                     "stock, so the winner is a pizza we can actually make."),
        ("Name it", "This is the part people remember. Keep it clean — every "
                    "entry is read by a person before it goes anywhere."),
        ("Everyone votes", "Approved builds go up for a public vote."),
        ("The winner gets made", "It runs as a limited-time special across all "
                                 "ten Square Pegs, with your name on it if you want it there."),
    ],
    # ⚠ CONFIRM WITH THE KITCHEN — this list is drawn from the current menu and
    # the catering tray menu, but nobody on the line has signed off on it yet.
    "sauce": ["Tomato", "White (garlic and oil)", "Vodka sauce", "Pesto", "No sauce"],
    "cheese": ["Fresh mozzarella", "Shredded mozzarella", "Ricotta", "Goat cheese",
               "Parmesan", "Vegan cheese"],
    "toppings": ["Pepperoni", "House pork meatballs", "Spicy capicola", "Prosciutto",
                 "Italian sausage", "Grilled chicken", "Mushrooms", "Cherry peppers",
                 "Roasted red peppers", "Caramelised onions", "Black olives",
                 "Fresh basil", "Baby arugula", "Roasted tomatoes", "Garlic",
                 "Jalapeños", "Eggplant", "Artichoke hearts"],
    "finish": ["Hot honey", "Calabrian chili oil", "Balsamic glaze", "Maple",
               "Olive oil and sea salt", "Fresh basil", "Nothing — leave it alone"],
    "max_toppings": 4,
    "rules": [
        "Up to four toppings. Everything after that is a mess, not a pizza.",
        "One entry per person per round, so the vote means something.",
        "Nothing publishes until one of us has read it.",
        "If yours wins, we’ll contact you before anything goes out with your name on it.",
    ],
}
