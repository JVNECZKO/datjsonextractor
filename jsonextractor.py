import time
import json
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


def set_cookies(driver, cookies):
    driver.get("") # insert url
    time.sleep(5) 
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.refresh()
    time.sleep(7) 

def intercept_network_requests(driver, reference_code, output_folder):

    driver.get_log("performance")
    
    # Find search box and insert ref code
    search_box = driver.find_element(By.ID, "searchBoxSearchTerm")
    search_box.clear()
    search_box.send_keys(reference_code)
    search_box.send_keys(Keys.RETURN)

    # Wait to load search results
    time.sleep(7)

    # Download Netowork Logs
    logs = driver.get_log("performance")
    log_data = []

    for log in logs:
        message = json.loads(log["message"])
        log_data.append(message)  # save log to list
        if "Network.responseReceived" in message["message"]["method"]:
            response_params = message["message"]["params"]
            if "response" in response_params and "requestId" in response_params:
                response = response_params["response"]
                if "mimeType" in response and "application/json" in response["mimeType"]:
                    request_id = response_params["requestId"]
                    body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                    try:
                        response_data = json.loads(body['body'])
                        # save singular JSON file for each call
                        output_file = os.path.join(output_folder, f"{reference_code}_{request_id}.json")
                        with open(output_file, 'w') as f:
                            json.dump(response_data, f, indent=4)
                    except json.JSONDecodeError:
                        pass
    
    # Save all logs in JSON
    output_file = os.path.join(output_folder, f"{reference_code}_network_logs.json")
    with open(output_file, 'w') as f:
        json.dump(log_data, f, indent=4)

# Selenium config
caps = DesiredCapabilities.CHROME
caps['goog:loggingPrefs'] = {'performance': 'ALL'}

options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # launch in headless mode, to save memory usage
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Init Cookies
cookies = [
    {"name": "accessToken", "value": "insert_elements_token", "domain": ".elements.4sellers.cloud"},
    {"name": "refreshToken", "value": "insert_elements_token", "domain": ".elements.4sellers.cloud"}
]
# Set cookies in web browser
set_cookies(driver, cookies)

# Read reference codes
df = pd.read_excel("Insert_reference_code_path")
reference_codes = df['ReferenceCodeColumn'].tolist()

# Output Folder
output_folder = "Insert_output_folder"
os.makedirs(output_folder, exist_ok=True)

# Download data and save in JSON
for code in reference_codes:
    intercept_network_requests(driver, code, output_folder)

# Close Web Browser
driver.quit()

