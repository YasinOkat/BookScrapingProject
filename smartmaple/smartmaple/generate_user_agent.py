from fake_useragent import UserAgent


def generate_random_user_agent():
    ua = UserAgent()
    return ua.random


random_user_agent = generate_random_user_agent()
print("User Agent:", random_user_agent)
