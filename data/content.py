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
        "slug": "glastonbury-ct", "name": "Glastonbury", "region": "Greater Hartford",
        "street": "1001 Hebron Ave", "city": "Glastonbury", "state": "CT", "zip": "06033",
        "phone": "(860) 286-0415", "toast": "square-peg-pizzeria",
        "lat": 41.717186, "lng": -72.574051, "geo_exact": True,  # US Census geocoder
        "hours_note": "The kitchen closes an hour before we do Wednesday through Friday.", "hours": h(*(("11:30","21:00"),("11:30","21:00"),("11:30","22:00"),("11:30","22:00"),("11:30","00:00"),("11:00","23:00"),("11:00","21:00"))),
        "tag": "Where it all started",
        "blurb": "Our first Square Peg. Glastonbury is where the wood-fired oven got lit in 2020, and it’s still where regulars come for date nights, team dinners, and the same pie they’ve ordered since day one.",
        "nearby": ["Wethersfield", "Rocky Hill", "Portland", "Hebron", "Marlborough"],
        "same_as": ["https://www.yelp.com/biz/square-peg-pizzeria-glastonbury-2"],
        "photo": "oven-pizza",
    },
    {
        "slug": "east-hartford-ct", "menu_extra": ["Breakfast on weekends from 7am: omelettes and the Pegg & Cheese", "Brunch cocktails like mimosas, Bloody Marys and Aperol spritzes"], "name": "East Hartford", "region": "Greater Hartford",
        "street": "130 Long Hill St", "city": "East Hartford", "state": "CT", "zip": "06108",
        "phone": "(860) 509-4221", "toast": "square-peg-pizzera-east-hartford",
        "lat": 41.790362, "lng": -72.594171, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("11:00","22:00"),("11:00","20:30"),("11:00","20:30"),("11:00","22:00"),("11:00","20:30"),("07:00","20:30"),("07:00","22:00"))),
        "tag": "Breakfast on weekends",
        "blurb": "East Hartford is home base: our commissary kitchen here makes the dough and sauce for every Connecticut Square Peg, fresh and never frozen. It’s also the one Peg serving breakfast, with omelettes and the Pegg & Cheese from 7am on weekends.",
        "nearby": ["Hartford", "Manchester", "South Windsor", "Wethersfield", "Glastonbury"],
        "same_as": ["https://www.yelp.com/biz/square-peg-pizzeria-east-hartford"],
        "photo": "dough",
    },
    {
        "slug": "vernon-ct", "name": "Vernon", "region": "Greater Hartford",
        "street": "226 Talcottville Rd", "city": "Vernon", "state": "CT", "zip": "06066",
        "phone": "(860) 926-0088", "toast": "square-peg-pizzeria-vernon-226-talcottville-rd",
        "lat": 41.836661, "lng": -72.491494, "geo_exact": True,  # US Census geocoder
        "hours_note": "The kitchen closes an hour before we do Wednesday through Friday.", "hours": h(*(("11:30","21:00"),("11:30","21:00"),("11:30","22:00"),("11:30","22:00"),("11:30","00:00"),("11:00","23:00"),("11:00","21:00"))),
        "tag": "Open till midnight Fridays",
        "blurb": "Right on Talcottville Road (Route 83), Vernon is the easy stop for Rockville, Ellington and Tolland: pickup on the way home, or a late one on Friday when the oven runs until midnight.",
        "nearby": ["Rockville", "Ellington", "Tolland", "Manchester", "South Windsor"],
        "photo": "margherita-board",
    },
    {
        # "bar": False = no beer/wine/cocktails yet (liquor license pending); "detroit": False = no Detroit-style pizza yet. Remove each once available.
        "slug": "bolton-ct", "bar": False, "detroit": False, "pastas": ["Chicken Parmesan", "Pasta alla Vodka", "Spaghetti & Meatballs", "The Bella Parmigiana"], "menu_extra": ["Burgers"], "name": "Bolton", "region": "Greater Hartford",
        "street": "270 West St", "city": "Bolton", "state": "CT", "zip": "06043",
        "phone": "(860) 791-7109", "toast": "square-peg-pizzeria-bolton-270-west-street",
        "lat": 41.742106, "lng": -72.436706, "geo_exact": True,  # US Census geocoder
        "hours": h(*(None,("11:00","20:00"),("11:00","21:00"),("11:00","21:00"),("11:00","21:00"),("11:00","21:00"),("11:00","20:00"))),
        "tag": "Newest Peg",
        "blurb": "Our newest home, in the space Liz and Brody made special for six years as Parkside Pizza & Ice Cream. Most of the Parkside crew stayed on, so you’ll see the same familiar faces. We’re here to add to this place, not erase it.",
        "nearby": ["Manchester", "Coventry", "Andover", "Vernon", "Hebron"],
        "photo": "pizza-boxes",
    },
    {
        "slug": "storrs-ct", "name": "Storrs", "region": "Eastern CT",
        "street": "9 Dog Ln", "city": "Storrs", "state": "CT", "zip": "06268",
        "phone": "(860) 454-6038", "toast": "squarepegwindsor",
        "lat": 41.804999, "lng": -72.243305, "geo_exact": True,  # US Census geocoder
        "hours_note": "The kitchen closes an hour or two before the bar Wednesday through Saturday.", "hours": h(*(("11:30","21:00"),("11:30","21:00"),("11:30","22:00"),("11:30","00:00"),("11:30","01:00"),("11:00","01:00"),("11:00","22:00"))),
        "tag": "Steps from UConn",
        "blurb": "Our founders are UConn alumni, so Storrs Center feels like coming home. Dog Lane is where Husky fans land after the game and alumni reunions come together, and the oven runs until 1am on Fridays and Saturdays.",
        "nearby": ["Mansfield", "Coventry", "Willington", "Ashford", "Tolland"],
        "photo": "friends-holiday",
    },
    {
        "slug": "preston-ct", "name": "Preston", "region": "Eastern CT",
        "street": "353 CT-165", "city": "Preston", "state": "CT", "zip": "06365",
        "phone": "(860) 319-0930", "toast": "square-peg-new-preston-353-connecticut-165",
        "lat": 41.528840, "lng": -71.982108, "geo_exact": True,  # exact pin from Google Maps
        "hours_note": "The kitchen closes an hour before we do on Wednesday and Thursday.", "hours": h(*(("11:30","21:00"),("11:30","21:00"),("11:30","22:00"),("11:30","22:00"),("11:30","23:00"),("11:00","23:00"),("11:00","21:00"))),
        "tag": "Southeastern CT",
        "blurb": "On Route 165, Preston brings wood-fired pies to Norwich, Ledyard and the rest of the southeast corner of the state. It’s an easy dinner stop before or after a night at the casinos.",
        "nearby": ["Norwich", "Ledyard", "Griswold", "Lisbon", "North Stonington"],
        "photo": "table-spread",
    },
    {
        "slug": "plainville-ct", "name": "Plainville", "region": "Central CT",
        "street": "400 New Britain Ave", "city": "Plainville", "state": "CT", "zip": "06062",
        "phone": "(860) 996-0363", "toast": "square-peg-plainville-400-new-britain-avenue",
        "lat": 41.671493, "lng": -72.833556, "geo_exact": True,  # US Census geocoder
        "hours_note": "The kitchen closes an hour before we do on Wednesday and Thursday.", "hours": h(*(("11:30","21:00"),("11:30","21:00"),("11:30","22:00"),("11:30","22:00"),("11:00","23:00"),("11:00","23:00"),("11:00","21:00"))),
        "tag": "Central Connecticut",
        "blurb": "Plainville is our Central CT kitchen, close to New Britain, Southington and Farmington. Drop in, pick up on the way home, or plan a party we can feed.",
        "nearby": ["New Britain", "Southington", "Farmington", "Bristol", "Berlin"],
        "same_as": ["https://www.yelp.com/biz/square-peg-pizzeria-plainville"],
        "photo": "oven-fire",
    },
    {
        "slug": "berlin-ct", "pastas": ["Chicken Parmesan", "Pasta alla Vodka", "Pasta Bolognese", "Spaghetti & Meatballs"], "menu_extra": ["Hot dogs"], "kids_menu": False, "salads": False, "parm_line": "meatball parm and Italian combo sandwiches", "name": "Berlin Truck Bar", "short": "Berlin", "region": "Central CT",
        "street": "151 Webster Square Rd", "city": "Berlin", "state": "CT", "zip": "06037",
        "phone": "(860) 505-4072", "toast": "square-peg-pizza-berlin-119-webster-square-road",
        "lat": 41.628734, "lng": -72.745911, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("16:00","21:00"),None,None,("16:00","22:00"),("12:00","23:00"),("12:00","23:00"),("11:00","19:00"))),
        "tag": "The Truck Bar",
        "blurb": "Berlin is our Truck Bar on Webster Square Road: brick-oven pizza, sandwiches, wings and a bar with an easy, hang-out feel. Come in for a weekend afternoon or a game night.",
        "nearby": ["Kensington", "New Britain", "Cromwell", "Newington", "Meriden"],
        "photo": "truck-tent",
    },
    {
        "slug": "shelton-ct", "name": "Shelton", "region": "Fairfield & New Haven",
        "street": "320 Howe Ave, Unit 6", "city": "Shelton", "state": "CT", "zip": "06484",
        "phone": "(203) 538-5044", "toast": "square-peg-shelton-310-howe-avenue-unit-6",
        "lat": 41.314898, "lng": -73.091125, "geo_exact": True,  # US Census geocoder
        "hours_note": "The kitchen closes an hour before we do Wednesday through Saturday.", "hours": h(*(("12:00","21:00"),("12:00","21:00"),("12:00","22:00"),("12:00","22:00"),("12:00","23:00"),("11:00","23:00"),("11:00","21:00"))),
        "tag": "Downtown Shelton",
        "blurb": "Our Fairfield County outpost on Howe Avenue, a short walk from the Riverwalk. Shelton brings the Square Peg oven to Derby, Stratford and the Valley.",
        "nearby": ["Derby", "Ansonia", "Stratford", "Trumbull", "Monroe"],
        "photo": "friends-sharing",
    },
    {
        "slug": "delray-beach-fl", "name": "Delray Beach", "region": "Florida",
        "street": "4957 W Atlantic Ave", "city": "Delray Beach", "state": "FL", "zip": "33445",
        "phone": "(561) 566-8828", "toast": "square-peg-delray-beach-4957-west-atlantic-avenue",
        "lat": 26.457838, "lng": -80.12169, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("11:30","21:00"),("11:30","21:00"),("11:30","21:00"),("11:30","21:00"),("11:30","22:00"),("11:00","22:00"),("11:00","21:00"))),
        "tag": "Connecticut pizza in Florida",
        "blurb": "Connecticut pizza, Florida sunshine. Delray Beach has its own kitchen making dough and sauce from scratch, the same way East Hartford does for our Connecticut Pegs. On West Atlantic Avenue, our Delray Peg feeds snowbirds who missed their Glastonbury pie and locals who are just finding out what the fuss is about.",
        "nearby": ["Boynton Beach", "Boca Raton", "Lake Worth Beach", "Highland Beach"],
        "photo": "kid-slice",
    },
]

