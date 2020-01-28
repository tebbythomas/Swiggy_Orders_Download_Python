'''
Description:
Python 3 code using Seleniun to login to your Swiggy account on the Desktop,
scrape all the order information in your account and present the information
in a json file that includes details like:
1. Number of Swiggy Orders
2. Total amount spent
3. Number of orders delivered
4. Number of orders cancelled
5. Average amount spent per order
6. Each order's details - like restaurant, location, amount spent, date of order, etc

Input required: Phone number associated with the account and the subsequent OTP that is received on the phone

Output: orders_summary.json - containing all the order info
'''

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import datetime
import os
import time
import json


# Path of your chrome driver - make sure the version matches your chrome browser version
CHROMEDRIVER_PATH = '/Users/tebbythomas/Downloads/chromedriver'
# Swiggy Login Screen
SWIGGY_LOGIN_URL = 'https://www.swiggy.com'
# Scraped Order Details File
SCRAPED_ORDER_DETAILS_FILE = 'scraped_content.txt'
# Output JSON Filename
ORDER_INFO_JSON = 'orders_summary.json'

# Function to scrape web application for order details into a text file
def scrape_content_to_txt_file():
    # Selenium code to access the chrome driver
    driver = webdriver.Chrome(CHROMEDRIVER_PATH)

    # Opens the browser to the main login screen
    driver.get(SWIGGY_LOGIN_URL)
    print("Accessed the login screen")

    # Used to click on DIV element to enable infinite scrolling
    actions = ActionChains(driver)

    # Entering login details
    time.sleep(2)
    login_link = driver.find_element_by_link_text('Login')
    login_link.click()
    time.sleep(2)
    login_div = driver.find_element_by_id("overlay-sidebar-root")
    login_div.find_element_by_tag_name('input').send_keys(os.environ['MOBILE_NUM'])
    time.sleep(2)
    login_div.find_elements_by_tag_name('a')[1].click()

    print("Please enter the OTP received on your mobile number:")
    otp = input()
    login_div.find_elements_by_tag_name('input')[1].send_keys(otp)
    login_div.find_element_by_tag_name('a').click()
    time.sleep(4)
    # Link containing username has order details
    driver.find_element_by_link_text('Tebby Thomas').click()
    time.sleep(5)
    # Button to give more orders - it is an infinite scrolling button
    show_more_orders_el = driver.find_element_by_xpath("//div[contains(text(),'Show More Orders')]")
    actions.move_to_element_with_offset(show_more_orders_el, 10, 10).click(show_more_orders_el).perform()
    root_div = driver.find_element_by_id("root")
    first_inner_div = root_div.find_element_by_tag_name("div")

    while True:
        time.sleep(5)
        show_more_orders_el = driver.find_element_by_xpath("//div[contains(text(),'Show More Orders')]")
        # Size of inner div is calculated because it keeps increasing
        # The show more orders button has to keep getting clicked till 
        # the size of the page stops increasing
        first_inner_div = root_div.find_element_by_tag_name("div")
        prev_size = first_inner_div.size
        actions.move_to_element_with_offset(show_more_orders_el, 10, 10).click(show_more_orders_el).perform()
        first_inner_div = root_div.find_element_by_tag_name("div")
        cur_size = first_inner_div.size
        #print("Previous page height = {} and current page height = {}".format(prev_size['height'], cur_size['height']))
        # Check done to prevent program exiting immediately
        if prev_size['height'] == cur_size['height'] and cur_size['height'] != 2110:
            break
        first_inner_div = root_div.find_element_by_tag_name("div")
    root_div = driver.find_element_by_id("root")
    first_inner_div = root_div.find_element_by_tag_name("div")
    text_file = open(SCRAPED_ORDER_DETAILS_FILE, "w")
    n = text_file.write(first_inner_div.text)
    text_file.close()


# Function to check for phrases to ignore in text file
def check_phrase_in_line(line, key_phrases_to_ignore):
    for phrase in key_phrases_to_ignore:
        if phrase in line:
            return True
    return False


# Function to parse orders text file and format it as a json file
def parse_orders_file():
    filepath = SCRAPED_ORDER_DETAILS_FILE
    key_phrases_to_ignore = ["VIEW DETAILS", "REORDER", "HELP", "SHOW MORE ORDERS", "LOADING..."]
    each_restaurant_keys = ["Restaurant", "Location", "Order_Num_Time", "Order_Status", "Ordered_Items", "Amount_Paid"]
    # Final Dicitonary object to be later stored as json
    Orders_Summary = dict()
    # Only the individual order details stored here
    Order_Details_Sorted_By_Date_Desc = dict()
    order_count = 1
    total_amt_spent = 0
    total_cancelled_order_count = 0
    avg_amount_per_order = 0
    with open(filepath) as fp:
        line = fp.readline()
        cnt = 1
        order_cnt = 1
        while line:
            if "Past Orders" in line:
                while line:
                    line_count = 0
                    each_restaurant = dict()
                    if line == "":
                        break
                    while line_count < 6:
                        line = fp.readline()
                        line = line.replace("\n", "")
                        if line == "":
                            break
                        #print(line)
                        #print(each_restaurant)
                        while check_phrase_in_line(line, key_phrases_to_ignore) == True:
                            line = fp.readline()
                        line = line.replace("\n", "")
                        if line == "":
                            break
                        line_count += 1
                        if line_count == 6:
                            #print(line)
                            amt = int(line.split(":")[1].strip())
                            if "Cancelled" not in each_restaurant["Order_Status"]:
                                total_amt_spent += amt
                            else:
                                total_cancelled_order_count += 1
                            each_restaurant[each_restaurant_keys[line_count-1]] ="Rs." + line.split(":")[1]
                        else:
                            #print(line)
                            each_restaurant[each_restaurant_keys[line_count-1]] = line
                    #Order_Details_Sorted_By_Date_Desc["Order#_{}".format(order_cnt)] = each_restaurant
                    if line == "":
                        break
                    Order_Details_Sorted_By_Date_Desc[order_cnt] = each_restaurant
                    order_cnt += 1
            line = fp.readline()

    order_cnt -= 1
    avg_amount_per_order = total_amt_spent/(order_cnt - total_cancelled_order_count)
    # print("Total number of orders: {}".format(order_cnt))
    # print("Total amount spent: {}".format(total_amt_spent))
    # print("Total number of cancelled orders : {}".format(total_cancelled_order_count))
    # print("Average amount spent per order: {}".format(round(avg_amount_per_order, 2)))
    Orders_Summary["Count_Of_Orders_Total"] = order_cnt
    Orders_Summary["Count_Of_Orders_Delivered"] = order_cnt - total_cancelled_order_count
    Orders_Summary["Count_Of_Orders_Cancelled"] = total_cancelled_order_count
    Orders_Summary["Amt_Spent_In_Total"] = "Rs. {}".format(total_amt_spent)
    Orders_Summary["Avg_Amt_Spent_Per_Order"] = "Rs. {}".format(round(avg_amount_per_order, 2))
    Orders_Summary["Order_Details_Sorted_By_Date_Desc"] = Order_Details_Sorted_By_Date_Desc

    json_obj = json.dumps(
        Orders_Summary,
        sort_keys=True,
        indent=4
    )
    with open(ORDER_INFO_JSON, 'w') as fp:
        fp.write(json_obj)
    print("Order Details written into file: {}".format(ORDER_INFO_JSON))


# Entry point of code
if __name__=='__main__':
    scrape_content_to_txt_file()
    parse_orders_file()