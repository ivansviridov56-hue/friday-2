"""Long-term memory store: a short list of facts kept in a local JSON file.

One responsibility: keep facts, save them atomically, find them again.
It knows nothing about voice, commands or the LLM. The caller passes the file
path (resolved from the project root), so nothing here is hardcoded.

Fact texts are personal data, so they are never written to the log.
"""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile
import threading
import time
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_MAX_FACTS = 100
DEFAULT_MAX_FACT_LENGTH = 300

_NON_WORD = re.compile(r"[\W_]+", re.UNICODE)


class AddStatus(Enum):
    ADDED = "added"
    EMPTY = "empty"
    TOO_LONG = "too_long"
    DUPLICATE = "duplicate"
    FULL = "full"


def normalize(text: str) -> str:
    """Lower case, 'ё' as 'е', punctuation and repeated spaces collapsed."""
    lowered = text.lower().replace("ё", "е")
    return _NON_WORD.sub(" ", lowered).strip()


class MemoryStore:
    """Facts about the user, persisted to a JSON file."""

    def __init__(
        self,
        path: Path,
        max_facts: int = DEFAULT_MAX_FACTS,
        max_fact_length: int = DEFAULT_MAX_FACT_LENGTH,
    ) -> None:
        self._path = Path(path)
        self._max_facts = max_facts
        self._max_fact_length = max_fact_length
        self._lock = threading.Lock()
        self._facts: list[str] = self._load()

    def __len__(self) -> int:
        with self._lock:
            return len(self._facts)

    def facts(self) -> list[str]:
        """A copy of all facts, oldest first."""
        with self._lock:
            return list(self._facts)

    def add(self, text: str) -> AddStatus:
        """Save one fact. Returns why it was not saved, if it was not."""
        fact = text.strip()
        if not normalize(fact):
            return AddStatus.EMPTY
        if len(fact) > self._max_fact_length:
            return AddStatus.TOO_LONG
        with self._lock:
            key = normalize(fact)
            if any(normalize(existing) == key for existing in self._facts):
                return AddStatus.DUPLICATE
            if len(self._facts) >= self._max_facts:
                return AddStatus.FULL
            updated = [*self._facts, fact]
            self._save(updated)
            self._facts = updated
        logger.info("memory: fact added (%d stored)", len(updated))
        return AddStatus.ADDED

    def forget(self, query: str) -> list[str]:
        """Remove every fact that contains the query. Returns the removed facts."""
        key = normalize(query)
        if not key:
            return []
        with self._lock:
            removed = [f for f in self._facts if key in normalize(f)]
            if not removed:
                return []
            kept = [f for f in self._facts if f not in removed]
            self._save(kept)
            self._facts = kept
        logger.info("memory: %d fact(s) forgotten (%d stored)", len(removed), len(kept))
        return removed

    def _load(self) -> list[str]:
        if not self._path.exists():
            return []
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            raw = data["facts"]
            if not isinstance(raw, list):
                raise ValueError("'facts' is not a list")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            logger.warning(
                "memory: cannot read the memory file (%s)", type(exc).__name__
            )
            self._keep_backup()
            return []
        facts = [item.strip() for item in raw if isinstance(item, str) and item.strip()]
        logger.info("memory: loaded %d fact(s)", len(facts))
        return facts

    def _keep_backup(self) -> None:
        """Move an unreadable file aside so it is never overwritten silently."""
        stamp = time.strftime("%Y%m%d-%H%M%S")
        target = self._path.with_name(f"{self._path.name}.bad-{stamp}")
        counter = 1
        while target.exists():
            counter += 1
            target = self._path.with_name(f"{self._path.name}.bad-{stamp}-{counter}")
        try:
            os.replace(self._path, target)
            logger.warning("memory: unreadable file kept as %s", target.name)
        except OSError as exc:
            logger.error("memory: could not keep a backup (%s)", type(exc).__name__)

    def _save(self, facts: list[str]) -> None:
        """Write to a temporary file in the same folder, then replace atomically."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"facts": facts}, ensure_ascii=False, indent=2)
        fd, tmp_name = tempfile.mkstemp(
            dir=self._path.parent, prefix=self._path.name, suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(tmp_name, self._path)
        except BaseException:
            Path(tmp_name).unlink(missing_ok=True)
            raise
