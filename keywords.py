# Anchor: included in every Google Trends batch so batches can be normalized.
# "cricket" scores ~20 next to typical keywords (YouTube Search, India, 12 months),
# so it doesn't squash smaller terms to 0. Keep it OUT of KEYWORDS below.
ANCHOR = "cricket"

# Two-step (chained) reference for small keywords (decision Q40). Google Trends scores each batch
# 0-100 against its biggest term, so small regional keywords round to 0 next to cricket.
# Level 0 keywords are measured with cricket, level 1 with "Excel" (~20% of cricket),
# level 2 with "bike review" (~5% of Excel). Each reference is itself a tracked keyword
# measured one level up, so every level converts back to the cricket scale.
# References must be searched all over India (bike review: 35 of 36 states), because state-level
# results are chained through them too: a regional reference (e.g. "share market Tamil", tried
# first) leaves every state outside its region blank.
# fetch_trends.py moves a keyword down a level automatically when it comes back (almost) all zero.
ANCHOR_CHAIN = [ANCHOR, "Excel", "bike review"]

# Tier 2 niche groups (decision Q33): kept unless they slow the pipeline down.
# Set to False to drop all of them at once (history already collected is kept).
INCLUDE_TIER2 = True

# (keyword, language) - language is used as relevanceLanguage for YouTube search and
# becomes the keyword's "Language" in the dashboard.
# Regional keywords use the "topic + language" pattern (e.g. "UPSC Telugu"), because that's
# how most Indians search (decision Q34). Older native-script terms are kept for their history.
KEYWORDS = {
    # ------------------------------------------------------------- original groups
    "Tech": [
        ("iPhone", "en"), ("AI tools", "en"), ("ChatGPT", "en"), ("Android", "en"),
        ("laptop", "en"), ("Samsung", "en"), ("unboxing", "en"), ("मोबाइल रिव्यू", "hi"),
        ("mobile review Telugu", "te"), ("mobile review Tamil", "ta"), ("mobile review Kannada", "kn"),
        ("mobile review Malayalam", "ml"), ("mobile review Bengali", "bn"), ("mobile review Marathi", "mr"),
        ("mobile review Gujarati", "gu"),
    ],
    "Finance": [
        ("SIP", "en"), ("share market", "en"), ("mutual funds", "en"), ("credit card", "en"),
        ("UPI", "en"), ("income tax", "en"), ("gold rate", "en"), ("शेयर बाजार", "hi"),
        ("ஷேர் மார்க்கெட்", "ta"), ("शेअर मार्केट", "mr"),
        ("share market Telugu", "te"), ("share market Tamil", "ta"), ("share market Kannada", "kn"),
        ("share market Malayalam", "ml"), ("share market Bengali", "bn"), ("share market Marathi", "mr"),
        ("share market Gujarati", "gu"),
    ],
    "Education": [
        ("UPSC", "en"), ("JEE", "en"), ("NEET", "en"), ("coding", "en"), ("Excel", "en"),
        ("English speaking", "en"), ("सामान्य ज्ञान", "hi"), ("பொது அறிவு", "ta"),
        ("UPSC Telugu", "te"), ("UPSC Tamil", "ta"), ("UPSC Kannada", "kn"),
        ("UPSC Malayalam", "ml"), ("UPSC Bengali", "bn"), ("UPSC Marathi", "mr"),
        ("UPSC Gujarati", "gu"),
    ],
    "Gaming": [
        ("BGMI", "en"), ("Free Fire", "en"), ("Minecraft", "en"), ("GTA 5", "en"),
        ("Roblox", "en"), ("Valorant", "en"), ("गेमिंग", "hi"), ("గేమింగ్", "te"),
    ],
    "Food": [
        ("street food", "en"), ("biryani", "en"), ("chicken recipe", "en"), ("veg recipe", "en"),
        ("cake recipe", "en"), ("रेसिपी", "hi"), ("சமையல்", "ta"), ("వంటలు", "te"),
        ("ಅಡುಗೆ", "kn"), ("রান্না", "bn"), ("പാചകം", "ml"),
    ],
    "Travel": [
        ("Goa", "en"), ("Manali", "en"), ("Kashmir", "en"), ("Ladakh", "en"),
        ("travel vlog", "en"), ("ट्रैवल व्लॉग", "hi"),
    ],
    "Music": [
        ("Bhojpuri song", "hi"), ("Punjabi song", "en"), ("Haryanvi song", "hi"), ("lofi", "en"),
        ("ਪੰਜਾਬੀ ਗੀਤ", "pa"), ("বাংলা গান", "bn"), ("ಕನ್ನಡ ಹಾಡುಗಳು", "kn"), ("मराठी गाणी", "mr"),
    ],
    "Movies": [
        ("movie review", "en"), ("trailer", "en"), ("South movie Hindi dubbed", "hi"),
        ("web series", "en"), ("தமிழ் படம்", "ta"), ("తెలుగు సినిమా", "te"),
        ("മലയാളം സിനിമ", "ml"), ("ਪੰਜਾਬੀ ਫਿਲਮ", "pa"),
    ],
    "Sports": [
        ("IPL", "en"), ("Virat Kohli", "en"), ("India vs New Zealand", "en"), ("football", "en"),
        ("WWE", "en"), ("kabaddi", "en"), ("ਕਬੱਡੀ", "pa"),
    ],
    "News": [
        ("hindi news", "hi"), ("breaking news", "en"), ("election", "en"), ("PM Modi", "en"),
        ("తెలుగు వార్తలు", "te"), ("தமிழ் செய்திகள்", "ta"), ("मराठी बातम्या", "mr"),
        ("ಕನ್ನಡ ಸುದ್ದಿ", "kn"), ("മലയാളം വാർത്ത", "ml"),
    ],
    "Health & Fitness": [
        ("workout", "en"), ("yoga", "en"), ("weight loss", "en"), ("diet plan", "en"),
        ("gym", "en"), ("घरेलू उपाय", "hi"),
        ("health tips Telugu", "te"), ("health tips Tamil", "ta"), ("health tips Kannada", "kn"),
        ("health tips Malayalam", "ml"), ("health tips Bengali", "bn"), ("health tips Marathi", "mr"),
        ("health tips Gujarati", "gu"),
    ],
    "Business & Startups": [
        ("business ideas", "en"), ("startup", "en"), ("Shark Tank India", "en"),
        ("digital marketing", "en"), ("make money online", "en"), ("बिजनेस आइडिया", "hi"),
    ],
    "Beauty & Lifestyle": [
        ("makeup", "en"), ("skincare", "en"), ("saree", "en"), ("mehndi design", "en"),
        ("hairstyle", "en"), ("मेहंदी डिजाइन", "hi"), ("মেকআপ", "bn"),
    ],
    # ------------------------------------------------------------- Tier 1 niches (added 6 Nov 2026)
    "Devotional & Spiritual": [
        ("bhajan", "hi"), ("devotional songs", "en"), ("Hanuman Chalisa", "hi"), ("bhakti", "hi"),
        ("temple vlog", "en"),
    ],
    "Comedy & Entertainment": [
        ("comedy video", "en"), ("funny video", "en"), ("prank", "en"), ("roast", "en"),
    ],
    "Kids & Family": [
        ("cartoon", "en"), ("kids songs", "en"), ("rhymes", "en"), ("moral stories", "en"),
    ],
    "Automobiles": [
        ("car review", "en"), ("bike review", "en"), ("electric scooter", "en"), ("new car launch", "en"),
    ],
    "Agriculture & Village life": [
        ("farming", "en"), ("organic farming", "en"), ("village life", "en"), ("kisan", "hi"),
    ],
    "Government jobs": [
        ("SSC CGL", "en"), ("govt jobs", "en"), ("railway exam", "en"), ("bank exam", "en"),
        ("police exam", "en"),
    ],
    "Facts & Knowledge": [
        ("amazing facts", "en"), ("science facts", "en"), ("history facts", "en"), ("mystery", "en"),
    ],
    "Motivation & Self-improvement": [
        ("motivation", "en"), ("success story", "en"), ("study motivation", "en"), ("life lessons", "en"),
    ],
}

