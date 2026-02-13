from celery_app import celery
from database import SessionLocal
import models
from services.marketprice import get_live_price
from datetime import datetime


@celery.task(bind=True, autoretry_for=(Exception,), retry_backoff=10, retry_kwargs={"max_retries": 3})
def refresh_investments_task(self, user_id: int):
    db = SessionLocal()

    investments = (
        db.query(models.Investment)
        .filter(models.Investment.user_id == user_id)
        .all()
    )

    for inv in investments:
        try:
            price = get_live_price(inv.symbol)

            inv.last_price = price
            inv.current_value = round(inv.units * price, 2)
            inv.last_price_at = datetime.utcnow()

        except Exception as e:
            print(f"Price fetch failed for {inv.symbol}: {e}")

    db.commit()
    db.close()

    return f"Investments refreshed for user {user_id}"
