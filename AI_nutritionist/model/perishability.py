import re


PERISHABILITY_TIERS = {
    "highly_perishable": {
        "days": 2,
        "items": [
            "shrimp", "fish", "salmon", "tuna", "cod", "tilapia",
            "halibut", "trout", "swordfish", "shellfish", "scallop",
            "scallops", "oyster", "oysters", "clam", "clams",
            "mussel", "mussels", "crab", "lobster",
            "fresh basil", "fresh parsley", "fresh cilantro",
            "fresh dill", "fresh mint", "fresh chives", "fresh herbs",
            "raspberry", "raspberries", "strawberry", "strawberries",
            "blackberry", "blackberries", "blueberry", "blueberries",
        ],
    },
    "perishable": {
        "days": 5,
        "items": [
            "chicken", "turkey", "pork", "beef", "lamb", "veal",
            "bacon", "sausage", "ham",
            "ground beef", "ground turkey", "ground pork", "ground chicken",
            "milk", "buttermilk", "cream", "heavy cream", "half and half",
            "sour cream", "yogurt", "cottage cheese", "ricotta",
            "spinach", "kale", "arugula", "lettuce", "romaine",
            "mushroom", "mushrooms", "tomato", "tomatoes",
            "avocado", "cucumber", "zucchini", "asparagus",
            "eggplant", "bell pepper", "green onion", "scallion",
            "scallions", "broccoli", "cauliflower",
            "peach", "peaches", "plum", "plums", "grape", "grapes",
            "cherry", "cherries", "mango", "papaya", "pineapple",
        ],
    },
    "moderate": {
        "days": 14,
        "items": [
            "egg", "eggs", "butter", "cheese", "cheddar", "mozzarella",
            "parmesan", "feta", "swiss", "gouda", "brie", "blue cheese",
            "apple", "apples", "orange", "oranges", "lemon", "lemons",
            "lime", "limes", "grapefruit", "pear", "pears",
            "carrot", "carrots", "celery", "cabbage",
            "onion", "onions", "garlic", "shallot", "shallots", "leek",
            "potato", "potatoes", "sweet potato", "yam",
            "beet", "beets", "radish", "turnip", "parsnip",
            "squash", "pumpkin", "ginger",
        ],
    },
    "pantry_stable": {
        "days": 365,
        "items": [
            "rice", "pasta", "noodle", "noodles", "spaghetti", "macaroni",
            "flour", "sugar", "brown sugar", "powdered sugar",
            "salt", "pepper", "black pepper",
            "oil", "olive oil", "vegetable oil", "canola oil", "coconut oil",
            "sesame oil", "vinegar", "balsamic", "red wine vinegar",
            "apple cider vinegar", "soy sauce", "worcestershire",
            "honey", "maple syrup", "molasses",
            "baking soda", "baking powder", "yeast", "cornstarch",
            "bean", "beans", "black beans", "kidney beans",
            "lentil", "lentils", "chickpea", "chickpeas",
            "canned tomato", "canned tomatoes", "tomato paste",
            "tomato sauce", "broth", "stock", "chicken broth", "beef broth",
            "vegetable broth",
            "cinnamon", "paprika", "cumin", "oregano", "thyme",
            "rosemary", "bay leaf", "vanilla", "cocoa", "chili powder",
            "garlic powder", "onion powder", "nutmeg", "turmeric",
            "oats", "oatmeal", "cornmeal", "couscous", "quinoa", "barley",
        ],
    },
}


TIER_PRIORITY = {
    "highly_perishable": 0,
    "perishable": 1,
    "moderate": 2,
    "pantry_stable": 3,
}


TIER_LABELS = {
    "highly_perishable": "Use within 1-3 days",
    "perishable": "Use within a week",
    "moderate": "Lasts 1-3 weeks",
    "pantry_stable": "Pantry stable",
}


def _normalize(text):
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text).strip().lower())


def classify(ingredient):
    text = _normalize(ingredient)
    if not text:
        return None
    best_tier = None
    best_match_len = 0
    for tier, data in PERISHABILITY_TIERS.items():
        for item in data["items"]:
            if re.search(rf"\b{re.escape(item)}\b", text):
                if len(item) > best_match_len:
                    best_match_len = len(item)
                    best_tier = tier
    return best_tier


def shelf_life_days(ingredient):
    tier = classify(ingredient)
    if tier is None:
        return None
    return PERISHABILITY_TIERS[tier]["days"]


def annotate(ingredient_list):
    annotated = []
    for ing in ingredient_list or []:
        tier = classify(ing)
        annotated.append({
            "ingredient": ing,
            "tier": tier,
            "days": PERISHABILITY_TIERS[tier]["days"] if tier else None,
            "label": TIER_LABELS.get(tier) if tier else None,
            "priority": TIER_PRIORITY.get(tier, 99),
        })
    annotated.sort(key=lambda a: (a["priority"], a["ingredient"].lower() if a["ingredient"] else ""))
    return annotated


def suggest_use_first(ingredient_list, tiers=("highly_perishable", "perishable")):
    flagged = []
    for ing in ingredient_list or []:
        tier = classify(ing)
        if tier in tiers:
            flagged.append((ing, tier))
    flagged.sort(key=lambda p: TIER_PRIORITY[p[1]])
    return [ing for ing, _ in flagged]


def perishability_coverage(user_perishables, recipe_blob):
    if not user_perishables:
        return 0.0
    if not isinstance(recipe_blob, str) or not recipe_blob:
        return 0.0
    blob = recipe_blob.lower()
    matched = sum(1 for p in user_perishables if p and p.lower() in blob)
    return matched / len(user_perishables)


def perishability_match_count(user_perishables, recipe_blob):
    if not user_perishables:
        return 0
    if not isinstance(recipe_blob, str) or not recipe_blob:
        return 0
    blob = recipe_blob.lower()
    return sum(1 for p in user_perishables if p and p.lower() in blob)
