"""
Recommendation engine — runs as a Django management command or Celery task.

Algorithms:
  1. Collaborative filtering  — cosine similarity between users based on borrow history
  2. Content-based filtering  — TF-IDF on book title + genre + description
  3. Hybrid score             — 0.6 × collaborative + 0.4 × content-based
"""
import os
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from django.conf import settings

MODEL_DIR = os.path.join(settings.BASE_DIR, 'ml_models')
os.makedirs(MODEL_DIR, exist_ok=True)

COLLAB_MATRIX_PATH = os.path.join(MODEL_DIR, 'user_item_matrix.pkl')
CONTENT_MATRIX_PATH = os.path.join(MODEL_DIR, 'content_matrix.pkl')
BOOK_IDS_PATH = os.path.join(MODEL_DIR, 'book_ids.pkl')


# ── Training ──────────────────────────────────────────────────────────────────

def build_user_item_matrix():
    """
    Builds a user × book matrix where each cell = number of times borrowed.
    Saved to disk for fast inference.
    """
    from apps.borrowings.models import BorrowingHistory, Borrowing

    history_qs = list(BorrowingHistory.objects.values('user_id', 'book_id'))
    active_qs = list(Borrowing.objects.values('user_id', 'book_id'))
    
    if not history_qs and not active_qs:
        return None, None

    df = pd.DataFrame(history_qs + active_qs)
    matrix = df.groupby(['user_id', 'book_id']).size().unstack(fill_value=0)
    joblib.dump(matrix, COLLAB_MATRIX_PATH)
    return matrix


def build_content_matrix():
    """
    TF-IDF on title + genre + description for every active book.
    """
    from apps.books.models import Book

    books = Book.objects.filter(is_active=True).values('id', 'title', 'genre', 'description', 'author')
    if not books:
        return None, None

    df = pd.DataFrame(list(books))
    df['text'] = (
        df['title'].fillna('') + ' ' +
        df['genre'].fillna('') + ' ' +
        df['author'].fillna('') + ' ' +
        df['description'].fillna('')
    )

    vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(df['text'])
    book_ids = df['id'].tolist()

    joblib.dump({'matrix': tfidf_matrix, 'vectorizer': vectorizer, 'book_ids': book_ids}, CONTENT_MATRIX_PATH)
    return tfidf_matrix, book_ids


def train_all():
    """Called by the nightly Celery task and the management command."""
    print("Building user-item matrix...")
    build_user_item_matrix()
    print("Building content matrix...")
    build_content_matrix()
    print("Training complete.")


# ── Inference ─────────────────────────────────────────────────────────────────

def get_collaborative_scores(user_id, n=20):
    """Returns {book_id: score} for collaborative filtering."""
    if not os.path.exists(COLLAB_MATRIX_PATH):
        return {}

    matrix = joblib.load(COLLAB_MATRIX_PATH)

    if user_id not in matrix.index:
        return {}

    user_vec = matrix.loc[user_id].values.reshape(1, -1)
    similarities = cosine_similarity(user_vec, matrix.values)[0]
    similar_users_idx = np.argsort(similarities)[::-1][1:11]  # top 10 similar users

    scores = {}
    already_borrowed = set(matrix.columns[matrix.loc[user_id] > 0])

    for idx in similar_users_idx:
        sim_score = similarities[idx]
        sim_user_borrows = matrix.iloc[idx]
        for book_id, count in sim_user_borrows.items():
            if book_id not in already_borrowed and count > 0:
                scores[book_id] = scores.get(book_id, 0) + sim_score * count

    # Normalize
    if scores:
        max_score = max(scores.values())
        scores = {k: v / max_score for k, v in scores.items()}

    return scores


def get_content_scores(user_id, n=20):
    """Returns {book_id: score} based on books the user has read."""
    if not os.path.exists(CONTENT_MATRIX_PATH):
        return {}

    from apps.borrowings.models import BorrowingHistory, Borrowing

    data = joblib.load(CONTENT_MATRIX_PATH)
    tfidf_matrix = data['matrix']
    book_ids = data['book_ids']

    history_ids = list(BorrowingHistory.objects.filter(user_id=user_id).values_list('book_id', flat=True))
    active_ids = list(Borrowing.objects.filter(user_id=user_id).values_list('book_id', flat=True))
    read_book_ids = list(set(history_ids + active_ids))
    
    if not read_book_ids:
        return {}

    read_indices = [book_ids.index(bid) for bid in read_book_ids if bid in book_ids]
    if not read_indices:
        return {}

    user_profile = np.asarray(tfidf_matrix[read_indices].mean(axis=0))
    sim_scores = cosine_similarity(user_profile, tfidf_matrix)[0]

    scores = {}
    for idx, score in enumerate(sim_scores):
        bid = book_ids[idx]
        if bid not in read_book_ids:
            scores[bid] = float(score)

    return scores


def get_recommendations(user_id, n=10):
    """
    Returns list of (book_id, hybrid_score) sorted by score desc.
    """
    collab = get_collaborative_scores(user_id)
    content = get_content_scores(user_id)

    all_book_ids = set(collab.keys()) | set(content.keys())
    hybrid = {}
    for bid in all_book_ids:
        c_score = collab.get(bid, 0)
        ct_score = content.get(bid, 0)
        hybrid[bid] = 0.6 * c_score + 0.4 * ct_score

    sorted_recs = sorted(hybrid.items(), key=lambda x: x[1], reverse=True)[:n]
    return sorted_recs  # [(book_id, score), ...]


def refresh_recommendations_for_user(user_id):
    """
    Compute fresh recommendations and save to BookRecommendation table.
    Called per-user by the nightly Celery task.
    """
    from apps.recommendations.models import BookRecommendation
    from apps.books.models import Book

    recs = get_recommendations(user_id)
    if not recs:
        return

    # Delete old recommendations for this user
    BookRecommendation.objects.filter(user_id=user_id).delete()

    # Bulk create new ones
    book_ids = [r[0] for r in recs]
    books = {b.id: b for b in Book.objects.filter(id__in=book_ids, is_active=True)}

    new_recs = []
    for book_id, score in recs:
        if book_id in books:
            new_recs.append(BookRecommendation(
                user_id=user_id,
                book=books[book_id],
                score=score,
                reason="Based on your reading history",
            ))

    BookRecommendation.objects.bulk_create(new_recs)