REGIONS = ["Greater Hartford", "Central CT", "Eastern CT", "Fairfield & New Haven", "Florida"]

# Current deal — update monthly.
DEAL = {
    "eyebrow": "Loyalty members only",
    "headline": "$6 off when you spend $36+",
    "detail": "Monday–Friday, dine-in. One use per member. Not valid with other offers. Tax & gratuity not included.",
    "expires": "2026-09-30",
    "expires_label": "Ends Sept 30",
}

POINTS = [
    (100, "Free cookie"), (200, "$5 off"), (300, "Free appetizer", "excludes wings"),
    (350, "Any pasta dish"), (400, "Any small pizza"), (500, "Large specialty pizza"),
    (600, "$25 reward card"), (1000, "$50 reward card"),
]

APP_PERKS = ["$5 off your next order", "Exclusive in-app deals", "Flash promos", "Rewards every visit"]

SIGNATURES = [
    ("Spicy Margherita", "Cherry peppers, spicy capicola, fresh mozzarella, basil", "pizza-cutout"),
    ("Margherita", "Fresh mozzarella, tomato sauce & basil. The classic, fire-kissed", "margherita-board"),
    ("Prince of Paramus", "House pork meatballs, mushrooms, mozzarella, tomato sauce", "table-spread"),
    ("Bianco", "Goat cheese, ricotta, garlic, maple & Calabrian chili oil", "oven-pizza"),
]

