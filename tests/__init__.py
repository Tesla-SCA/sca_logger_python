from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(".env", raise_error_if_not_found=True))
