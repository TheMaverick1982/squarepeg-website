"""
Square Peg Pizzeria — site content.
Everything the site says lives here. Edit this file, run `python3 build.py`, redeploy.
"""

import os

# ------------------------------------------------------------------ TOAST GO-LIVE SWITCH
# Today Toast serves ordering and menus on the main domain (squarepegpizzeria.com/order/...).
# At launch this website takes over the main domain and Toast moves to the order subdomain.
# On launch day set TOAST_ON_SUBDOMAIN = True, rebuild, push. That one change moves every
# Order / Menu / Gift card button, the search data and llms.txt to the subdomain.
# (The 301 redirects from old main-domain Toast URLs always point to the subdomain.)
# For a test build without editing this file: SP_TOAST_ON_SUBDOMAIN=1 python3 build.py --staging
TOAST_ON_SUBDOMAIN = True
TOAST_MAIN_DOMAIN = "https://squarepegpizzeria.com"          # where Toast lives today
TOAST_SUBDOMAIN = "https://order.squarepegpizzeria.com"      # where Toast lives after launch
# Paths on the Toast site. The redirects assume Toast keeps the same paths on the subdomain;
# confirm with Toast (LAUNCH_CHECKLIST.md) and change these if its paths differ.
TOAST_PATHS = {"order": "/order/", "picker": "/order", "menu": "/menu", "gift_cards": "/gift-cards"}
if os.environ.get("SP_TOAST_ON_SUBDOMAIN") in ("1", "0"):
    TOAST_ON_SUBDOMAIN = os.environ["SP_TOAST_ON_SUBDOMAIN"] == "1"
TOAST_HOST = TOAST_SUBDOMAIN if TOAST_ON_SUBDOMAIN else TOAST_MAIN_DOMAIN

SITE = {
    "name": "Square Peg Pizzeria",
    "domain": "https://squarepegpizzeria.com",
    # Where "Order" buttons go: TOAST_HOST + /order/<location's toast slug>. Set by the switch above.
    "order_base": TOAST_HOST + TOAST_PATHS["order"],
    "order_picker_toast": TOAST_HOST + TOAST_PATHS["picker"],
    # Menus live in Toast (per location, with live prices). "Menu" buttons open the location
    # picker and send guests to that location's Toast page. This is the fallback link.
    "menu_url": TOAST_HOST + TOAST_PATHS["menu"],
    # Toast eGift cards. If Toast gives you a different gift card link (e.g. https://www.toasttab.com/<slug>/giftcards),
    # replace this line with that full URL.
    "gift_cards_url": TOAST_HOST + TOAST_PATHS["gift_cards"],
    "email": "info@squarepegpizzeria.com",
    "app_link": "https://onelink.to/squarepeg-app",
    # "Sign in" in the header: the Toast ordering account (saved cards, past orders).
    # TODO confirm this is the right Toast account page once ordering is on the subdomain.
    "toast_account_path": "/account",
    "loyalty_signin": "https://squarepegpizzeria.comosense.net/auth/signin?callbackUrl=%2Fmember%2Frewards",
    # Rewards sign-up and sign-in are the same Como page.
    "loyalty_signup": "https://squarepegpizzeria.comosense.net/auth/signin?callbackUrl=%2Fmember%2Frewards",
    "careers": "/careers/",
    "careers_external": "https://jobs.squarepegpizzeria.com/careers",
    "careers_embed_src": "https://www.joinwingman.app/careers/square-peg-pizzeria?embed=1",
    # Pizza-making classes: tickets and upcoming dates (Eventbrite).
    "events_calendar_url": "https://www.eventbrite.com/o/square-peg-pizzeria-40036949473",
    "facebook": "https://www.facebook.com/squarepegpizzeria/",
    "instagram": "https://www.instagram.com/SquarePegPizzeria/",
    # No dedicated catering line: the catering form is the fastest route, or guests call their location.
    "catering_phone": "",
    "founded": "2020",
    # Chatbot (Vendasta web chat) — pasted verbatim from Square Peg.
    "chat_src": "https://cdn.apigateway.co/webchat-client..prod/sdk.js",
    "chat_widget_id": "c8ba1e1a-1e32-11f1-a953-6241c47b1fa1",
    # Contact form → Supabase (see supabase/contact_messages.sql and DEPLOY_VERCEL.md).
    # The anon key is public by design; the table only allows inserts.
    # Optional: send the contact form through the submit-contact Edge Function instead of
    # straight to the table, so a Cloudflare Turnstile check can be verified server-side.
    # Fill in both to switch it on (see SUPABASE_SETUP.md); leave blank to post to the table.
    "contact_endpoint": "",        # e.g. https://abcdefgh.functions.supabase.co/submit-contact
    "turnstile_site_key": "",      # Cloudflare Turnstile site key (public)
    "supabase_url": "https://ytkwogufrjffcgfpinrf.supabase.co",
    "supabase_anon_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl0a3dvZ3VmcmpmZmNnZnBpbnJmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk3MDM5MDIsImV4cCI6MjEwNTI3OTkwMn0.TBUjxGEnpo-sv7Yinb1GKIKOW14R2o1sYq5B_5viDPA",
    # Analytics — fill in to activate (left blank = nothing loads)
    "ga4_id": "G-REQKJC1SBJ",
    "meta_pixel_id": "",
}

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def h(mon, tue, wed, thu, fri, sat, sun):
    """Hours helper: each arg is ("11:30","21:00") or None for closed. Close past midnight = "01:00"."""
    return dict(zip(DAYS, [mon, tue, wed, thu, fri, sat, sun]))

