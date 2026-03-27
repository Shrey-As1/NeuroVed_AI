import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

faq = pd.read_csv("data/Mental_Health_FAQ.csv")

questions = faq["Questions"].astype(str).tolist()
answers = faq["Answers"].astype(str).tolist()

vectorizer = TfidfVectorizer(stop_words="english")
question_vectors = vectorizer.fit_transform(questions)


def retrieve_answer(query):

    query_vec = vectorizer.transform([query])

    similarity = cosine_similarity(query_vec, question_vectors)

    best_idx = similarity.argmax()
    score = similarity[0][best_idx]

    if score > 0.45:
        return answers[best_idx]

    return None