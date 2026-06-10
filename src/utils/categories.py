# src/utils/categories.py

CATEGORY_KEYWORDS = {
    "Food & Dining": [
        "zomato", "swiggy", "restaurant", "cafe", "coffee", "pizza", "burger",
        "biryani", "dhaba", "hotel", "food", "kitchen", "bakery", "chai",
        "starbucks", "mcdonald", "dominos", "kfc", "subway"
    ],
    "Groceries": [
        "bigbasket", "grofers", "blinkit", "zepto", "grocery", "vegetables",
        "supermarket", "reliance fresh", "dmart", "more", "nature basket",
        "fruits", "milk", "sabji", "kirana"
    ],
    "Transport": [
        "ola", "uber", "rapido", "metro", "bus", "train", "irctc", "redbus",
        "petrol", "fuel", "auto", "taxi", "cab", "indigo", "spicejet",
        "flight", "airways", "parking"
    ],
    "Entertainment": [
        "netflix", "amazon prime", "hotstar", "spotify", "youtube", "movie",
        "pvr", "inox", "cinema", "theatre", "concert", "bookmyshow", "gaming"
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "ajio", "nykaa", "meesho", "snapdeal",
        "shopping", "clothes", "fashion", "shoes", "accessories"
    ],
    "Healthcare": [
        "pharmacy", "hospital", "clinic", "doctor", "medicine", "apollo",
        "medplus", "1mg", "pharmeasy", "lab", "diagnostic", "health"
    ],
    "Utilities": [
        "electricity", "water", "gas", "internet", "broadband", "airtel",
        "jio", "vodafone", "bsnl", "recharge", "bill", "tata power"
    ],
    "Education": [
        "school", "college", "university", "course", "udemy", "coursera",
        "books", "fees", "tuition", "coaching", "upgrad", "unacademy"
    ],
    "Investment": [
        "zerodha", "groww", "upstox", "mutual fund", "sip", "stock",
        "insurance", "lic", "ppf", "nps", "fd", "rdrd"
    ],
    "Rent & Housing": [
        "rent", "housing", "pg", "maintenance", "society", "apartment"
    ],
}


def categorize_merchant(merchant: str, raw_text: str = "") -> str:
    """
    Categorize a transaction based on merchant name and surrounding text.
    Uses keyword matching against predefined categories.
    Returns 'Others' if no match found.
    """
    search_text = (merchant + " " + raw_text).lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in search_text:
                return category

    return "Others"