# Hours below come from squarepegpizzeria.com/locations (Sept 2026).
# Several differ from the hours shown in Toast ordering — see LAUNCH_CHECKLIST.md.
LOCATIONS = [
    {
        "slug": "glastonbury-ct", "review_url": "https://g.page/r/CZzu2KdNLF0JEAE/review",
        # Kitchen closes before the bar on these days (from the store hours).
        "kitchen": {"Wed": "21:00", "Thu": "21:00", "Fri": "23:00"}, "name": "Glastonbury", "region": "Greater Hartford",
        "street": "1001 Hebron Ave", "city": "Glastonbury", "state": "CT", "zip": "06033",
        "phone": "(860) 286-0415", "toast": "square-peg-pizzeria",
        "lat": 41.717186, "lng": -72.574051, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("11:30","21:00"),("11:30","21:00"),("11:30","22:00"),("11:30","22:00"),("11:00","00:00"),("11:00","23:00"),("11:00","21:00"))),
        "tag": "Where it all started",
        "blurb": "Our first Square Peg. Glastonbury is where the wood-fired oven got lit in 2020, and it’s still where regulars come for date nights, team dinners, and the same pie they’ve ordered since day one.",
        "nearby": ["Wethersfield", "Rocky Hill", "Portland", "Hebron", "Marlborough"],
        "same_as": ["https://www.yelp.com/biz/square-peg-pizzeria-glastonbury-2"],
        "photo": "oven-pizza",
    },
    {
        "slug": "east-hartford-ct", "review_url": "https://g.page/r/CdU-gccb2zW6EAE/review", "menu_extra": ["Breakfast on weekends from 7am: omelettes and the Pegg & Cheese", "Brunch cocktails like mimosas, Bloody Marys and Aperol spritzes"], "name": "East Hartford", "region": "Greater Hartford",
        "street": "130 Long Hill St", "city": "East Hartford", "state": "CT", "zip": "06108",
        "phone": "(860) 509-4221", "toast": "square-peg-pizzera-east-hartford",
        "lat": 41.790362, "lng": -72.594171, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("11:00","22:00"),("11:00","20:30"),("11:00","20:30"),("11:00","22:00"),("11:00","20:30"),("07:00","20:30"),("07:00","22:00"))),
        "tag": "Breakfast on weekends",
        "blurb": "East Hartford is the one Peg serving breakfast: omelettes and the Pegg & Cheese from 7am on weekends. The rest of the week it’s the full Square Peg — wood-fired pizza, handmade pasta, parm sandwiches and a bar — on Long Hill Street, an easy stop off Route 2 or the Charter Oak Bridge.",
        "nearby": ["Hartford", "Manchester", "South Windsor", "Wethersfield", "Glastonbury"],
        "same_as": ["https://www.yelp.com/biz/square-peg-pizzeria-east-hartford"],
        "photo": "dough",
    },
    {
        "slug": "vernon-ct", "review_url": "https://g.page/r/Ca9plvDsyye4EAE/review",
        # Kitchen closes before the bar on these days (from the store hours).
        "kitchen": {"Wed": "21:00", "Thu": "21:00", "Fri": "23:00"}, "name": "Vernon", "region": "Greater Hartford",
        "street": "226 Talcottville Rd", "city": "Vernon", "state": "CT", "zip": "06066",
        "phone": "(860) 926-0088", "toast": "square-peg-pizzeria-vernon-226-talcottville-rd",
        "lat": 41.836661, "lng": -72.491494, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("12:00","20:00"),("12:00","20:00"),("12:00","21:00"),("12:00","21:00"),("12:00","23:00"),("11:00","23:00"),("11:00","20:00"))),
        "tag": "Open till midnight Fridays",
        "blurb": "Right on Talcottville Road (Route 83), Vernon is the easy stop for Rockville, Ellington and Tolland: pickup on the way home, or a late one on Friday when the oven runs until midnight.",
        "nearby": ["Rockville", "Ellington", "Tolland", "Manchester", "South Windsor"],
        "photo": "margherita-board",
    },
    {
        # "bar": False = no beer/wine/cocktails yet (liquor license pending); "detroit": False = no Detroit-style pizza yet. Remove each once available.
        # "wood": False = this is the one kitchen that is not wood-fired, so no page here says wood-fired.
        "slug": "bolton-ct", "review_url": "https://g.page/r/CWYf9GcLXaLlEBM/review", "bar": False, "detroit": False, "wood": False, "pastas": ["Chicken Parmesan", "Pasta alla Vodka", "Spaghetti & Meatballs", "The Bella Parmigiana"], "menu_extra": ["Burgers"], "name": "Bolton", "region": "Greater Hartford",
        "street": "270 West St", "city": "Bolton", "state": "CT", "zip": "06043",
        "phone": "(860) 791-7109", "toast": "square-peg-pizzeria-bolton-270-west-street",
        "lat": 41.742106, "lng": -72.436706, "geo_exact": True,  # US Census geocoder
        "hours": h(*(None,("11:00","20:00"),("11:00","21:00"),("11:00","21:00"),("11:00","21:00"),("11:00","21:00"),("11:00","20:00"))),
        "tag": "Newest Peg",
        "blurb": "Our newest Peg, on West Street in Bolton. Dough made fresh from scratch, never frozen, plus handmade pasta, parm sandwiches, wings and salads. A straightforward neighborhood spot — weeknight dinner with the family, or a pickup on the way through town.",
        "nearby": ["Manchester", "Coventry", "Andover", "Vernon", "Hebron"],
        "photo": "pizza-boxes",
    },
    {
        "slug": "storrs-ct", "review_url": "https://g.page/r/CVgVzNCipW3ZEAE/review", "sunday_ticket": True,
        # UConn campus payment, Storrs only. Flagged per location so no other
        # Peg ever advertises something it cannot take.
        "husky_bucks": True,
        # Kitchen closes before the bar on these days (from the store hours).
        "kitchen": {"Sun": "21:00", "Wed": "21:00", "Thu": "22:00", "Fri": "23:00", "Sat": "23:00"}, "name": "Storrs", "region": "Eastern CT",
        "street": "9 Dog Ln", "city": "Storrs", "state": "CT", "zip": "06268",
        "phone": "(860) 454-6038", "toast": "squarepegwindsor",
        "lat": 41.804999, "lng": -72.243305, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("11:30","21:00"),("11:30","21:00"),("11:30","21:00"),("11:30","00:00"),("11:00","00:00"),("11:00","23:00"),("11:00","21:00"))),
        "tag": "Steps from UConn",
        "blurb": "Our founders are UConn alumni, so Storrs Center feels like coming home. Dog Lane is where Husky fans land after the game and alumni reunions come together, and the kitchen runs late Thursday through Saturday.",
        "nearby": ["Mansfield", "Coventry", "Willington", "Ashford", "Tolland"],
        "photo": "friends-holiday",
    },
    {
        "slug": "preston-ct", "review_url": "https://g.page/r/CdzzsjM-nYI5EAE/review", "sunday_ticket": True,
        # Kitchen closes before the bar on these days (from the store hours).
        "kitchen": {"Wed": "21:00", "Thu": "21:00"}, "name": "Preston", "region": "Eastern CT",
        "street": "353 CT-165", "city": "Preston", "state": "CT", "zip": "06365",
        "phone": "(860) 319-0930", "toast": "square-peg-new-preston-353-connecticut-165",
        "lat": 41.528840, "lng": -71.982108, "geo_exact": True,  # exact pin from Google Maps
        "hours": h(*(("16:00","20:00"),("16:00","20:00"),("11:30","21:00"),("11:30","21:00"),("11:30","22:00"),("11:30","22:00"),("11:30","20:00"))),
        "tag": "Southeastern CT",
        "blurb": "On Route 165, Preston brings wood-fired pies to Norwich, Ledyard and the rest of the southeast corner of the state. It’s an easy dinner stop before or after a night at the casinos.",
        "nearby": ["Norwich", "Ledyard", "Griswold", "Lisbon", "North Stonington"],
        "photo": "table-spread",
    },
    {
        "slug": "plainville-ct", "review_url": "https://g.page/r/CRm0rKa4S61lEAE/review",
        # Kitchen closes before the bar on these days (from the store hours).
        "kitchen": {"Wed": "21:00", "Thu": "21:00"}, "name": "Plainville", "region": "Central CT",
        "street": "400 New Britain Ave", "city": "Plainville", "state": "CT", "zip": "06062",
        "phone": "(860) 996-0363", "toast": "square-peg-plainville-400-new-britain-avenue",
        "lat": 41.671493, "lng": -72.833556, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("11:30","21:00"),("11:30","21:00"),("11:30","21:00"),("11:30","21:00"),("11:00","23:00"),("11:00","23:00"),("11:00","20:00"))),
        "tag": "Central Connecticut",
        "blurb": "Plainville is our Central CT kitchen, close to New Britain, Southington and Farmington. Drop in, pick up on the way home, or plan a party we can feed.",
        "nearby": ["New Britain", "Southington", "Farmington", "Bristol", "Berlin"],
        "same_as": ["https://www.yelp.com/biz/square-peg-pizzeria-plainville"],
        "photo": "oven-fire",
    },
    {
        "slug": "berlin-ct", "review_url": "https://g.page/r/CaLinkTYNBDbEBM/review", "pastas": ["Chicken Parmesan", "Pasta alla Vodka", "Pasta Bolognese", "Spaghetti & Meatballs"], "menu_extra": ["Hot dogs"], "kids_menu": False, "salads": False, "parm_line": "meatball parm and Italian combo sandwiches", "name": "Berlin Truck Bar", "short": "Berlin", "region": "Central CT",
        "street": "151 Webster Square Rd", "city": "Berlin", "state": "CT", "zip": "06037",
        "phone": "(860) 505-4072", "toast": "square-peg-pizza-berlin-119-webster-square-road",
        "lat": 41.628734, "lng": -72.745911, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("16:00","21:00"),None,None,("16:00","22:00"),("11:00","23:00"),("11:00","23:00"),("11:00","19:00"))),
        "tag": "The Truck Bar",
        "blurb": "Berlin is our Truck Bar on Webster Square Road: brick-oven pizza, sandwiches, wings and a bar with an easy, hang-out feel. Come in for a weekend afternoon or a game night.",
        "nearby": ["Kensington", "New Britain", "Cromwell", "Newington", "Meriden"],
        "photo": "truck-tent",
    },
    {
        "slug": "shelton-ct", "review_url": "https://g.page/r/CSSSW9EazyNFEAE/review", "sunday_ticket": True,
        # Kitchen closes before the bar on these days (from the store hours).
        "kitchen": {"Wed": "21:00", "Thu": "21:00", "Fri": "22:00", "Sat": "22:00"}, "name": "Shelton", "region": "Fairfield & New Haven",
        "street": "320 Howe Ave, Unit 6", "city": "Shelton", "state": "CT", "zip": "06484",
        "phone": "(203) 538-5044", "toast": "square-peg-shelton-310-howe-avenue-unit-6",
        "lat": 41.314898, "lng": -73.091125, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("16:00","21:00"),("16:00","21:00"),("16:00","21:00"),("16:00","21:00"),("12:00","23:00"),("11:30","22:00"),("11:30","20:00"))),
        "tag": "Downtown Shelton",
        "blurb": "Our Fairfield County outpost on Howe Avenue, a short walk from the Riverwalk. Shelton brings the Square Peg oven to Derby, Stratford and the Valley.",
        "nearby": ["Derby", "Ansonia", "Stratford", "Trumbull", "Monroe"],
        "photo": "friends-sharing",
    },
    {
        "slug": "delray-beach-fl", "review_url": "https://g.page/r/CdcNVlETKllxEAE/review", "sunday_ticket": True, "name": "Delray Beach", "region": "Florida",
        "street": "4957 W Atlantic Ave", "city": "Delray Beach", "state": "FL", "zip": "33445",
        "phone": "(561) 566-8828", "toast": "square-peg-delray-beach-4957-west-atlantic-avenue",
        "lat": 26.457838, "lng": -80.12169, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("12:00","21:00"),("12:00","21:00"),("12:00","21:00"),("12:00","21:00"),("12:00","22:00"),("12:00","22:00"),("12:00","20:00"))),
        "tag": "Connecticut pizza in Florida",
        "blurb": "Connecticut pizza, Florida sunshine. Delray Beach has its own kitchen making dough and sauce from scratch, the same way East Hartford does for our Connecticut Pegs. On West Atlantic Avenue, our Delray Peg feeds snowbirds who missed their Glastonbury pie and locals who are just finding out what the fuss is about.",
        "nearby": ["Boynton Beach", "Boca Raton", "Lake Worth Beach", "Highland Beach"],
        "photo": "kid-slice",
    },
]

