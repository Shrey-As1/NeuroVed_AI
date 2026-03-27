"""Daily mental-health quote utility.
Returns one quote per day, cycling through the list automatically.
"""
from datetime import date

QUOTES = [
    ("You don't have to be positive all the time. It's perfectly okay to feel sad, angry, annoyed, frustrated, scared, or anxious.", "Lori Deschene"),
    ("There is hope, even when your brain tells you there isn't.", "John Green"),
    ("Mental health… is not a destination, but a process. It's about how you drive, not where you're going.", "Noam Shpancer"),
    ("Self-care is how you take your power back.", "Lalah Delia"),
    ("You are not your illness. You have an individual story to tell. You have a name, a history, a personality.", "Julian Seifter"),
    ("Healing is not linear. Some days will be harder than others, and that is okay.", "Unknown"),
    ("Sometimes the most important thing in a whole day is the rest we take between two deep breaths.", "Etty Hillesum"),
    ("It's okay to not be okay — as long as you are not giving up.", "Karen Salmansohn"),
    ("Be gentle with yourself. You are a child of the universe, no less than the trees and the stars.", "Max Ehrmann"),
    ("You are worthy of love and belonging — even on the days you don't feel it.", "Brené Brown"),
    ("Tough times never last, but tough people do.", "Robert H. Schuller"),
    ("Even the darkest night will end and the sun will rise.", "Victor Hugo"),
    ("Your present circumstances don't determine where you can go; they merely determine where you start.", "Nido Qubein"),
    ("The strongest people are not those who show strength in front of us, but those who win battles we know nothing about.", "Unknown"),
    ("Recovery is not one and done. It is one day at a time.", "Unknown"),
    ("You are braver than you believe, stronger than you seem, and smarter than you think.", "A.A. Milne"),
    ("Asking for help is the bravest thing you can do.", "Unknown"),
    ("One small crack does not mean you are broken; it means you were put to the test and didn't fall apart.", "Linda Poindexter"),
    ("Almost everything will work again if you unplug it for a few minutes, including you.", "Anne Lamott"),
    ("Vulnerability is the birthplace of innovation, creativity, and change.", "Brené Brown"),
    ("Not until we are lost do we begin to understand ourselves.", "Henry David Thoreau"),
    ("Start where you are. Use what you have. Do what you can.", "Arthur Ashe"),
    ("Sometimes you climb out of bed in the morning and you think, I'm not going to make it, but you laugh inside — remembering all the times you've felt that way.", "Charles Bukowski"),
    ("Mental health is not a luxury. It is a fundamental human right.", "Unknown"),
    ("Your mental health is a priority. Your happiness is essential. Your self-care is a necessity.", "Unknown"),
    ("Breathe. You are enough. You are safe. You are loved.", "Unknown"),
    ("In the middle of difficulty lies opportunity.", "Albert Einstein"),
    ("It's okay to ask for help. It's a sign of strength, not weakness.", "Unknown"),
    ("Fall seven times, stand up eight.", "Japanese Proverb"),
    ("Be the change you wish to see in the world — and start by being kind to yourself.", "Unknown"),
    ("You survived 100% of your worst days. You can survive this too.", "Unknown"),
    ("The wound is the place where the Light enters you.", "Rumi"),
    ("Happiness can be found even in the darkest of times, if one only remembers to turn on the light.", "Albus Dumbledore"),
    ("Gentle reminder: you are doing better than you think.", "Unknown"),
    ("Peace begins with a smile.", "Mother Teresa"),
]


def get_daily_quote() -> dict:
    """Return today's quote as {text, author}."""
    idx = date.today().toordinal() % len(QUOTES)
    text, author = QUOTES[idx]
    return {"text": text, "author": author}
