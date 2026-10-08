"""The handful of local pages that earn their place.

Not one page per town. Google's spam policies call that doorway abuse, and 160
near-identical "Pizza in [Town]" pages would put the whole site at risk. A page
belongs here only when it says something the location page cannot: a crowd with
its own reasons for turning up, a landmark worth naming, a payment method nobody
else takes.

Each entry is written, not generated. If a new one can't carry three sections of
content that are true only of that place, it doesn't belong on this list.

`store` must match a slug in LOCATIONS; `miles` rows come from
data/service_areas.json (straight-line, so they're stated as "about").
"""

TOWN_PAGES = [
    {
        "slug": "pizza-near-uconn",
        "store": "storrs-ct",
        "title": "Pizza Near UConn | Square Peg Pizzeria, Storrs Center",
        "desc": "Wood-fired pizza on Dog Lane in Storrs Center, steps from the UConn "
                "campus. Husky Bucks accepted, kitchen open late Thursday to Saturday, "
                "DJ on weekends.",
        "eyebrow": "Dog Lane, Storrs Center",
        "h1": "Pizza near UConn",
        "lede": "We&rsquo;re on Dog Lane in Storrs Center, a walk from the middle of campus. "
                "Our founders went to UConn, which is why this one feels less like a "
                "branch and more like coming home.",
        "hero": "friends-holiday",
        "sections": [
            ("Your One Card works here", "Husky Bucks",
             ["<b>We take Husky Bucks.</b> Dine in or order ahead for pickup and pay with "
              "your UConn One Card, same as cash. No separate account, no card to load, "
              "nothing to sign up for.",
              "It works on the full menu &mdash; pizza, pasta, wings, the lot &mdash; which is the "
              "part most people are surprised by. If you&rsquo;re ordering for a group and "
              "want to put a catering order on it, ask us first so we can set it up "
              "properly."]),
            ("After the game, after the show, after the library", "The kitchen runs late",
             ["Thursday through Saturday the kitchen stays open when most of Storrs has "
              "stopped cooking &mdash; until 11pm on Friday and Saturday nights.",
              "The DJ starts at 10pm on Friday and Saturday and runs to close. Wednesday "
              "is trivia, 6:30 to 8:30, which is the quieter end of the week and the "
              "better one if you actually want to hear each other."]),
            ("Parents&rsquo; weekend, move-in, graduation", "When the family&rsquo;s in town",
             ["Dog Lane is where Husky fans land after a game and where alumni reunions "
              "end up. If there are more than ten of you, send a large party request "
              "rather than turning up and hoping &mdash; graduation weekend in particular "
              "books out.",
              "Feeding a bigger group somewhere else on campus? Catering is pickup from "
              "here: trays of pasta, wings, salads and sandwiches, plus pizza, boxed and "
              "ready at a time you set."]),
            ("Clubs, teams and chapters", "Tuesday fundraisers",
             ["Bring your group in on a Tuesday and 20% of dine-in food sales goes back "
              "to your cause. It works for student organisations, club teams, Greek "
              "chapters and anything else that needs to raise money without running "
              "another bake sale.",
              "Pick your Tuesday, we&rsquo;ll give you something to share, and your people "
              "eat dinner they were going to eat anyway."]),
        ],
        "faq": [
            ("Does Square Peg take Husky Bucks?",
             "Yes. Our Storrs location on Dog Lane accepts Husky Bucks on your UConn One "
             "Card, for dine-in and for pickup orders, across the whole menu."),
            ("How far is it from the UConn campus?",
             "We&rsquo;re at 9 Dog Ln in Storrs Center, which is a walk from the middle of "
             "campus rather than a drive. Mansfield is about a mile out and Willimantic "
             "about seven."),
            ("How late is the kitchen open?",
             "Thursday through Saturday the kitchen runs late &mdash; until 11pm on Friday "
             "and Saturday. Earlier in the week it closes with the dining room."),
            ("Is there anything going on during the week?",
             "Trivia on Wednesday from 6:30 to 8:30, and a DJ from 10pm to close on "
             "Friday and Saturday. We also carry NFL Sunday Ticket."),
            ("Can we order for a club or a team?",
             "Yes, two ways. Catering is pickup from the Storrs kitchen for any headcount, "
             "and Tuesday fundraisers give 20% of dine-in food sales back to your group."),
        ],
    },
    {
        "slug": "pizza-near-mohegan-sun",
        "store": "preston-ct",
        "title": "Pizza Near Mohegan Sun & Foxwoods | Square Peg Preston",
        "desc": "Wood-fired pizza and Italian food on Route 165 in Preston, about nine "
                "miles from Mohegan Sun and a short drive from Foxwoods. Dinner before "
                "a show, or after one.",
        "eyebrow": "Route 165, Preston",
        "h1": "Pizza near Mohegan Sun",
        "lede": "About nine miles from Uncasville and a short run from Foxwoods, on "
                "Route 165. Far enough off the property to feel like a night out, "
                "close enough that you&rsquo;re back before the show starts.",
        "hero": "table-spread",
        "sections": [
            ("Before the show, or after it", "A real dinner, off the floor",
             ["Casino dining does one thing well and another thing badly: there&rsquo;s plenty "
              "of it, and almost none of it is quiet. Preston is the other option &mdash; a "
              "wood-fired kitchen on Route 165 where you sit down, order a pie and a "
              "drink, and have a conversation.",
              "If you&rsquo;re headed to the Arena, eat on the way in rather than fighting the "
              "post-show rush. Thursday the kitchen runs to 9pm, which covers most "
              "early curtains."]),
            ("Where it actually is", "Nine miles, not nine hundred",
             ["Preston sits between Norwich and the casinos, which means it&rsquo;s a short "
              "drive from most of southeastern Connecticut rather than a trip. Norwich is "
              "about five miles out, Ledyard six, Uncasville nine, and Mystic twelve.",
              "There&rsquo;s parking, which is its own argument."]),
            ("If you&rsquo;re staying the week", "Trivia, bingo and the football",
             ["Thursday is trivia, 7 to 9. Sunday is bingo at 6. And we carry NFL Sunday "
              "Ticket, so the games are on.",
              "It&rsquo;s a locals&rsquo; room that happens to be near two casinos, rather than a "
              "casino restaurant. Most weeks that&rsquo;s the better room to be in."]),
        ],
        "faq": [
            ("How far is Square Peg Preston from Mohegan Sun?",
             "About nine miles. We&rsquo;re at 353 CT-165 in Preston, between Norwich and the "
             "casinos &mdash; a short drive rather than a trip."),
            ("Is it close to Foxwoods?",
             "Yes. Foxwoods sits in Ledyard, which is about six miles from us, so we&rsquo;re "
             "an easy stop either side of a night there."),
            ("Do you take reservations for a group?",
             "For ten or more, send a large party request and we&rsquo;ll save the tables and "
             "plan the food so it lands together."),
            ("What&rsquo;s on during the week?",
             "Trivia on Thursday from 7 to 9, bingo on Sunday at 6, and NFL Sunday "
             "Ticket through the football season."),
            ("Which towns are you closest to?",
             "Norwich, Ledyard, Jewett City, Lisbon, Griswold and North Stonington are "
             "all within a few miles, with Uncasville, Mystic and Groton a little "
             "further out."),
        ],
    },
    {
        "slug": "pizza-near-boca-raton",
        "store": "delray-beach-fl",
        "title": "Pizza Near Boca Raton | Square Peg Pizzeria, Delray Beach",
        "desc": "Connecticut wood-fired pizza about seven miles north of Boca Raton, on "
                "West Atlantic Avenue in Delray Beach. Happy hour every day, dough and "
                "sauce made in house.",
        "eyebrow": "West Atlantic Avenue, Delray Beach",
        "h1": "Pizza near Boca Raton",
        "lede": "About seven miles north of Boca on West Atlantic Avenue. A Connecticut "
                "pizzeria that moved to Florida and brought its kitchen with it.",
        "hero": "kid-slice",
        "sections": [
            ("Why it tastes different", "The dough is made here",
             ["Our Delray kitchen makes its own dough and sauce from scratch, the same "
              "way our Connecticut kitchens do. It isn&rsquo;t trucked in part-baked and it "
              "isn&rsquo;t a franchise recipe &mdash; it&rsquo;s the same pizza nine other Square Pegs "
              "are making fifteen hundred miles north.",
              "Which is the whole reason this location exists. Enough people who grew up "
              "on it ended up down here that it stopped being a joke and became a "
              "restaurant."]),
            ("Every single day", "Happy hour, and a late one",
             ["Happy hour runs every day from 2 to 6, and again from 8:30 to close on "
              "Friday and Saturday &mdash; which is unusual enough in this stretch of Atlantic "
              "Avenue to be worth the drive up from Boca on its own.",
              "Sunday is jackpot bingo from 4 to 6, Monday bingo at 6:30, Wednesday "
              "trivia from 7 to 9. The football is on through the season."]),
            ("Who&rsquo;s actually coming", "Boca, Boynton and Highland Beach",
             ["Boca Raton is about seven miles south, Boynton Beach six north and "
              "Highland Beach five east, so most of the coastal strip is a short drive.",
              "Plenty of our regulars are snowbirds who knew the name before they knew "
              "the address. If you ate at a Square Peg in Glastonbury or Vernon twenty "
              "years ago, it&rsquo;s the same pizza."]),
        ],
        "faq": [
            ("How far is Square Peg from Boca Raton?",
             "About seven miles. We&rsquo;re at 4957 W Atlantic Ave in Delray Beach, a short "
             "drive north up the coast."),
            ("When is happy hour?",
             "Every day from 2 to 6, and again from 8:30 to close on Friday and "
             "Saturday nights."),
            ("Is this the same Square Peg as the Connecticut ones?",
             "Yes. Same family, same recipes, and the Delray kitchen makes its own dough "
             "and sauce from scratch exactly the way the Connecticut kitchens do."),
            ("What&rsquo;s on during the week?",
             "Jackpot bingo on Sunday from 4 to 6, bingo on Monday from 6:30 to 8:30, "
             "trivia on Wednesday from 7 to 9, and NFL Sunday Ticket in season."),
            ("Do you cater in the Delray and Boca area?",
             "Yes, as pickup from our Delray Beach kitchen. Trays of pasta, salads, "
             "wings, sandwiches and dessert, plus pizza, ready at a time you set. We "
             "don&rsquo;t deliver."),
        ],
    },
]