# "Sal" — the pairing assistant. The widget is a third-party embed (same SDK as the
# floating chat, different widget id), so the page suppresses the floating one to
# avoid two instances of the SDK on one page. Everything below the widget is real
# content: the page has to be worth landing on even if the widget fails to load.
PAIRING = {
    "widget_id": "ea5ec150-73e8-11f1-b4c7-6291690b83e2",
    "lede": "Tell Sal what you\u2019re ordering, who\u2019s at the table, or just what kind of night "
            "it is. You\u2019ll get a drink that actually fits \u2014 not a list of everything we pour.",
    "asks": [
        "What should I drink with a pepperoni pizza?",
        "We\u2019re splitting a white pizza and wings \u2014 one bottle for the table?",
        "Something that isn\u2019t beer, but isn\u2019t sweet either.",
        "First date. Don\u2019t let me order wrong.",
        "What goes with the fried eggplant?",
        "I like bourbon. Build me a dinner around that.",
    ],
    "steps": [
        ("Tell Sal what\u2019s on the table",
         "A pizza, a pasta, a whole order for four. However you\u2019d say it out loud."),
        ("Get a real recommendation",
         "One or two options, with the reason behind them \u2014 not a wine list dumped on your lap."),
        ("Order it",
         "Bring the answer to your server, or start an order online and work from there."),
    ],
    # House pairings, written as guidance rather than specific bottles, because the
    # list varies by location. Keep these honest — they are the SEO content here.
    "classics": [
        ("Pepperoni", "A hoppy IPA",
         "Pepperoni renders out a lot of fat and a fair amount of heat. Hop bitterness scrubs the "
         "fat off your palate between bites, so the last slice tastes like the first one did."),
        ("Margherita", "A dry Italian red, or a dry ros\u00e9",
         "A simple pie lives or dies on the tomato. You want acid to meet acid \u2014 a wine with "
         "some bite keeps the sauce bright instead of flattening it out."),
        ("A white pizza", "A crisp, unoaked white",
         "No tomato means no acid on the plate, so the glass has to bring it. Something lean and "
         "cold cuts through the cream and cheese rather than piling richness on richness."),
        ("Anything with chili or hot honey", "An off-dry white, or a cold lager",
         "A touch of sweetness takes the edge off capsaicin. High alcohol does the opposite \u2014 "
         "it makes heat burn hotter, which is why a big red is the wrong move here."),
        ("Wings", "A cold lager",
         "Carbonation and cold are doing the work. You want something that resets your mouth and "
         "gets out of the way, not a beer that competes with the sauce."),
        ("Handmade pasta", "A medium-bodied red",
         "Enough structure to stand next to a long-cooked sauce, enough acidity to keep a heavy "
         "bowl from turning into a nap."),
    ],
}

# The link-in-bio page. Ordered by what actually earns a tap from a social profile:
# ordering first, then the thing being promoted right now, then the booking paths.
# Keep this under about a dozen rows — a long list gets scrolled past, not read.
# ("Label", "destination", "sub-label or empty", "accent" True for the primary rows)
LINKS = [
    ("Order Online", "ORDER", "Pickup or delivery from any location", True),
    ("Find a Location", "/locations/", "Ten spots across CT and Delray Beach", False),
    ("This Month\u2019s Specials", "/monthly-specials/", "The limited-time menu, gone at the end of the month", True),
    ("Ask Sal: What Should I Drink?", "/pairing/", "Our pairing guide, free to use", False),
    ("Deals & Rewards", "/deals/", "Join free and start with $5 off", True),
    ("Gift Card Giveaway", "https://go.squarepegpizzeria.com/GC", "Enter this month\u2019s $50 drawing", False),
    ("Ongoing Promotions", "/promotions/", "Pasta, wings, wine and happy hour", False),
    ("Catering", "/catering/", "Office lunches, parties, game days", False),
    ("Tuesday Night Fundraisers", "/fundraisers/", "20% back to your school, team or cause", False),
    ("Large Party Reservations", "/large-party-reservations/", "Tables for eight or more", False),
    ("Food Truck Rentals", "/food-truck/", "Wood-fired pizza at your event", False),
    ("Gift Cards", "GIFT", "Send one in a minute", False),
    ("We\u2019re Hiring", "/careers/", "Every location, every shift", False),
]

# Pizza calculator. Sizes and slice counts come from MENU["pizza_styles"] — keep them
# in step. The math is area-based rather than a flat "3 slices each" rule, because an
# 18" slice is roughly 1.7x the area of a 12" slice and a flat rule badly under-orders
# for big pies. Appetite values are in square inches of pizza per person.
CALC = {
    "sizes": [
        # label, diameter/description, slices, area in square inches
        ("18\u2033 large round", "18\u2033", 8, 254),
        ("12\u2033 small round", "12\u2033", 6, 113),
        ("Detroit-style pan", "10\u00d714\u2033", 6, 140),
    ],
    "appetites": [
        ("light", "Light \u2014 a slice or two", 48),
        ("normal", "Normal \u2014 most people", 70),
        ("hearty", "Hearty \u2014 teenagers, game day", 95),
    ],
    "kid_area": 36,          # a child eats roughly half an adult portion
    "sides_discount": 0.80,  # apps, salads and wings take ~20% off the pizza needed
    "catering_threshold": 20,
    "notes": [
        ("Rounds come two ways", "A 12\u2033 round cuts into 6 slices, an 18\u2033 into 8. The large isn\u2019t "
         "just two more slices \u2014 it\u2019s more than twice the pizza, because area grows with the square "
         "of the diameter."),
        ("Detroit sits in between", "The 10\u00d714\u2033 pan is 6 thick, crispy-edged squares. It eats heavier "
         "than a round of the same area, so it goes further than the numbers suggest. Available at every "
         "location except Bolton."),
        ("Order one more than feels right", "Leftover pizza is a feature. Running out in front of your "
         "guests is not, and a second round of ordering adds half an hour to the night."),
        ("Mixed crowds round up", "Kids eat about half an adult portion, but they also eat unpredictably. "
         "If the split is close, take the larger number."),
    ],
}

# FAQ hub. Every answer has to be true for US — sizes come from MENU["pizza_styles"],
# food-safety numbers from USDA guidance. Generic pizza-blog filler loses to pizza blogs;
# the only edge here is answering as the people who actually make it.
PIZZA_FAQ = [
    ("Sizes & servings", [
        ("How many slices are in a large pizza?",
         "Ours is an 18\u2033 round cut into 8 slices. The 12\u2033 round is cut into 6, and the Detroit-style "
         "pan is 6 squares. Slice counts vary wildly between pizzerias \u2014 always ask by diameter, not by "
         "the word \u201clarge.\u201d"),
        ("How many people does a large pizza feed?",
         "Three to five adults if pizza is the whole meal, and more if there are appetizers on the table. "
         "An 18\u2033 pie is about 254 square inches, so each of its 8 slices is roughly 70% bigger than a "
         "slice off a 12\u2033. Our <a href=\"/pizza-calculator/\">pizza calculator</a> does the arithmetic."),
        ("Is a large pizza twice the size of a small?",
         "No \u2014 it\u2019s more than twice. Area grows with the square of the diameter, so going from a "
         "12\u2033 to an 18\u2033 gives you about 2.25 times the pizza, not 1.5 times. Two smalls are less "
         "food than one large."),
    ]),
    ("Reheating & leftovers", [
        ("Can you reheat wood-fired pizza?",
         "Yes, and a skillet beats a microwave every time. Put the slice in a dry pan over medium heat for "
         "about three minutes, then add a few drops of water to the pan away from the slice and cover it for "
         "another minute. The base re-crisps while the steam melts the cheese. A microwave does the opposite: "
         "it steams the crust soft."),
        ("How long does leftover pizza keep?",
         "USDA guidance for cooked leftovers is three to four days refrigerated, within two hours of coming "
         "off the table. Pizza is no exception, however convincing it looks on the counter the next morning."),
        ("Can you freeze pizza?",
         "You can. Wrap slices individually so they don\u2019t fuse, and reheat from frozen in a skillet or a "
         "hot oven rather than thawing first \u2014 thawed crust goes limp."),
    ]),
    ("Cheese, sauce & styles", [
        ("What\u2019s the difference between mozzarella and fresh mozzarella?",
         "Low-moisture mozzarella is aged and drier, so it browns, stretches and behaves predictably under "
         "high heat. Fresh mozzarella is packed in water or brine, has a milkier flavor and a softer texture, "
         "and releases moisture as it melts \u2014 which is why a Margherita made with it has those wet, "
         "creamy pools rather than an even blanket. Neither is better; they do different jobs."),
        ("What is a white pizza?",
         "A pizza built without tomato sauce. The base is usually cheese, cream, oil or garlic, which means "
         "there\u2019s no acidity on the plate to cut the richness \u2014 worth knowing when you pick a drink "
         "to go with it."),
        ("What is Detroit-style pizza?",
         "A thick rectangular pan pizza with cheese taken right to the edges, so it caramelizes against the "
         "hot pan and forms a crisp, chewy border. Ours is a 10\u00d714\u2033 pan cut into 6, available at "
         "every location except Bolton."),
        ("What does wood-fired actually change?",
         "Heat and speed. A wood-fired oven runs far hotter than a home oven and cooks a pie in minutes rather "
         "than tens of minutes, which puts char on the crust before the inside dries out. That\u2019s where the "
         "leopard-spotting and the chew come from."),
    ]),
    ("Ordering", [
        ("Do you have gluten-free pizza?",
         "We make a 12\u2033 gluten-free crust, and vegan cheese can go on any pizza. One honest caveat: our "
         "kitchens handle wheat flour all day, so we can\u2019t promise a coeliac-safe environment. If you "
         "have a serious allergy, tell your server and they\u2019ll walk you through what we can and can\u2019t "
         "guarantee."),
        ("How far ahead should I order for a party?",
         "For a handful of pies, the same day is usually fine. For a crowd, or anything on a Friday or "
         "Saturday evening, give us a day \u2014 and for twenty people or more, <a href=\"/catering/\">catering</a> "
         "is normally cheaper and arrives hot together rather than in waves."),
        ("Can I order a half-and-half pizza?",
         "On a round, yes \u2014 ask when you order. The Detroit pan is built differently and doesn\u2019t "
         "split as cleanly."),
    ]),
]

