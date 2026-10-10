from sqlalchemy import exists
from sqlalchemy.orm import Session, joinedload

from app.models.order import Order, OrderItem, OrderStatus
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate


def user_has_purchased(db: Session, user: User, product_id: int) -> bool:
    return db.query(
        exists().where(
            Order.user_id == user.id,
            Order.status != OrderStatus.CANCELLED,
            OrderItem.order_id == Order.id,
            OrderItem.product_id == product_id,
        )
    ).scalar()


def user_already_reviewed(db: Session, user: User, product_id: int) -> bool:
    return (
        db.query(Review)
        .filter(Review.product_id == product_id, Review.user_id == user.id)
        .first()
        is not None
    )


def list_reviews_for_product(db: Session, product_id: int) -> list[Review]:
    return (
        db.query(Review)
        .options(joinedload(Review.user))
        .filter(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
        .all()
    )


def create_review(db: Session, user: User, product_id: int, review_in: ReviewCreate) -> Review:
    review = Review(
        product_id=product_id,
        user_id=user.id,
        rating=review_in.rating,
        comment=review_in.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review
