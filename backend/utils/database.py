from models import db, Notification


def push_notification(user_id, title, message, notif_type="info"):
    """Creates an in-app notification record for a user. The frontend polls
    /api/notifications to render these in real time (short-interval polling
    simulates a live/real-time feed without needing websockets)."""
    if user_id is None:
        return None
    notif = Notification(user_id=user_id, title=title, message=message, notif_type=notif_type)
    db.session.add(notif)
    db.session.commit()
    return notif


def paginate_query(query, page=1, per_page=10):
    page = max(1, page)
    per_page = max(1, min(100, per_page))
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page else 0,
    }