# Pizza trivia. Where a well-known story is disputed, say so — being the page that gets it
# right is more useful than being the hundredth page repeating the myth.
PIZZA_TRIVIA = {
    "facts": [
        ("The word is older than the dish you\u2019re picturing",
         "\u201cPizza\u201d turns up in a Latin document from Gaeta, in southern Italy, dated 997 AD \u2014 "
         "nearly eight centuries before tomatoes appeared on one. It referred to a flatbread.",
         True),
        ("Naples got UNESCO status for it",
         "In 2017 UNESCO added the art of the Neapolitan \u201cpizzaiuolo\u201d to its list of intangible "
         "cultural heritage \u2014 protecting the craft of making it, not the recipe.",
         True),
        ("Tomatoes were considered dangerous",
         "Europeans grew tomatoes as ornamental plants for two centuries before eating them, partly because "
         "the acid leached lead out of pewter plates and poisoned wealthy diners. The poor ate off wood, and "
         "ate tomatoes.",
         True),
        ("Pepperoni is an American invention",
         "Order pepperoni in Italy and you may get peppers \u2014 \u201cpeperoni\u201d is the Italian for "
         "bell peppers. The spicy cured sausage is Italian-American, and it is comfortably the most ordered "
         "topping in the United States.",
         True),
    ],
    "myths": [
        ("Queen Margherita inspired the Margherita",
         "The story \u2014 that Raffaele Esposito built a red, white and green pizza for Queen Margherita of "
         "Savoy in 1889 \u2014 is repeated everywhere, including by us until we looked into it. The supporting "
         "document has been challenged by historians as a likely forgery, and pizzas with those toppings were "
         "already being sold in Naples. Lovely story. Probably not history."),
        ("Pineapple is an Italian outrage",
         "Hawaiian pizza was invented in Ontario, Canada, in 1962, by a Greek-born restaurateur. Italy was "
         "never consulted and has nothing to do with it either way."),
        ("Authentic pizza must be thin and crispy",
         "A true Neapolitan base is soft and foldable in the middle with a puffed, blistered rim \u2014 not "
         "cracker-crisp. The crisp-throughout style is a later, largely American development."),
    ],
}

# "What pizza are you?" — results map to real menu items only, so every result can link
# straight to an order. Each answer carries a score for each result key.
QUIZ = {
    "results": {
        "spicy-margherita": ("Spicy Margherita", "pie-spicy-margherita",
            "You like a little trouble. Cherry peppers, spicy capicola, fresh mozzarella and basil \u2014 "
            "familiar enough to be comforting, hot enough to keep you honest."),
        "margherita": ("Margherita", "pie-margherita",
            "You have nothing to prove. Fresh mozzarella, tomato and basil, fire-kissed. The one that exposes "
            "a bad pizzeria and rewards a good one."),
        "prince": ("Prince of Paramus", "pie-prince-of-paramus",
            "You order like you mean it. House pork meatballs, mushrooms, mozzarella and tomato sauce \u2014 "
            "dinner, not a snack."),
        "bianco": ("Bianco", "pie-bianco",
            "You read the whole menu before deciding. Goat cheese, ricotta, garlic, maple and Calabrian chili "
            "oil \u2014 sweet, sharp and a bit contrary."),
        "detroit": ("Detroit-style", "pie-detroit",
            "You\u2019re in it for the edges. A thick 10\u00d714\u2033 pan with the cheese taken right to the "
            "rim so it caramelizes against the metal. At every location except Bolton."),
    },
    "questions": [
        ("It\u2019s Friday at 7pm. Where are you?", [
            ("At the bar, ordering a second one", {"spicy-margherita": 2, "detroit": 1}),
            ("A corner table with one other person", {"margherita": 2, "bianco": 1}),
            ("At home, box on the coffee table", {"detroit": 2, "prince": 1}),
            ("Somewhere loud with six friends", {"prince": 2, "spicy-margherita": 1}),
        ]),
        ("Pick a problem with most pizza.", [
            ("Not enough heat", {"spicy-margherita": 3}),
            ("Too much going on", {"margherita": 3}),
            ("Not enough food", {"prince": 2, "detroit": 1}),
            ("Too predictable", {"bianco": 3}),
        ]),
        ("The best part of the slice is\u2026", [
            ("The crust", {"detroit": 2, "margherita": 1}),
            ("The cheese pull", {"detroit": 1, "bianco": 2}),
            ("Whatever\u2019s on top", {"prince": 2, "spicy-margherita": 1}),
            ("The char", {"margherita": 2, "spicy-margherita": 1}),
        ]),
        ("Your drink order says a lot.", [
            ("Cold lager, no thinking required", {"detroit": 2, "prince": 1}),
            ("Whatever the bartender suggests", {"bianco": 2, "margherita": 1}),
            ("A red with some backbone", {"prince": 2, "margherita": 1}),
            ("Something with a kick in it", {"spicy-margherita": 2}),
        ]),
        ("Someone suggests splitting a pizza. You\u2026", [
            ("Agree, then order your own anyway", {"prince": 2, "detroit": 1}),
            ("Suggest two and leftovers", {"detroit": 2, "prince": 1}),
            ("Happily \u2014 you want room for dessert", {"margherita": 2, "bianco": 1}),
            ("Only if they let you pick", {"spicy-margherita": 2, "bianco": 1}),
        ]),
        ("Last one. A night out should be\u2026", [
            ("Easy", {"margherita": 2, "detroit": 1}),
            ("Interesting", {"bianco": 3}),
            ("Loud", {"spicy-margherita": 2, "prince": 1}),
            ("Filling", {"prince": 3}),
        ]),
    ],
}

# Date night page. Everything here is true of our own rooms — no recommending other
# businesses, which is what makes a local guide a maintenance burden and a liability.
DATE_NIGHT = {
    "lede": "No reservation anxiety, no tasting menu, no performance. A fire, a bottle and "
            "something that came out of the oven four minutes ago.",
    "reasons": [
        ("The oven does the talking",
         "Wood-fired pies cook in minutes, so food arrives while you\u2019re still on the first drink \u2014 "
         "not forty minutes into a conversation that had started to flag."),
        ("Splitting is the point",
         "A pizza, a pasta and something fried in the middle of the table beats two plates and a silence. "
         "Order three things and share all of them."),
        ("It costs what it costs",
         "You can have a very good night here for the price of two entr\u00e9es somewhere with a tasting menu, "
         "and nobody has to pretend to be impressed."),
        ("Nobody is rushing you",
         "The kitchen runs late most nights, and longer on football days. Stay for dessert."),
    ],
    "order": [
        ("Start", "Something fried to share while you look at the rest of the menu. It buys you ten minutes "
                  "of not deciding anything."),
        ("Middle", "One round pizza between two is plenty if you\u2019ve started with an appetizer. Pick one "
                   "red and one white if you\u2019re getting two \u2014 they taste different enough to be worth it."),
        ("Drink", "Friday is half-price bottles after 5pm. Happy hour runs 2\u20136pm every day at every "
                  "location with a bar. Not sure what goes with what? "
                  "<a href=\"/pairing/\">Ask Sal</a>."),
        ("End", "Dessert, and the argument about who\u2019s paying."),
    ],
}

REGIONS = ["Greater Hartford", "Central CT", "Eastern CT", "Fairfield & New Haven", "Florida"]

# Monthly member deal. Each entry is date-gated in the browser (Eastern time,
# both ends inclusive), so next month's promo can be staged ahead of its start
# date and swaps itself in overnight. Keep them in chronological order and make
# sure the windows don't overlap — two live at once would both render.
DEALS = [
    {
        "eyebrow": "Loyalty members only",
        "headline": "$6 off when you spend $36+",
        "detail": "Monday–Friday, dine-in. One use per member. Not valid with other offers. Tax & gratuity not included.",
        "starts": "2000-01-01",
        "expires": "2026-09-30",
        "expires_label": "Ends Sept 30",
    },
    {
        "eyebrow": "Loyalty members only",
        "headline": "$8 off when you spend $38+",
        "detail": "Monday–Friday, dine-in. One use per member. Not valid with other offers. Tax & gratuity not included.",
        "starts": "2026-10-01",
        "expires": "2026-10-31",
        "expires_label": "Ends Oct 31",
    },
]
DEAL = DEALS[0]  # legacy single-deal reference

POINTS = [
    (100, "Free cookie"), (200, "$5 off"), (300, "Free appetizer", "excludes wings"),
    (350, "Any pasta dish"), (400, "Any small pizza"), (500, "Large specialty pizza"),
    (600, "$25 reward card"), (1000, "$50 reward card"),
]

APP_PERKS = ["$5 off your next order", "Exclusive in-app deals", "Flash promos", "Rewards every visit"]

SIGNATURES = [
    ("Spicy Margherita", "Cherry peppers, spicy capicola, fresh mozzarella, basil", "pie-spicy-margherita"),
    ("Margherita", "Fresh mozzarella, tomato sauce & basil. The classic, fire-kissed", "pie-margherita"),
    ("Prince of Paramus", "House pork meatballs, mushrooms, mozzarella, tomato sauce", "pie-prince-of-paramus"),
    ("Bianco", "Goat cheese, ricotta, garlic, maple & Calabrian chili oil", "pie-bianco"),
]

