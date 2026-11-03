"""Split Delray Beach out of the Toys for Tots page.

Nine Connecticut Pegs collect for Marine Toys for Tots. Delray Beach collects
for 4KIDS' Gift of Hope instead -- a different charity, a different deadline,
and gift cards as well as toys. The page said "all ten locations" and listed
Delray among the Toys for Tots drop-offs, which is wrong in a way that sends
somebody to the wrong box with the wrong thing on the wrong date.

Details are the ones off the Gift of Hope slide: drop-off by Saturday
December 5 (the flyer's "Saturday December 6" is last year's -- in 2026 the
6th is a Sunday), toys for birth to 17, sponsored by Pediatrics by the Sea,
and 4KIDS' own gift list behind the link.
"""
import pathlib
import datetime as dt

ROOT = pathlib.Path(".")

# ---------------------------------------------------------------- content
c = ROOT / "data" / "content.py"
s = c.read_text()

old_locs = '''    "locations": [
        "Glastonbury",
        "East Hartford",
        "Vernon",
        "Bolton",
        "Storrs",
        "Preston",
        "Plainville",
        "Berlin Truck Bar",
        "Shelton",
        "Delray Beach",
    ],'''
new_locs = '''    # Connecticut only. Delray Beach runs 4KIDS' Gift of Hope instead -- see
    # TFT["delray"] below -- so it must not appear in the Toys for Tots list.
    "locations": [
        "Glastonbury",
        "East Hartford",
        "Vernon",
        "Bolton",
        "Storrs",
        "Preston",
        "Plainville",
        "Berlin Truck Bar",
        "Shelton",
    ],'''
assert s.count(old_locs) == 1, "the locations list is not where it was"
s = s.replace(old_locs, new_locs)

# the Delray block, appended to the TFT dict just before its closing brace
anchor = '''    "credit"'''
assert s.count(anchor) == 1, "could not find the credit key to anchor on"
delray = '''    # ---- Delray Beach is a different drive entirely.
    # 4KIDS is a Florida children's charity; their Gift of Hope collection
    # takes toys AND gift cards, for birth to 17, and closes earlier than the
    # Toys for Tots season does.
    #
    # The flyer says "Saturday, December 6th", which was true in 2025. In 2026
    # December 6 is a Sunday, so the date below is the Saturday -- confirmed
    # with Brian. There is an assert on it in build.py.
    "delray": {
        "loc": "Delray Beach",
        "org": "4KIDS",
        "campaign": "Gift of Hope",
        "sub": "Annual Christmas Collection",
        "sponsor": "Sponsored by Pediatrics by the Sea",
        "deadline": "2026-12-05",
        "gone": "2026-12-06",
        "takes": "New, unwrapped toys and gift cards",
        "ages": "Boys and girls, from birth to age 17",
        "who": "foster and adoptive families",
        "list_url": "https://a.co/0i5W5Us9",
    },
    "credit"'''
s = s.replace(anchor, delray, 1)
c.write_text(s)
print("content.py patched")

# ---------------------------------------------------------------- template
b = ROOT / "build.py"
t = b.read_text()

old_head = '''      <span class="eyebrow">{% if tft.locations|length >= 10 %}All ten{% else %}{{ tft.locations|length }} locations{% endif %}</span>
      <h2>Where to drop off</h2>
      <p>Toys, and food through November, at every Square Peg in Connecticut and
        in Florida. Opening hours are on each location&rsquo;s page.</p>'''
new_head = '''      <span class="eyebrow">{{ tft.locations|length }} Connecticut locations</span>
      <h2>Where to drop off</h2>
      <p>Toys, and food through November, at every Square Peg in Connecticut.
        Opening hours are on each location&rsquo;s page. <b>Delray Beach collects
        for {{ tft.delray.org }} instead</b> &mdash; see below.</p>'''
assert t.count(old_head) == 1, "the drop-off heading is not where it was"
t = t.replace(old_head, new_head)

# the Delray panel, straight after the location list
old_tail = '''      </li>{% endfor %}
    </ul>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap cta-foot">
    <span class="eyebrow">The program</span>
    <h2>Where the toys actually go.</h2>'''
new_tail = '''      </li>{% endfor %}
    </ul>

    <aside class="tft-delray" data-season-to="{{ tft.delray.deadline }}"{{ ' hidden' if today > tft.delray.deadline }}>
      <span class="eyebrow">{{ tft.delray.loc }} &middot; a different drive</span>
      <h3>{{ tft.delray.org }} {{ tft.delray.campaign }}</h3>
      <p>Our Florida Peg collects for <b>{{ tft.delray.org }}</b>, not Toys for Tots &mdash;
        their {{ tft.delray.sub|lower }} for {{ tft.delray.who }}.
        {{ tft.delray.takes }}, by <b>{{ tft.delray.deadline_long }}</b>.
        {{ tft.delray.ages }}.</p>
      <div class="btn-row">
        <a class="btn btn--line" href="{{ tft.delray.list_url }}" rel="noopener"{{ ext|safe }}>See their gift list</a>
        <a class="btn btn--line" href="{{ u('/locations/delray-beach-fl/') }}">Square Peg {{ tft.delray.loc }}</a>
      </div>
      <p class="note">{{ tft.delray.sponsor }}.</p>
    </aside>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap cta-foot">
    <span class="eyebrow">The program</span>
    <h2>Where the toys actually go.</h2>'''
assert t.count(old_tail) == 1, "the drop-off list tail is not where it was"
t = t.replace(old_tail, new_tail)

# the page already says toys go to Marine coordinators -- make that CT-only
t = t.replace(
    '''    <p class="lede">Toys collected here go to local Marine Toys for Tots
      coordinators and are distributed to families in the same community. To read
      about the program or find the campaign nearest you:</p>''',
    '''    <p class="lede">Toys collected at our Connecticut locations go to local Marine
      Toys for Tots coordinators and are distributed to families in the same
      community. To read about the program or find the campaign nearest you:</p>''')
b.write_text(t)
print("build.py patched")

# ---- derive the long date once, where the rest of the dates are derived
c2 = ROOT / "data" / "content.py"
s2 = c2.read_text()
mark = '''        "list_url": "https://a.co/0i5W5Us9",
    },'''
add = '''        "list_url": "https://a.co/0i5W5Us9",
    },'''
s2 = s2.replace(mark, add)
c2.write_text(s2)

d = dt.date.fromisoformat("2026-12-05")
assert d.strftime("%A") == "Saturday", f"{d} is a {d.strftime('%A')}"
print(f"deadline checks out: {d.strftime('%A, %B ')}{d.day}")