TIER2 = {
    "Astrology": [
        ("rashifal", "hi"), ("horoscope", "en"), ("vastu", "en"), ("astrology", "en"),
    ],
    "Daily vlogs": [
        ("daily vlog", "en"), ("couple vlog", "en"), ("family vlog", "en"), ("village vlog", "en"),
    ],
    "DIY & Crafts": [
        ("DIY", "en"), ("craft ideas", "en"), ("home decor", "en"), ("drawing", "en"),
    ],
    "Pets & Animals": [
        ("dog", "en"), ("cat", "en"), ("pet care", "en"), ("animals", "en"),
    ],
    "Home & Interior": [
        ("home tour", "en"), ("interior design", "en"), ("house construction", "en"), ("kitchen design", "en"),
    ],
}

if INCLUDE_TIER2:
    KEYWORDS.update(TIER2)


def all_keywords():
    """Flat list of (category, keyword, lang)."""
    return [(cat, kw, lang) for cat, items in KEYWORDS.items() for kw, lang in items]


_kws = [kw for _, kw, _ in all_keywords()]
assert len(_kws) == len(set(_kws)), "duplicate keyword in KEYWORDS"
assert ANCHOR not in _kws, "ANCHOR must not be in KEYWORDS"
assert all(a in _kws for a in ANCHOR_CHAIN[1:]), "chain references after cricket must be tracked keywords"