# Menu overview for /our-menu/ and location pages. Taken from the Toast online menus (Sept 2026).
# No prices here: Toast has the live menu and prices for each location.
MENU = {
    "pizza_styles": [
        ("Neo-Neapolitan rounds", "12″ (6 slices) or 18″ (8 slices), red or white. Wood-fired at every location except Bolton."),
        ("Detroit-style", "Thick, crispy-edged 10×14″ pan pizza (6 slices). At every location except Bolton."),
        ("Gluten-free", "12″ gluten-free crust on any round pie. Vegan cheese on any pizza."),
    ],
    "sections": [
        ("Pasta", "pasta", [
            ("Chicken Parmesan", "Breaded chicken, house-made sauce and mozzarella over pasta."),
            ("Pasta alla Vodka", "Rigatoni in a garlic tomato cream sauce with vodka and basil, finished with Calabrian chili oil."),
            ("Pasta Bolognese", "Pappardelle in a traditional beef and pork tomato cream sauce."),
            ("Shrimp Scampi", "Sautéed shrimp and spaghetti in a creamy white wine, lemon and garlic sauce."),
            ("Spaghetti & Meatballs", "Two jumbo house-made pork meatballs, marinara and parmesan."),
            ("The Bella Parmigiana", "Crispy eggplant over spaghetti with parmesan and marinara."),
        ]),
        ("Parm sandwiches & Italian subs", "sandwiches", [
            ("Chicken Parm", "Crispy chicken, marinara and mozzarella on toasted bread."),
            ("Meatball Parm", "House-made pork meatballs, marinara, mozzarella and parmesan."),
            ("Eggplant & Ham Parm", "Crispy eggplant and ham with marinara and mozzarella."),
            ("Italian Combo", "Prosciuttini, ham, spicy capicola, fresh mozzarella and red wine vinaigrette."),
            ("The Hot Honey Eggplant", "Crispy eggplant with a sweet-heat hot honey finish."),
        ]),
        ("Starters & wings", "starters", [
            ("House-made pork meatballs", "Two jumbo meatballs with pecorino romano and our sauce."),
            ("Calamari", "Plain or loaded."),
            ("Honey bruschetta", "A sweet-and-savory take on the classic."),
            ("Fried mozzarella & garlic bread", "The two starters every table fights over."),
            ("Wood-fired wings", "Sauced (BBQ, hot honey, buffalo, Carolina gold) or dry-rubbed."),
        ]),
        ("Salads", "salads", [
            ("Caesar", "Romaine, croutons, shaved pecorino, Caesar dressing."),
            ("House", "Romaine, cucumber, red onion, fennel, roasted tomatoes, parmesan, red wine vinaigrette."),
            ("Chef, market greens & more", "Add chicken, shrimp, salmon or prosciutto."),
        ]),
        ("Kids' meals", "kids", [
            ("Kids pasta, spaghetti & meatballs, pasta alla vodka", "Smaller portions of the grown-up favorites."),
            ("Chicken fingers & mac and cheese", "The reliable ones."),
        ]),
        ("Beer, wine & cocktails", "drinks", [
            ("Cocktails", "Margaritas, spritzes and house specialties, shaken to go with pizza and pasta."),
            ("Beer", "Draft and bottled beer, including local picks."),
            ("Wine", "Reds and whites by the glass or bottle."),
        ]),
        ("Desserts", "desserts", [
            ("New York-style cheesecake", "In a graham cracker crust."),
            ("Gelato sandwiches & Italian sorbet", "A cool finish after the wood-fired oven."),
            ("Fried dough, brownies & warm cookies", "Chocolate chip cookies topped with sea salt."),
        ]),
    ],
    "drinks_note": "Beer, wine and cocktails are served at every Square Peg except Bolton.",
    "note": "Menus vary a little by location and change with the seasons. Your Square Peg’s online menu always has the current items and prices.",
}

# Real reviews shown on the current squarepegpizzeria.com homepage.
REVIEWS = [
    ("I’m not a big fan of pizza, but I will tell you this pizza, I can eat a whole small one by myself. That’s how good it is. My kids absolutely love their food.", "Cliff"),
    ("The crust was exactly what I love: thin and airy but had a great bite and chew. It wasn’t greasy, and the mozzarella was tasty.", "Olga"),
    ("Best vegan cheese pizza I’ve ever had. Life changing for someone who can’t have dairy!", "Jessica"),
]

FUNDRAISER_FAQ = [
    ("Is the fundraiser dine-in only?", "Yes. Only dine-in food purchases count. Take-out, delivery and third-party apps are excluded."),
    ("How do supporters make their purchase count?", "They dine in any Tuesday from 4pm to close at the location you booked and tell their server they’re supporting your organization."),
    ("How much does our organization earn?", "20% of qualifying dine-in food sales, excluding tax and alcohol. We total everything at the end of the night and send the donation after the event."),
    ("How many organizations can book a night?", "One organization per location per Tuesday. If your date is taken, we’ll add you to our priority waiting list."),
    ("What do we get to promote it?", "A custom digital flyer and social-ready graphics made by our team. Server tracking and sales reporting are handled by us."),
]

# ---------------------------------------------------------------- Catering
# Square Peg does NOT deliver and does NOT set up. Everything is pickup, from any
# of the ten locations. Nothing on the site may imply otherwise — see
# Catering_Launch_Runbook_Fall2026.md, where the ads were rewritten for the same
# reason. The food truck is the one exception: it travels, and it is booked
# through the same form.
# The three ways a group can eat with us, and the honest basis for choosing one.
# This table is the most useful thing on any of the event pages: most people
# arrive not knowing which of the three they actually want.
EVENT_ROUTES = [
    ("Come to us", "Large party reservation",
     "Ten or more at one of our tables. We save the seats and plan the food so it "
     "lands together instead of in waves.", "/large-party-reservations/"),
    ("We cook, you collect", "Pickup catering",
     "Trays of pasta, wings, salads, sandwiches and dessert, plus pizza. Ready "
     "boxed at the time you agreed. No minimum.", "/catering/"),
    ("We come to you", "The food truck",
     "A real wood-fired oven on wheels, cooking pies in front of your guests. "
     "The only one of the three where we turn up.", "/food-truck/"),
    ("Your cause, our Tuesday", "Tuesday fundraiser",
     "Bring your group in on a Tuesday and 20% of dine-in food sales goes back "
     "to your school, team or cause.", "/fundraisers/"),
]

TRUCK = {
    "party_min": "10 or more",
    "season": "May through October",
    "events": ["Weddings and rehearsal dinners", "Graduation parties",
               "School and team events", "Corporate days and office parties",
               "Breweries, festivals and markets", "Block parties and backyard birthdays"],
    # Deliberately no radius and no minimum on the page: both are decided job by
    # job, and publishing a number we'd have to break is worse than publishing none.
    "steps": [
        ("Send the form",
         "Date, where it is, and roughly how many people. Choose Food truck "
         "private service when the form asks."),
        ("We build the menu with you",
         "The truck menu isn’t fixed. We put it together around your crowd, your "
         "timing and what you want to spend."),
        ("The oven rolls up",
         "We park, fire up and cook in front of your guests. Pies come out of the "
         "flame and onto the plate."),
    ],
    # The comparison people actually need. Both columns are true, which is the point.
    "vs": [
        ("Where the food is made", "In our kitchen", "In front of your guests"),
        ("How it arrives", "You collect it, boxed and hot", "We drive it to you"),
        ("What’s on it", "The full tray menu plus pizza", "Built around your event"),
        ("Minimum order", "None", "Depends on the job"),
        ("Best for", "Offices, parties, anything on a schedule",
         "Weddings, festivals, anywhere the food is part of the show"),
    ],
}

# Only questions we can answer honestly. Radius, minimums, deposits and weather
# are all decided job by job, so they route to the conversation rather than to a
# number we would end up breaking.
TRUCK_FAQ = [
    ("How far ahead should I book the food truck?",
     "As early as you have a date. May through October is the busy stretch and "
     "Saturdays go first — summer weekends are often spoken for months out. Off "
     "season there is usually more room, so it is always worth asking."),
    ("How far will the truck travel?",
     "It depends on the date and the job, so we would rather not publish a radius "
     "we would have to break. Send the form with where you are and when, and we "
     "will give you a straight answer."),
    ("Is there a minimum number of guests?",
     "Nothing fixed. Whether the truck makes sense for your event depends on the "
     "headcount, the date and what you want to spend, and that is the conversation "
     "we will have when we call you back."),
    ("What is on the truck menu?",
     "Whatever we build with you. It is a real wood-fired oven, so pizza is the "
     "heart of it, and we put the rest of the menu together around your crowd and "
     "your budget rather than handing you a fixed package."),
    ("Can you handle gluten-free or vegan guests?",
     "Yes. We have a 12″ gluten-free crust and vegan cheese. Tell us the numbers "
     "when we talk and we will plan for them properly rather than improvising on "
     "the day."),
    ("What do you need from us on the day?",
     "Somewhere to park and set up — a driveway, a lot or a flat piece of lawn. "
     "We go through space and access with you before the date so there are no "
     "surprises when the truck pulls in."),
    ("Can we book the truck and pickup catering together?",
     "Yes, and for bigger events it is often the right answer: the truck cooks "
     "pizza in front of your guests while trays of salad, pasta and dessert come "
     "from the kitchen. Mention both on the form."),
]

