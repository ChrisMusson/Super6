BASE_URL = "https://api.s6.sbgservices.com/v2"

API_URLS = {
    "active": f"{BASE_URL}/round/active",
    "prediction": f"{BASE_URL}/round/{{}}/user/{{}}",
    "round": f"{BASE_URL}/round/{{}}",
    "user": f"{BASE_URL}/round/1/user/{{}}"   
}
