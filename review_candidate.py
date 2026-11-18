"""A proposed change for you to evaluate after completing Store.

A teammate proposes keeping each statistics result in memory so repeated
statistics requests can reuse it. Compare this version with Store before
choosing what to release. Keep your findings in your own release note.
"""
from store import Store


class CandidateStore(Store):
    def __init__(self, database):
        super().__init__(database)
        self._previous_stats = {}

    def stats(self, code):
        if code not in self._previous_stats:
            result = super().stats(code)
            if result is not None:
                self._previous_stats[code] = result
            return result
        return dict(self._previous_stats[code])