# The guest-facing half of the fundraiser program.
#
# /fundraisers/ sells the idea to the organiser: how it works, how to book a
# Tuesday. The people that organiser then emails are supporters, and they need a
# completely different page — what to do on the night, and what does and doesn't
# count. This is the URL that goes in their newsletter and on their website,
# which also makes it the page that collects the local backlinks.
#
# Rules here must stay identical to FUNDRAISER_FAQ. If one changes, change both.
FUNDRAISER_NIGHT = {
    "share": "20%",
    "window": "4pm to close",
    "steps": [
        ("Come in on their Tuesday",
         "Any time from 4pm to close, at the Square Peg your group booked. You "
         "don’t need a ticket, a flyer or a reservation."),
        ("Eat in the restaurant",
         "Dine-in only. Takeout, delivery and the third-party apps don’t count "
         "towards the total — this is the one that trips people up."),
        ("Tell your server who you’re with",
         "Say the group’s name when you order. That’s how your table gets counted."),
    ],
    "counts": ["Food, eaten in the restaurant",
               "Any Tuesday booking, 4pm to close",
               "Any size table — two people or twenty"],
    "excluded": ["Takeout and curbside",
                 "Delivery and third-party apps",
                 "Alcohol",
                 "Tax and tip"],
    "faq": [
        ("Do I need a flyer or a code?",
         "No. Just tell your server which group you’re supporting when you order."),
        ("Does takeout count?",
         "No. Only food eaten in the restaurant counts, which is why it matters that "
         "everyone comes in rather than ordering ahead for pickup."),
        ("What time should we come?",
         "Any time from 4pm to close on the Tuesday the group booked. Earlier is "
         "usually quieter if you’re bringing small children."),
        ("Does my drink count?",
         "Soft drinks are food sales and count. Alcohol doesn’t, and neither does "
         "tax or tip."),
        ("How much goes to the group?",
         "20% of qualifying dine-in food sales across the whole night. We total it "
         "up after close and send the donation to the organisation."),
        ("Can I come if I’m not part of the group?",
         "Yes, and please do. Anyone who dines in that night and mentions the group "
         "adds to their total."),
    ],
}

CATERING = {
    # ⚠ CONFIRM BEFORE PUSHING. Worked from the real tray prices on the catering
    # sheet, not guessed: a full tray feeds 40–50, so pasta ($151) + salad ($116)
    # + wings ($151) + cookies ($203) is $621, i.e. $12.42–15.53 a head. Swap the
    # pasta for chicken parm and it is $13.64–17.05. A lighter spread — pasta,
    # salad, garlic bread — comes in at $7.20–9.00.
    "per_head": "$12–18",
    "per_head_note": "That is a full spread — a pasta, a salad, wings and dessert. "
                     "Keep it lighter and it lands nearer $8.",
    "lead_time": "48 hours",
    "tray_half": "20–25",
    "tray_full": "40–50",
    "steps": [
        ("Send the form",
         "Date, headcount, which Square Peg, and anything we should know — allergies, "
         "a vegetarian table, a crowd of teenagers."),
        ("Our catering manager calls you",
         "One person, for all ten locations. They go through the menu with you, size "
         "the trays to your headcount and send an estimate."),
        ("Pick it up hot",
         "Boxed and waiting at the time you agreed, at the location you chose. "
         "Nothing to set up, nothing to send back."),
    ],
    # His own sheet: HALF TRAY serves 20–25, FULL TRAY serves 40–50.
    "feeds": [
        ("20–25", "Half trays", "Two or three dishes plus a dessert covers it"),
        ("40–50", "Full trays", "Same spread, one size up"),
        ("75–100", "Two full trays of each", "Worth a call — this one we plan properly"),
    ],
    "menu": [
        ("Starters", "Bone-in wings and boneless tenders in six flavours, cheesy garlic "
                     "bread, fried mozzarella, house-made pork meatballs, shrimp cocktail."),
        ("Salads", "House, Caesar, chef, market greens, and the Beet Dropper with goat "
                   "cheese, pistachios and crispy prosciutto."),
        ("Pastas", "Pasta alla vodka, spaghetti & marinara, Bolognese, shrimp scampi, "
                   "macaroni & cheese."),
        ("Add a protein", "Chicken parm, eggplant parm, roasted or fried chicken, "
                          "meatballs, salmon, shrimp — on top of any pasta tray."),
        ("Sandwich platters", "Ten or twenty on toasted rolls, up to four kinds: chicken "
                              "parm, Italian combo, meatball parm, turkey, BLT, hot honey "
                              "eggplant and more."),
        ("Desserts", "Cookie platters, fudge brownies, New York cheesecake, and fried "
                     "dough bites with Nutella."),
        ("Pizza", "Added from the regular menu. One 18″ round feeds about three and a "
                  "half adults, so a crowd of 50 is around fourteen pies."),
    ],
    "wing_flavors": "BBQ · Hot Honey · Buffalo · Peg Seasoning (garlic parm) · "
                    "Sweet & Smoky Dry Rub · Carolina Gold Mustard",
    "truck": "The food truck is the one thing that does come to you. Same form, "
             "choose Food truck as the event type.",
}

CATERING_FAQ = [
    ("How far ahead should I book catering?", "The earlier the better, especially October through December. Send the form with your date and headcount and we’ll confirm availability."),
    ("Can you cater at every location?", "Yes. Catering is available from all Square Peg locations. Choose the one closest to you, and your order will be ready for pickup there."),
    ("Do you have gluten-free or dairy-free options?", "Yes. We offer a 12″ gluten-free crust and vegan cheese. Tell us in the notes and we’ll plan for it."),
    ("Can the food truck come to our event?", "Yes. Book the Square Peg food truck for parties, schools, corporate events and fundraisers using the same form. Choose “Food truck” as the event type."),
    ("Do you deliver catering?", "No. Every catering order is pickup, from the Square Peg you choose. We’d rather tell you that up front than promise a van and a chafing dish we don’t have. If you need us on site, book the food truck instead — that one really does come to you."),
    ("Is there a minimum order?", "No minimum and no headcount floor. Ten people or a hundred, we’ll size it with you."),
    ("What’s the largest order you can do?", "There’s no hard ceiling with enough notice. Tell us the date and the number and we’ll tell you straight away whether that kitchen can take it on that day."),
    ("How many pizzas do I need?", "About one 18″ pie for every three and a half adults, which is where the table on this page comes from. If it’s a teenage or game-day crowd, work on two and a half. Our pizza calculator will do the arithmetic for you."),
    ("What does catering cost?", "Most orders land somewhere around $12–18 a head once you add wings, salad and dessert; pizza on its own is closer to $7. Your estimate comes from our catering manager after you send the form, so you see a real number before you commit to anything."),
    ("How do I pay?", "Our catering manager goes through it with you when they send the estimate."),
    ("Can I change the headcount after I book?", "Yes, within reason and with notice. Numbers move — tell us as soon as you know and we’ll adjust the order."),
]

SMS_TERMS = [
    ("Program", "Square Peg Pizzeria offers a recurring SMS messaging program to keep you informed about exclusive promotions and deals, upcoming events and entertainment, order confirmations, and loyalty and rewards updates."),
    ("Program name", "Square Peg Pizzeria SMS Alerts."),
    ("Message frequency", "Message frequency varies. You may receive up to 8 messages per month depending on your activity and location."),
    ("Message and data rates", "Message and data rates may apply. Check with your mobile carrier for details on your messaging plan."),
    ("How to opt out", "You may opt out of our SMS program at any time. Reply STOP, CANCEL, END, QUIT, or UNSUBSCRIBE to any message from us. You will receive one final confirmation message confirming your opt-out. No further messages will be sent after that."),
    ("How to get help", "Reply HELP to any message for assistance. You may also contact us directly at info@squarepegpizzeria.com or (860) 286-0415."),
    ("Supported carriers", "Available on all major US carriers. Carrier availability may vary."),
    ("Consent is not required for purchase", "Opting into our SMS program is never required to make a purchase, use our services, or participate in our rewards program."),
    ("Data sharing", "No mobile information will be shared with third parties or affiliates for marketing or promotional purposes. All categories exclude text messaging originator opt-in data and consent. This information will not be shared with any third party."),
    ("Privacy", "For full details on how we handle your personal information, see our Privacy Policy at squarepegpizzeria.com/privacy/."),
]

DICE = {
    "headline": "Roll doubles. Win pizza.",
    "when": "Monday–Thursday, until 4:00 PM, at every Square Peg",
    "how": [
        ("Order any full-price appetizer", "Monday through Thursday, before 4pm."),
        ("Roll two dice at your table", "Your server brings the dice. You roll."),
        ("Match them and win", "Any double wins a free small cheese pizza, right then. Double sixes win a $20 gift card for your next visit."),
    ],
    "odds": "Your odds of rolling a double are one in six.",
    "terms": "One roll per guest, per visit, with the purchase of any full-price appetizer. Free small cheese pizza is one per loyalty member and must be redeemed on the same visit; not transferable, no substitutions. Gift card is issued on the spot for use on a future visit. Valid Monday–Thursday until 4:00 PM at participating Square Peg Pizzeria locations. Not valid with any other offer, discount, or loyalty reward. House dice only; a team member must witness the roll. Employees and immediate family are not eligible. Management may end the promotion at any time.",
}

# ---------------------------------------------------------------------------
# Embedded forms from Square Peg Connect (connect.squarepegpizzeria.com).
# Once Connect has the embed snippet (CONNECT_EMBED_SNIPPET.html), each form reports its own
# height and resizes itself on every step, with no logo and no extra white space.
# Until then: "crop" hides Connect's logo header, and "mobile"/"desktop" are fixed frame
# heights (px) that fit the tallest step.
EMBEDS = {
    "catering": {"src": "https://connect.squarepegpizzeria.com/public/catering",
                 "title": "Square Peg catering request form", "crop": 196, "mobile": 1230, "desktop": 1210},
    "large_party": {"src": "https://connect.squarepegpizzeria.com/public/large-reservations",
                    "title": "Square Peg large reservation request form", "crop": 196, "mobile": 680, "desktop": 660},
    "fundraiser": {"src": "https://connect.squarepegpizzeria.com/public/fundraisers",
                   "title": "Square Peg Tuesday fundraiser request form", "crop": 196, "mobile": 680, "desktop": 660},
}
EMBEDS["food_truck"] = EMBEDS["catering"]

