import time


def login(driver, username, pin, url="https://super6.skysports.com/results/round/1/user/1000000"):

    driver.get(url)
    done = False
    attempts = 0
    while done is False:
        try:
            time.sleep(1)
            driver.switch_to.frame("SkyBetAccount")
            form = driver.find_element_by_tag_name("form")
            form.find_element_by_name("username").send_keys(username)
            form.find_element_by_name("pin").send_keys(pin)
            form.find_element_by_tag_name("button").click()
            done = True
        except:
            if attempts > 5:
                print(
                    "Something was wrong with the website, probably couldn't find the correct form or iframe")
                break
            else:
                attempts += 1
                driver.refresh()
    time.sleep(2)  # Makes sure the annoying popup has enough time to fully load
    driver.refresh()  # Gets rid of the popup
    time.sleep(0.5)
