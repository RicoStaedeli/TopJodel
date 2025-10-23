class AuthenticationError(Exception):
    PREFIX = "❌ Authentication error: "

    def __init__(self, message):
        super().__init__(self.PREFIX + str(message))

class RegistrationError(Exception):
    PREFIX = "❌ Registration failed: "

    def __init__(self, message):
        # store the prefixed message
        super().__init__(self.PREFIX + str(message))

class UserError(Exception):
    pass

class TokenError(Exception):
    pass

class ProfileError(Exception):
    PREFIX = "❌ Profile error: "

    def __init__(self, message):
        super().__init__(self.PREFIX + str(message))