LARGE_PARTY_FAQ = [
    ("What counts as a large party?", "Ten or more. At that point tables have to be moved and the kitchen wants a heads-up, so send a request rather than turning up and hoping. Birthdays, team dinners, showers, reunions, office parties — we’ll confirm what works for your group size and date."),
    ("Do all locations take large party reservations?", "Yes. Space is different at every Square Peg, so we’ll confirm the best setup for your group at the location you choose."),
    ("Can we plan the food ahead of time?", "Yes. Tell us what you have in mind in your request and we’ll plan it with you, so everything hits the table hot and together."),
    ("Do you have gluten-free or dairy-free options?", "Yes. We offer a 12″ gluten-free crust and vegan cheese. Mention any dietary needs in your request."),
    ("How far ahead should we book?", "As early as you can, especially for Friday and Saturday nights and during the holidays."),
    ("Would a fundraiser work better for our group?", "If you’re raising money for a school, team or nonprofit, a Tuesday Night Fundraiser earns 20% of dine-in food sales for your cause."),
]

CONTACT_TOPICS = [
    "General question", "Feedback about a visit", "Catering", "Large party reservation", "Food truck",
    "Fundraiser", "Gift cards", "Rewards / app help", "Jobs", "Media or partnership",
]

# ---------------------------------------------------------------------------
# Weekly entertainment (from squarepegpizzeria.com/entertainment). Day, event, time.
ENTERTAINMENT = {
    "plainville-ct": [("Mon", "Bingo", "6–8pm"), ("Wed", "Trivia", "6:30–8:30pm"), ("Fri", "DJ", "7–10pm")],
    "shelton-ct": [("Tue", "Bingo", "6–8pm")],
    # A 4th value is an optional start date: the event shows with a "from <date>" badge until
    # then, and the badge disappears on its own once the date passes (no rebuild needed).
    # Tidy up by deleting the 4th value whenever you're next in here.
    "vernon-ct": [("Wed", "Trivia", "6:30–8:30pm"), ("Sat", "Bingo", "6–8pm", "2026-09-26")],
    "east-hartford-ct": [("Thu", "Bingo", "6:30–8:30pm"), ("Sat", "Bingo", "6:30–8:30pm")],
    "glastonbury-ct": [("Wed", "What Trivia", "6:30–9pm")],
    "preston-ct": [("Thu", "Trivia", "7–9pm"), ("Sun", "Bingo", "6pm")],
    "storrs-ct": [("Wed", "Trivia", "6:30–8:30pm"), ("Fri", "DJ", "10pm–close"), ("Sat", "DJ", "10pm–close")],
    "delray-beach-fl": [("Sun", "Jackpot Bingo", "4–6pm"), ("Mon", "Bingo", "6:30–8:30pm"), ("Wed", "Trivia", "7–9pm")],
}

# Ongoing promotions (from squarepegpizzeria.com/promotions).
PROMOS = {
    "daily": [
        ("Tuesday", "Pasta Night", "$15", "After 5pm. Carb up, wind down."),
        ("Wednesday", "Wing Night", "$1 per wing", "After 5pm. You bring the appetite, we bring the heat."),
        ("Friday", "Wine Night", "½-price bottles", "After 5pm. Because you survived the week."),
    ],
    "lunch": [
        ("2 slices + drink", "Cheese or pepperoni."),
        ("1 slice + salad + drink", "Cheese or pepperoni, with a fresh salad."),
    ],
    "lunch_note": "$10 each. Monday–Friday, 11am–2pm where open, dine-in.",
    # Happy hour runs at every location with a bar (Bolton has none yet, so it's
    # gated on the location's "bar" flag). Deals aren't published yet — when they
    # are, add them as a list here and they'll render under the times.
    "happy_hour": {"days": "Every day", "time": "2–6pm", "deals": []},
    "app": [
        ("Refer a friend, get $10", "Invite a friend through the Square Peg app. When they join, a $10 reward lands in your app wallet. Limit one referral reward per month."),
        ("Rewards Club: $10 a month", "Pay $10 a month and get $20 in Square Peg credit, loaded automatically. Sign up in the app. Monthly credits expire in 30 days."),
        ("Load money, get rewarded", "Load $20, get $22. Load $50, get $55. Load $100, get $110. Bonus credit to use in the restaurant."),
    ],
    "punch": [
        ("Buy 6 pizzas, get a free large pizza", "Lunchtime only, until 3pm"),
        ("Buy 6 sandwiches, get the 7th free", "Lunchtime only, until 3pm"),
        ("Buy 6 desserts, get the 7th free", "Anytime"),
    ],
    "app_perks": ["$5 welcome reward", "App-only flash sales (lunch, dinner & more)", "Lunch specials & hero discounts", "Surprise drops & birthday perks"],
    "heroes": "Active duty service members, veterans and first responders (police, firefighters, EMTs) get 15% off their meal. Just show a valid military, veteran or first responder ID. You serve the community. Let us serve you.",
}

# ---------------------------------------------------------------- GAME DAY (football season)
# The page lives at /game-day/ all year, but the nav link, home banner and the specials
# themselves only show between these dates. The window is checked in the browser, so the page
# turns itself on and off without a rebuild. Next season: move both dates forward.
GAME_DAY = {
    "season_from": "2026-09-01",
    "season_to": "2027-02-15",          # a week after the Super Bowl
    "season_label": "2026–27 football season",
    "tagline": "Come for the game. Stay for the pizza.",
    # Headline deals, shown as a band. These run during games only.
    "band": [
        ("$4", "Green Tea shots", "During football games", "band-shot"),
        ("$7", "Game day cocktails", "During football games", "band-cocktail"),
        ("$4", "Miller Lite", "During football games", "band-miller"),
    ],
    "cocktails_price": "$7 each",
    "cocktails": [
        ("The Blitz", "Transfusion", ["Vodka", "Grape juice", "Fresh lime", "Ginger ale"], "Cherry garnish"),
        ("The Hail Mary", "Dark 'n' Stormy", ["Captain spiced rum", "Fresh lime", "Ginger beer"], "Lime garnish"),
        ("Sack Attack", "Blue margarita", ["Tequila", "Triple sec", "Fresh lime juice", "Blue curaçao"], "Lime garnish"),
        ("Touchdown Tea", "John Daly", ["Vodka", "Iced tea", "Lemonade"], "Lemon garnish"),
    ],
    "mocktails_price": "$5 each",
    "mocktails": [
        ("The Extra Point", "", ["Orange juice", "Pineapple juice", "Fresh lemon juice", "Club soda", "Grenadine"], "Cherry garnish"),
        ("The Rookie", "", ["Orange juice", "Cranberry", "Pineapple juice", "Sprite"], "Lime garnish"),
    ],
    # NFL Sunday Ticket for Business, via EverPass. Add "sunday_ticket": True to a location
    # in LOCATIONS as each store's equipment goes in.
    "sunday_ticket_note": "More Square Pegs will have the Sunday Ticket soon.",
    "pizza_price": "$15 small · $26 large",
    "pizzas": [
        ("The White Out", "gd-white-out", "Chicken bacon ranch",
         ["Parm cream", "Mozzarella", "Chicken", "Bacon", "Ranch drizzle", "Green onions"]),
        ("The Red Zone", "gd-red-zone", "Loaded red",
         ["Red sauce", "Mozzarella", "Pepperoni", "Sausage", "Roasted red peppers", "Ricotta"]),
    ],
}

# ---------------------------------------------------------------------------
# Ticketed events at a single location (paint nights, tastings, fundraisers).
#
# Keyed by location slug. Each event shows on that location's page from
# `announce` until the end of `date` (Eastern time), then hides itself — no
# rebuild, no one having to remember to take it down. Delete the entry
# whenever you're next in here.
#
#   date     ISO date of the event. Also the last day the block shows.
#   announce ISO date the block starts showing. Omit to show immediately.
#   meta     Short facts shown as a row: time, price, what's included.
#   url      Where tickets are sold. cta is the button label.
#   host     Optional credit for an outside host/partner.
# ---------------------------------------------------------------------------
EVENTS = {
    "shelton-ct": [
        {
            "title": "Charcuterie Board Paint & Sip",
            "date": "2026-10-21",
            "announce": "2026-09-24",
            "blurb": "Pick a design, paint your own wooden serving board, and take it home the "
                     "same night. Multiple designs to choose from and every material you need is "
                     "on the table — just bring yourself.",
            "meta": ["6:30 PM", "$35 per person", "Drink included", "Multiple designs"],
            "url": "https://paintsquarepeg.eventbrite.com",
            "cta": "Get tickets",
            "host": "Hosted with Paint Bar CT (@paintbarct)",
        },
    ],
}

# ---------------------------------------------------------------------------
# One-off entertainment on specific dates (a guest host, a holiday night).
#
# Unlike ENTERTAINMENT above, these don't recur — each is a single date and
# each card hides itself in the browser the day after it happens, so a passed
# date never sits on the page. Keyed by location slug.
#
#   (ISO date, what it is, time)
# ---------------------------------------------------------------------------
ENT_DATES = {
    "delray-beach-fl": [
        ("2026-10-03", "Karaoke with Trish", "6–10pm"),
        ("2026-10-16", "Karaoke with Trish", "6–10pm"),
        ("2026-10-30", "Karaoke with Trish", "6–10pm"),
    ],
}

