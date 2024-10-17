"""API urls."""

import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv('API_URL')

# auth
SIGN_UP_URL = API_URL + os.getenv('SIGN_UP_URL')
LOG_IN_URL = API_URL + os.getenv('LOG_IN_URL')
USER_PROFILE_URL = API_URL + os.getenv('USER_PROFILE_URL')
LOG_OUT_URL = API_URL + os.getenv('LOG_OUT_URL')

# languages
ALL_LANGUAGES_URL = API_URL + os.getenv('ALL_LANGUAGES_URL')
AVAILABLE_LANGUAGES_URL = API_URL + os.getenv('AVAILABLE_LANGUAGES_URL')
LEARNING_LANGUAGES_URL = API_URL + os.getenv('LEARNING_LANGUAGES_URL')
INTERFACE_LANGUAGES_URL = API_URL + os.getenv('INTERFACE_LANGUAGES_URL')

# vocabulary
VOCABULARY_URL = API_URL + os.getenv('VOCABULARY_URL')

# collections
