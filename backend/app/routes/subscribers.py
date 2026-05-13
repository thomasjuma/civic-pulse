from fastapi import APIRouter

from app.database import get_connection
from app.models import Subscriber, SubscriberUpsert
from app.repositories import upsert_subscriber

router = APIRouter(prefix="/subscribers", tags=["subscribers"])


@router.post("", response_model=Subscriber)
def save_subscriber(subscriber: SubscriberUpsert) -> Subscriber:
    with get_connection() as connection:
        return upsert_subscriber(connection, subscriber)

