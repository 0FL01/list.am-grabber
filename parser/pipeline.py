import random
import time
from collections.abc import Callable
from dataclasses import dataclass

from db_service import ListingStateStore
from models import RentalListing


@dataclass(frozen=True)
class ProcessingResult:
    baselined: int = 0
    delivered: int = 0
    unchanged: int = 0


def process_listings(
    listings: list[RentalListing],
    state: ListingStateStore,
    notify: Callable[[RentalListing], None],
    notify_existing_on_first_run: bool = False,
    delivery_jitter_seconds: tuple[float, float] | None = None,
) -> ProcessingResult:
    unique_listings = list({listing.id: listing for listing in listings}.values())

    if not state.is_initialized():
        if not notify_existing_on_first_run:
            state.initialize(unique_listings)
            return ProcessingResult(baselined=len(unique_listings))
        state.initialize([])

    pending = []
    unchanged = 0
    for listing in unique_listings:
        if state.get_price_key(listing.id) == listing.price_key:
            unchanged += 1
        else:
            pending.append(listing)

    delivered = 0
    for index, listing in enumerate(pending):
        notify(listing)
        state.save(listing)
        delivered += 1
        if delivery_jitter_seconds and index < len(pending) - 1:
            time.sleep(random.uniform(*delivery_jitter_seconds))

    return ProcessingResult(delivered=delivered, unchanged=unchanged)