# ---------------------------------------------------------------------------
# Limited-time offer menu — the monthly specials page at /monthly-specials/.
#
# The URL never changes, so every QR code, link and post keeps working. Each
# month: swap `month`, `ends`, the blurb and the items, drop the new photos in
# assets/img-src as lto-<slug>.webp, and rebuild.
#
# `ends` is the last day the menu shows. After that the page swaps itself to a
# short "next month is coming" message (checked in the browser, Eastern time),
# so a stale menu never sits there if the update runs late.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------- happy hour
# Keyed by location slug, so each Peg publishes its own menu as it's finalised.
# A location with no entry here falls back to the "ask your bartender" strip.
#
#   hours   — (days, time) rows for the badge
#   starts  — ISO date this menu goes live. A "starts <date>" flag shows on the
#             page up to the day before, then disappears on its own. Drop the key
#             once the menu has been running a while.
#   groups  — (heading, blurb, [(item, price, detail)]) under "drinks" and "food"
HAPPY_HOUR = {
    "delray-beach-fl": {
        "tagline": "Why limit happy to an hour?",
        "hours": [("Every day", "2–6pm"), ("Fri & Sat", "8:30pm–close")],
        "note": "Dine-in only.",
        "starts": "2026-10-05",
        "local": ["Funky Buddha Hop Gun IPA", "3 Sons Citrus Machine (hazy)", "3 Sons Lite Crispy Bois"],
        "drinks": [
            ("Our signatures", "The ones everybody orders twice.", [
                ("Fruitful Peg-arita", "$9", "Classic + your pick: strawberry, watermelon, blueberry, dragon fruit, passion fruit or coconut", "Fan fave"),
                ("Classic Peg-arita", "$7", "Tequila, triple sec, lemon, lime & agave", None),
                ("Cold Brew Martini", "$9", "Cold brew, vodka & Kahlúa. Add Baileys +$2", None),
            ]),
            ("Well drinks", "", [
                ("Well drinks", "$4", "Vodka · gin · rum · tequila · bourbon", None),
                ("Treat yourself", "+$2", "Tito’s, Smirnoff, Tanqueray, Hendrick’s, Captain Morgan, Casamigos, Maker’s Mark, Woodford Reserve", None),
            ]),
            ("Beer & wine", "", [
                ("Draft beer", "$4", "Miller Lite, Michelob Ultra, Peroni or 3 Sons Lite Crispy Bois", None),
                ("Draft pitcher", "$16", "Miller Lite, Michelob Ultra, Peroni or 3 Sons Lite Crispy Bois", None),
                ("Domestic bottles", "$4", "Budweiser, Coors Light, Michelob Ultra or Yuengling", None),
                ("Local IPA on tap", "$7", "Funky Buddha Hop Gun or 3 Sons Citrus Machine (hazy)", "Local"),
                ("House wine", "$6 / $9", "6oz or 9oz. Cabernet, Malbec, Pinot Noir, Pinot Grigio, Sauvignon Blanc or Chardonnay", None),
            ]),
        ],
        "food": [
            ("Wings", "Six wings, one flavor, zero regrets.", [
                ("6 wings", "$11", "Pick a flavor: BBQ, Hot Honey, Buffalo, Carolina Gold Mustard, or Peg Seasoning or Sweet & Smokey dry rub. Bleu cheese or ranch on the side.", None),
            ]),
            ("Starters & sides", "", [
                ("Loaded chips", "$8", "House-made chips with cheese, bacon & chives", None),
                ("Cheesy dough bites", "$7", "Warm, cheesy bites + house marinara for dipping", None),
                ("Fried mozzarella", "$8", "2 pieces, breaded & fried + house marinara for dipping", None),
                ("Pork meatball", "$8", "One giant house-made meatball, Pecorino Romano + house marinara", None),
                ("Pretzel", "$11", "Extra-large knot + queso or Carolina Gold mustard BBQ", None),
                ("Side salad", "$5", "Choice of House or Caesar, with house-made dressing", None),
            ]),
            ("Small pizza", "Our classic pies, sized for one. Gluten-free crust +$6.", [
                ("Small cheese pizza", "$8", "House-made red sauce, mozz + a sprinkle of Parm", None),
                ("Small 1-topping pizza", "$10", "The cheese pizza + your favorite topping", None),
            ]),
        ],
    },
}

# ---------------------------------------------------------------- Halloween
# Peg or Treat: the Monday of Halloween week through Halloween itself. In 2026
# Halloween is a Saturday, so the $5 kids menu is what earns the weeknights and
# Saturday mostly fills itself.
#
# The page reads these three dates and shows one of three states on its own:
#   before "starts"      -> counting down
#   starts .. ends       -> running now
#   after "ends"         -> wrapped, winners coming
# Nothing to switch on or off by hand.
HALLOWEEN = {
    "name": "Peg or Treat",
    "year": 2026,
    "starts": "2026-10-26",
    "ends": "2026-10-31",
    "when": "Monday, October 26 – Saturday, October 31",
    "hashtag": "#PegOrTreat",
    "lede": "Six days of it. Come in costume, eat something, and get your picture "
            "taken in front of a wall of cheese pizza.",

    "prize": "$25 gift card",
    "prize_extra": "and your photo on our social media",
    "winners": "One winner at every Square Peg.",
    "judged": "Best costume, picked by the crew at your location after Halloween.",

    # Two ways in, so the families who will never post still get to enter.
    "enter": [
        ("Take the photo", "Get in front of the pizza wall, in costume. Any Square Peg, "
                           "any day of the week. Ask us and we’ll take it for you."),
        ("Post it and tag us", "Put it on Instagram or Facebook with #PegOrTreat and tag "
                               "your Square Peg. Tagged posts are what we judge from."),
        ("That’s it", "We pick a best costume at each location once Halloween’s done, "
                      "and get in touch to hand over the card."),
    ],

    # Every item is $5 on its own — the groups are how it reads on the board, not a
    # three-course set. A kid can order any of them.
    "kids": {
        "price": "$5",
        "line": "Kids eat for $5 all six days.",
        "note": "Every item below is $5 each — order any of them.",
        "menu": [
            ("Pizza", ["Two slices — cheese or pepperoni"]),
            ("Pasta, kid size", ["Mac and cheese", "Spaghetti with marinara",
                                 "Pasta alla vodka"]),
            ("Dessert", ["Fried dough with Nutella"]),
        ],
    },
    # Renames of drinks already on the menu, so the bar learns nothing new and the
    # kitchen orders nothing extra — only the name on the board changes.
    # CONFIRM WITH THE BAR before this goes live.
    "drinks": {
        "note": "Same drinks you already like, wearing a costume for the week.",
        "adults_price": "$9",
        "adults": [
            ("Vampire’s Kiss", "The Fruitful Peg-arita, made with strawberry."),
            ("Witch’s Brew", "The Fruitful Peg-arita, made with blueberry."),
            ("Zombie Cold Brew", "Our Cold Brew Martini. Cold brew, vodka and Kahlúa."),
            ("Jack-o’-Lantern Martini", "October’s Pumpkin Spice Martini."),
        ],
        # Nothing is added to either of these — same pour, different name on the
        # board, so no store has to stock or mix anything for the week.
        "kids": [
            ("Ghost Juice", "Square Peg Lemonade."),
            ("Monster Mash", "Any fountain soda. Mix them up!"),
        ],
    },

    "rules": [
        "Open to anyone who comes in during Peg or Treat week, October 26–31, 2026.",
        "To be considered you have to post your photo and tag us — we judge from "
        "tagged posts on Instagram and Facebook. A photo we take for you still has "
        "to be posted and tagged by you.",
        "One winner per Square Peg location. Best costume, judged by our crew — "
        "it isn’t a random drawing.",
        "Entering means you’re OK with us sharing your photo on our screens, our "
        "social accounts and this website. For anyone under 18, a parent or "
        "guardian needs to be the one entering.",
        "Winners are contacted after October 31. Prize is a $25 Square Peg gift card, "
        "no cash value, plus your photo on our social accounts.",
        "Not sponsored, endorsed or administered by Instagram or Facebook.",
    ],
}

LTO = {
    "month": "October",
    "year": "2026",
    "ends": "2026-10-31",
    "blurb": "Five things our kitchen only makes in October, plus two cocktails that taste "
             "like the season. Here until the 31st, then they're gone.",
    "sections": [
        ("Starter", [
            ("Fried Eggplant", "$12", "lto-eggplant",
             "Golden fried eggplant dusted in our Peg seasonings dry rub, with marinara for dipping."),
        ]),
        ("Sandwich", [
            ("Burrata Bliss", "$16", "lto-burrata",
             "Toasted garlic bread, fig jam, arugula and melted burrata. Our Italian take on a better grilled cheese."),
        ]),
        ("Signature brick oven pizza", [
            ("I Yuv You", "$18 small · $28 large", "lto-i-yuv-you",
             "The pizza our head chef makes for his own family. Red pie with mozzarella, pepperoni, "
             "fried eggplant, sliced roma tomatoes, red onions and parm."),
            ("The Bianca Bella", "$17 small · $27 large", "lto-bianca-bella",
             "A white pizza with mozzarella, parm cream, sausage, caramelized onions and fresh basil. "
             "Lives up to its name."),
        ]),
        ("Dessert", [
            ("Deep Fried Sandwich Cookies", "$12", "lto-cookies",
             "Five deep fried sandwich cookies, powdered sugar, chocolate sauce and a scoop of vanilla ice cream."),
        ]),
    ],
    # No photos for these — they render as copy-only cards.
    "cocktails": [
        ("Pumpkin Spice Martini", "$9",
         "Vanilla vodka, Kahlúa, Baileys, RumChata, pumpkin spice and cold brew, chilled, with whipped cream and caramel drizzle."),
        ("Fall Sangria", "$9",
         "Gooseneck Pinot Grigio, pear liqueur and apple cider in a salted caramel and cinnamon sugar rimmed glass."),
    ],
}
