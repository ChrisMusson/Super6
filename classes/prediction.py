class Prediction:
    '''A class that represents a user's prediction for a given fixture'''

    def __init__(
        self,
        user_id: int,
        round_number: int,
        challenge_id: int,
        home_score: int,
        away_score: int
    ) -> None:

        self.user_id = user_id
        self.round_number = round_number
        self.challenge_id = challenge_id
        self.home_score = home_score
        self.away_score = away_score
