import uuid
from json import JSONDecodeError
from loguru import logger
from locust import HttpUser, task


def create_user(client):
    # login as admin
    headers = {"Content-Type": "application/json"}
    body = {"username": "admin", "password": "222222"}
    admin_info = {}
    with client.post(url="/api/v1/users/login", headers=headers, json=body, name="/users/login") as resp:
        try:
            resp = resp.json()
            if resp["status"] != 1:
                resp.failure("failed to login as admin")
            else:  # success
                admin_info = resp["data"]
        except JSONDecodeError:
            resp.failure("Response could not be decoded as JSON")

    # create a user
    user_name = str(uuid.uuid4())
    password = "1234"
    headers = {"Authorization": f"Bearer {admin_info['token']}",
               "Accept": "application/json", "Content-Type": "application/json"}
    body = {"documentNum": None, "documentType": 0, "email": "test@example.com", "gender": 0, "password": password,
            "userName": user_name}
    with client.post(url="/api/v1/adminuserservice/users",
                     headers=headers, json=body, name="/adminuserservice/users") as resp:
        try:
            resp = resp.json()
            if resp["status"] != 1:
                resp.failure("failed to create user")
            else:  # success
                logger.info("create user, response:{}".format(resp))
        except JSONDecodeError:
            resp.failure("Response could not be decoded as JSON")

    # login as created user
    user_info = {}
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    body = {"username": user_name, "password": password}
    with client.post(url="/api/v1/users/login", headers=headers, json=body, name="/users/login") as resp:
        try:
            resp = resp.json()
            if resp["status"] != 1:
                resp.failure("failed to login as created user")
            else:  # success
                user_info = resp["data"]
                logger.info("created user logged in, user info: {}".format(user_info))
        except JSONDecodeError:
            resp.failure("Response could not be decoded as JSON")


class TrainTicketUser(HttpUser):
    # login as admin and create a user
    def on_start(self):
        create_user(self.client)

    @task
    def hello_world(self):
        resp = self.client.get("/")

    # delete the user, avoiding too many users
    def on_stop(self):
        pass
