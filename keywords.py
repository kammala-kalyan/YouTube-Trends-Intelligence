# Anchor: included in every Google Trends batch so batches can be normalized.
# "cricket" scores ~20 next to typical keywords (YouTube Search, India, 12 months),
# so it doesn't squash smaller terms to 0. Keep it OUT of KEYWORDS below.
ANCHOR = "cricket"

# (keyword, language) - language is used as relevanceLanguage for YouTube search.
# Built from the starter list plus the top tags in the 2026-11-05 trending snapshot.
KEYWORDS = {
    "Tech": [
        ("iPhone", "en"), ("AI tools", "en"), ("ChatGPT", "en"), ("Android", "en"),
        ("laptop", "en"), ("Samsung", "en"), ("unboxing", "en"), ("मोबाइल रिव्यू", "hi"),
    ],
    "Finance": [
        ("SIP", "en"), ("share market", "en"), ("mutual funds", "en"), ("credit card", "en"),
        ("UPI", "en"), ("income tax", "en"), ("gold rate", "en"), ("शेयर बाजार", "hi"),
        ("ஷேர் மார்க்கெட்", "ta"), ("शेअर मार्केट", "mr"),
    ],
    "Education": [
        ("UPSC", "en"), ("JEE", "en"), ("NEET", "en"), ("coding", "en"), ("Excel", "en"),
        ("SSC CGL", "en"), ("English speaking", "en"), ("सामान्य ज्ञान", "hi"),
        ("பொது அறிவு", "ta"),
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
        ("bhajan", "hi"), ("ਪੰਜਾਬੀ ਗੀਤ", "pa"), ("বাংলা গান", "bn"), ("ಕನ್ನಡ ಹಾಡುಗಳು", "kn"),
        ("मराठी गाणी", "mr"),
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
    ],
    "Business & Startups": [
        ("business ideas", "en"), ("startup", "en"), ("Shark Tank India", "en"),
        ("digital marketing", "en"), ("make money online", "en"), ("बिजनेस आइडिया", "hi"),
    ],
    "Beauty & Lifestyle": [
        ("makeup", "en"), ("skincare", "en"), ("saree", "en"), ("mehndi design", "en"),
        ("hairstyle", "en"), ("family vlog", "en"), ("मेहंदी डिजाइन", "hi"), ("মেকআপ", "bn"),
    ],
}


def all_keywords():
    """Flat list of (category, keyword, lang)."""
    return [(cat, kw, lang) for cat, items in KEYWORDS.items() for kw, lang in items]


_kws = [kw for _, kw, _ in all_keywords()]
assert len(_kws) == len(set(_kws)), "duplicate keyword in KEYWORDS"
assert ANCHOR not in _kws, "ANCHOR must not be in KEYWORDS"
