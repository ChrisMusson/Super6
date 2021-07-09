class Result:
    '''A class that represents the result of the given challenge_id'''

    def __init__(
        self,
        challenge_id: int,
        round_number: int,
        home_score: int,
        away_score: int,
        started: bool,
        finished: bool,
        void: bool
    ) -> None:

        self.challenge_id = challenge_id
        self.round_number = round_number
        self.home_score = home_score
        self.away_score = away_score
        self.started = started
        self.finished = finished
        self.void = void
