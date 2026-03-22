"""Pronunciation repository. Read + bulk-upsert for pipeline use."""

from sqlalchemy import select
# Note: Use sqlalchemy.dialects.sqlite if you are on SQLite instead of Postgres
from sqlalchemy.dialects.postgresql import insert 
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.pronunciations import PronunciationEntry


class PronunciationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[PronunciationEntry]:
        """Load full dictionary. Called once per pipeline run."""
        statement = select(PronunciationEntry).order_by(
            PronunciationEntry.written_form
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def bulk_upsert(self, terms: list[dict[str, str]]) -> int:
        """
        Persist new terms discovered during Term Extraction.
        Uses First-In Wins: If a word already exists (verified or unverified),
        we completely ignore the LLM's new guess to provide a stable admin queue.
        """
        if not terms:
            return 0

        values_to_insert = [
            {
                "written_form": term["written_form"].lower(),
                "spoken_form": term["spoken_form"],
                "is_verified": False,
            }
            for term in terms
        ]

        stmt = insert(PronunciationEntry).values(values_to_insert)

        # If the word is already in the DB, touch nothing.
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["written_form"]
        )

        result = await self.session.execute(stmt)
        return result.rowcount