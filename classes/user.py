class User:
    '''A class that represents a user'''

    def __init__(
        self,
        user_id: int,
        first_name: str,
        last_name: str
    ) -> None:

        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
