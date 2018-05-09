import json

__author__ = "Benjamin Martin"
__copyright__ = "Copyright 2018, The University of Queensland"
__license__ = "MIT"
__version__ = "1.0.0"

DEFAULT_GAME = 'basic'


class HighScoreManager:
    """Manages high scores across multiple game types & persists to file"""
    _data = None
    _top_scores = 10  # The number of scores on each leader board

    def __init__(self, filename='high_scores.json'):
        self._filename = filename
        self.load(filename)

    def load(self, filename):
        try:
            with open(filename) as file:
                self._data = json.load(file)
        except FileNotFoundError:
            self._data = {}

    def save(self, filename=None):
        if filename is None:
            filename = self._filename

        with open(filename, 'w') as file:
            json.dump(self._data, file)

    def get_lowest_score(self, game=DEFAULT_GAME):
        entries = self._data.get(game)

        if entries is None:
            return None

        return entries[-1]['score']

    def does_score_qualify(self, score, game=DEFAULT_GAME):
        if score == 0:
            return False

        lowest = self.get_lowest_score(game=game)

        if lowest is None:
            return True

        return len(self._data.get(game)) < self._top_scores or score > lowest

    def add_entry(self, name, score, data=None, game=DEFAULT_GAME):
        if game not in self._data:
            self._data[game] = []

        entries = self._data[game]

        entries.append({
            'name': name,
            'score': score,
            'data': data
        })

        entries.sort(key=lambda entry: entry['score'], reverse=True)

        if len(entries) > self._top_scores:
            return entries.pop()

    def get_entries(self, game='basic'):
        return self._data.get(game, [])
