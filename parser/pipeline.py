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
) -> ProcessingResult:
    unique_listings = list({listing.id: listing for listing in listings}.values())

    if not state.is_initialized():
        state.initialize(unique_listings)
        return ProcessingResult(baselined=len(unique_listings))

    delivered = 0
    unchanged = 0
    for listing in unique_listings:
        if state.get_price_key(listing.id) == listing.price_key:
            unchanged += 1
            continue

        notify(listing)
        state.save(listing)
        delivered += 1

    return ProcessingResult(delivered=delivered, unchanged=unchanged)
