import random
import urllib.parse
import uuid
from datetime import datetime, timedelta
from json import JSONDecodeError
from loguru import logger
from locust import HttpUser, task, between

ORDER_NOT_PAID = 0
ORDER_PAID = 1
ORDER_COLLECTED = 2


def get(client, url, name, err_msg, additional_headers=None):
    """
    http get method helper
    deal with json response, set necessary headers and so on
    :param client: http client
    :param url: url path
    :param name: request name for request grouping
    :param err_msg: error message when response status is not expected
    :param additional_headers: headers to be updated, optional
    :return:
    """
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if additional_headers:
        headers.update(additional_headers)
    with client.get(url=url, headers=headers, name=name) as resp:
        try:
            resp = resp.json()
            if resp["status"] != 1:
                logger.error("response status code: {}, error message: {}".format(resp["status"], err_msg))
            else:  # success
                return resp
        except JSONDecodeError:
            logger.error("Response could not be decoded as JSON")


def post(client, url, body, name, err_msg, additional_headers=None):
    """
    http post method helper
    deal with json response, set necessary headers and so on
    :param name: request name for request grouping
    :param err_msg: error message when response status is not expected
    :param client: http client
    :param url: url path
    :param body: request body
    :param additional_headers: headers to be updated, optional
    """
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if additional_headers:
        headers.update(additional_headers)
    with client.post(url=url, headers=headers, json=body, name=name) as resp:
        try:
            resp = resp.json()
            if resp["status"] != 1:
                logger.error("response status code: {}, error message: {}".format(resp["status"], err_msg))
            else:  # success
                return resp
        except JSONDecodeError:
            logger.error("Response could not be decoded as JSON")


def create_user(client):
    # login as admin
    body = {"username": "admin", "password": "222222"}
    admin_info = {}
    resp = post(client, url="/api/v1/users/login", body=body, name="/users/login",
                err_msg="failed to login as admin")
    logger.info("admin login, resp: {}".format(resp))
    admin_info = resp["data"]

    # create a user
    user_name = str(uuid.uuid4())
    password = "1234"
    headers = {"Authorization": "Bearer {}".format(admin_info["token"])}
    body = {"documentNum": 0, "documentType": 0, "email": "test@example.com", "gender": 0, "password": password,
            "userName": user_name}
    resp = post(client, url="/api/v1/adminuserservice/users", body=body, name="/adminuserservice/users",
                err_msg="failed to create user as admin", additional_headers=headers)
    logger.info("create a user, resp: {}".format(resp))

    # login as created user
    user_info = {}
    body = {"username": user_name, "password": password}
    resp = post(client, url="/api/v1/users/login", body=body, name="/users/login",
                err_msg="failed to login as created user")
    user_info = resp["data"]
    logger.info("created user logged in, user info: {}".format(user_info))
    return user_info  # userId, username, token


def create_contact_for_user(client, user_info):
    """
    create contact information for created user, like ID card info
    :param client: http client
    :param user_info: dict type, including username, userId and token
    """
    body = {"name": user_info["username"], "accountId": user_info["userId"],
            "documentType": 0, "documentNumber": "1234", "phoneNumber": "1234"}
    resp = post(client, url="/api/v1/contactservice/contacts", body=body, name="/contactservice/contacts",
                err_msg="failed to create contact for created user")
    logger.info("created contact, resp: {}".format(resp))


def search_tickets(client, source, dest, date):
    """
    search tickets from source to dest on date
    :param date: departure date
    :param client: http client
    :param source: starting place
    :param dest: end place
    """
    body = {"startingPlace": source, "endPlace": dest, "departureTime": date}
    resp = post(client, url="/api/v1/travelservice/trips/left", body=body, name="/travelservice/trips/left",
                err_msg="failed to search tickets")
    ticket_list = resp["data"]
    logger.info("searched tickets: {}".format(ticket_list))
    return ticket_list


def get_assurance(client):
    url = "/api/v1/assuranceservice/assurances/types"
    resp = get(client, url=url, name="/assuranceservice/assurances/types",
               err_msg="failed to get assurance")
    assurance_list = resp["data"]
    logger.info("get assurance: {}".format(assurance_list))
    return assurance_list


def get_food(client, date, source, dest, tripId):
    """
    get train food or station food supplied at trip `tripId` from `source` to `dest` on `date`
    when there is no food, http response status will be 0, which is not expected
    :param client: http client
    :param date: departure date
    :param source: starting place
    :param dest: end place
    :param tripId: trip id consisting of type and number, eg: D1234
    :return: food list
    """
    url = "/api/v1/foodservice/foods/{}/{}/{}/{}".format(date, urllib.parse.quote(source),
                                                         urllib.parse.quote(dest), tripId)
    resp = get(client, url=url, name="/foodservice/foods",
               err_msg="failed to get food")
    food_list = resp["data"]
    logger.info("get food: {}".format(food_list))
    return food_list