# Menu overview for /our-menu/ and location pages. Taken from the Toast online menus (Sept 2026).
# No prices here: Toast has the live menu and prices for each location.
MENU = {
    "pizza_styles": [
        ("Neo-Neapolitan rounds", "Wood-fired, 12″ (6 slices) or 18″ (8 slices), red or white."),
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

CATERING_FAQ = [
    ("How far ahead should I book catering?", "The earlier the better, especially October through December. Send the form with your date and headcount and we’ll confirm availability."),
    ("Can you cater at every location?", "Yes. Catering is available from all Square Peg locations. Choose the one closest to you, and your order will be ready for pickup there."),
    ("Do you have gluten-free or dairy-free options?", "Yes. We offer a 12″ gluten-free crust and vegan cheese. Tell us in the notes and we’ll plan for it."),
    ("Can the food truck come to our event?", "Yes. Book the Square Peg food truck for parties, schools, corporate events and fundraisers using the same form. Choose “Food truck” as the event type."),
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
    ("What counts as a large party?", "If your group is bigger than a regular table, send a request. Birthdays, team dinners, showers, reunions, office parties: we’ll confirm what works for your group size and date."),
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
    "east-hartford-ct": [("Thu", "Bingo", "6:30–8:30pm"), ("Sat", "Bingo", "6:30–8:30pm")],
    "glastonbury-ct": [("Wed", "What Trivia", "6:30–9pm")],
    "preston-ct": [("Thu", "Trivia", "7–9pm"), ("Sun", "Bingo", "6pm")],
    "storrs-ct": [("Wed", "Trivia", "6:30–8:30pm"), ("Fri", "DJ", "10pm–1am"), ("Sat", "DJ", "10pm–1am")],
    "delray-beach-fl": [("Sun", "Jackpot Bingo", "4–6pm"), ("Mon", "Bingo", "6–8pm"), ("Wed", "Trivia", "6–8pm")],
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
        ("Half sandwich + salad + drink", "Any sandwich on the menu with a fresh salad."),
        ("Pasta + salad + drink", "Your choice from the daily pasta lineup, with a garden salad."),
    ],
    "lunch_note": "$10 each. Monday–Friday, dine-in, lunchtime only.",
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