def get_contacts(client, user_id):
    url = "/api/v1/contactservice/contacts/account/{}".format(user_id)
    resp = get(client, url=url, name="/contactservice/contacts/",
               err_msg="failed to get contacts for specific user")
    contact_list = resp["data"]
    logger.info("get contacts: {}".format(contact_list))
    return contact_list


def preserve_ticket(client, user_id, contact_id, date, start_place, end_place, tripId):
    body = {
        "accountId": user_id,
        "contactsId": contact_id,
        "date": date,
        "from": start_place,
        "to": end_place,
        "tripId": tripId,
        # the following fields not used later, so we hard code here
        "seatType": "2",
        "foodName": "Soup",
        "foodPrice": 3.7,
        "foodType": 2,
        "stationName": "Su Zhou",
        "storeName": "Roman Holiday"
    }
    # random choose assurance
    need_assurance = random.choice([True, False])
    if need_assurance:
        body["assurance"] = "1"
    else:
        body["assurance"] = "0"

    resp = post(client, url="/api/v1/preserveservice/preserve", body=body, name="/preserveservice/preserve",
                err_msg="failed to preserve ticket")
    logger.info("preserved ticket, response message: {}".format(resp["data"]))


def get_matched_order(client, user_id, expected_status):
    body = {"loginId": user_id, "enableStateQuery": False,
            "enableTravelDateQuery": False, "enableBoughtDateQuery": False, "travelDateStart": None,
            "travelDateEnd": None, "boughtDateStart": None, "boughtDateEnd": None}
    resp = post(client, url="/api/v1/orderservice/order/refresh", body=body,
                name="/orderservice/order/refresh", err_msg="failed to get orders")
    order_list = resp["data"]
    order_id = ""
    for order in order_list:
        if order["status"] == expected_status:
            order_id = order["id"]
            break
    if order_id == "":
        logger.error("there is no not-paid order")
        return
    return order_id


def pay_ticket(client, user_id, trip_id):
    # get not paid order
    order_id = get_matched_order(client, user_id, ORDER_NOT_PAID)
    # pay the order
    body = {
        "orderId": order_id,
        "tripId": trip_id
    }
    post(client, url="/api/v1/inside_pay_service/inside_payment", body=body,
         name="/inside_pay_service/inside_payment", err_msg="failed to pay order")
    logger.info("paied ticket")


def collect_and_enter(client, user_id):
    # collect
    order_id = get_matched_order(client, user_id, ORDER_PAID)
    get(client, url="/api/v1/executeservice/execute/collected/{}".format(order_id),
        name="/executeservice/execute/collected", err_msg="failed to collect ticket")
    # enter station
    order_id = get_matched_order(client, user_id, ORDER_COLLECTED)
    get(client, url="/api/v1/executeservice/execute/execute/{}".format(order_id),
        name="/executeservice/execute/execute", err_msg="failed to collect ticket")
    logger.info("collected ticket and entered station")


def delete_user(client, user_id):
    # login as admin
    body = {"username": "admin", "password": "222222"}
    admin_info = {}
    resp = post(client, url="/api/v1/users/login", body=body, name="/users/login",
                err_msg="failed to login as admin")
    logger.info("admin login, resp: {}".format(resp))
    admin_info = resp["data"]
    headers = {"Authorization": "Bearer {}".format(admin_info["token"])}
    # delete current created user
    resp = client.delete(url="/api/v1/adminuserservice/users/{}".format(user_id),
                         headers=headers, name="/adminuserservice/users")
    logger.info("successfully delete user {}".format(user_id))


class TrainTicketUser(HttpUser):
    # define waiting time between each task
    wait_time = between(1, 5)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_info = None

    # create a user and login as that user, then set auth headers for following requests
    def on_start(self):
        self.user_info = create_user(self.client)
        self.client.headers.update({"Authorization": "Bearer {}".format(self.user_info["token"])})
        create_contact_for_user(self.client, self.user_info)

    @task
    def take_train(self):
        start_place = "Shang Hai"
        end_place = "Su Zhou"
        tomorrow_time = datetime.now() + timedelta(days=1)
        tomorrow_date = tomorrow_time.strftime("%Y-%m-%d")
        # search tickets
        ticket_list = search_tickets(self.client, source=start_place, dest=end_place, date=tomorrow_date)
        ticket = random.choice(ticket_list)
        trip_id = ticket["tripId"]["type"] + ticket["tripId"]["number"]

        # food and assurance are not used for downstream calls,
        #  the payload will have food information no matter we need or not, assurance only need 0 or 1
        _ = get_assurance(self.client)
        _ = get_food(self.client, tomorrow_date, start_place, end_place, trip_id)
        contact_list = get_contacts(self.client, self.user_info["userId"])
        contact = random.choice(contact_list)
        # book tickets
        preserve_ticket(self.client, self.user_info["userId"], contact["id"],
                        tomorrow_date, start_place, end_place, trip_id)
        # collect
        pay_ticket(self.client, self.user_info["userId"], trip_id)
        # enter station
        collect_and_enter(self.client, self.user_info["userId"])

    # delete the user, avoiding too many users
    def on_stop(self):
        delete_user(self.client, self.user_info["userId"])
