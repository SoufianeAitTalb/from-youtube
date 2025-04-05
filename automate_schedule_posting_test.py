import os
import random

from selenium import webdriver
from selenium.common import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

from sympy.physics.units import hours
from yt_dlp.compat import shutil


# run in cmd
# "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:\Users\soufa\AppData\Local\Google\Chrome\User Data

def upload_to_tiktok_studio(video_path: str, description:str = "",hour:str = 21,day:str=26):
    print(f"Uploading {video_path} for {hour}:{day} with description: {description}")

    # Configure Chrome to connect to the open instance
    chrome_options = Options()
    chrome_options.headless = False
    chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")  # Connect via debug port

    # Initialize WebDriver (no need for Service/chromedriver)
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Open TikTok Studio in a new tab
        driver.get("https://www.tiktok.com/tiktokstudio/upload?from=creator_center")
        print("done1")
        WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
        upload_button =driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        upload_button.send_keys(video_path)
        print("done2")
        WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.public-DraftEditor-content[contenteditable="true"]')))

        editable_div = driver.find_element(By.CSS_SELECTOR, 'div.public-DraftEditor-content[contenteditable="true"]')

        # Clear the existing text (optional, only if you want to remove the "english_test" text)
        editable_div.clear()

        # Add new text
        editable_div.send_keys(description)
        print("done2 - description")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'Programmer')]/ancestor::label")))
        radio_button = driver.find_element(By.XPATH, "//span[contains(text(),'Programmer')]/ancestor::label")
        radio_button.click()
        print("done3")

        WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CLASS_NAME, "TUXTextInputCore-input")))

        time_date_input = driver.find_elements(By.CLASS_NAME, "TUXTextInputCore-input")
        time_input = time_date_input[0]
        date_input = time_date_input[1]

        # Click the input field to open the time picker or dropdown
        time_input.click()
        time.sleep(1)

#***********************************
        #WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,
         #                                    f"//span[contains(text(),{hour})]/ancestor::div[@class='tiktok-timepicker-option-item']")))

        #hour_selector = driver.find_element(By.XPATH,
                                        #     f"//span[contains(text(),{hour})]/ancestor::div[@class='tiktok-timepicker-option-item']")
        #hour_selector.click()
#************************************************
        i=0
        while True:
            try :
                WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.XPATH,
                                                   f"//span[contains(text(),{hour})]/ancestor::div[@class='tiktok-timepicker-option-item']")))
                hour_selector = driver.find_element(By.XPATH,
                f"//span[contains(text(),{hour})]/ancestor::div[@class='tiktok-timepicker-option-item']")
                driver.execute_script("arguments[0].scrollIntoView(true);", hour_selector)
                hour_selector.click()
                break
            except (NoSuchElementException, ElementNotInteractableException):
                print(f"Day {day} not found, scrolling...{i}")
                WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.CLASS_NAME,
                                                                               "tiktok-timepicker-time-scroll-container")))

                time_picker_container = driver.find_element(By.CLASS_NAME, "tiktok-timepicker-time-scroll-container")
                if i==0:
                    driver.execute_script("arguments[0].scrollTop = 0", time_picker_container)
                    time.sleep(1)
                else :driver.execute_script(f"arguments[0].scrollTop = (arguments[0].scrollHeight/{5-i})", time_picker_container)
                time.sleep(1)  # Wait for the scroll to take effect
            i=i+1

        print("done4")

        date_input.click()

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                        f"//span[contains(text(),{day})]/ancestor::div[@class='jsx-1793871833 day-span-container']")))

        day_selector = driver.find_element(By.XPATH,
                                     f"//span[contains(text(),{day})]/ancestor::div[@class='jsx-1793871833 day-span-container']")

        day_selector.click()

        print("done5")
        #****************************************** add random audio

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME,
                                                                        "TUXButton")))

        modify_video_button = driver.find_element(By.CLASS_NAME,
                                           "TUXButton"
                                           )
        modify_video_button.click()
        print("done6")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID,
                                                                        "favourite")))

        favourite_audio_button = driver.find_element(By.ID,
                                                  "favourite"
                                                  )
        favourite_audio_button.click()
        print("don7")
        # Find all the music card containers
        WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".jsx-915372485.music-card-container")))

        music_cards = driver.find_elements(By.CSS_SELECTOR, ".jsx-915372485.music-card-container")

        if music_cards:
            # random_card = music_cards[0]
            random_card = random.choice(music_cards)

            # Scroll into view to ensure the element is interactable
            driver.execute_script("arguments[0].scrollIntoView(true);", random_card)

            actions = ActionChains(driver)
            actions.move_to_element(random_card).perform()

            # Wait for the button to appear relative to the card
            try:
                # Wait for button within the card (note: adjust XPath as needed)
                utiliser_button = WebDriverWait(random_card, 10).until(
                    EC.visibility_of_element_located(
                        (By.XPATH, ".//button[contains(@class, 'TUXButton') and normalize-space()='Utiliser']")
                    )
                )
                utiliser_button.click()
                print("Clicked the 'Utiliser' button!")
            except Exception as e:
                print(f"Error clicking button: {e}")

        time.sleep(2)




    finally:
        # Close only the automation tab, leave Chrome running
        print("nothing closed")
        driver.quit()
        #driver.close()
        #driver.quit()


def move_to_posted_folder(video_path, posted_folder):
    # Move the uploaded video to the 'posted' folder
    if not os.path.exists(posted_folder):
        os.makedirs(posted_folder)
    video_name = os.path.basename(video_path)
    posted_video_path = os.path.join(posted_folder, video_name)
    shutil.move(video_path, posted_video_path)
    print(f"Moved {video_name} to posted folder.")


# if __name__ == "__main__":
#     #lets say that we want  to post 3 videos per day
#     for i in range(16,23):
#         hour = f"0{i}" if i < 10 else str(i)
#         upload_to_tiktok_studio(
#             video_path=r"C:\Users\soufa\OneDrive\Desktop\social media\scripts\tiktok_stuffs\english_test.mp4",
#             description="Uploaded via remote debugging!",
#             hour= hour,
#             day='8'
#         )
#         print(f"working for {hour}")

if __name__ == "__main__":
    #lets say that we want  to post 3 videos per day

    upload_to_tiktok_studio(
            video_path=r"C:\Users\soufa\OneDrive\Desktop\social media\scripts\tiktok_stuffs\english_test.mp4",
            description="Uploaded via remote debugging!",
            hour= '21',
            day='8'
        )





# if __name__ == "__main__":
#     # Specify the folder where the videos are stored
#     videos_folder = r"C:\Users\soufa\Downloads\LLLLL\lillyabellaa_w_audio_tt_automation_test"
#     posted_folder = os.path.join(videos_folder, "posted")
#
#     # Get a sorted list of video files in the folder (assuming they are MP4 files)
#     video_files = [f for f in os.listdir(videos_folder) if f.endswith(".mp4")]
#     video_files.sort()  # Sorting the files in lexicographical order (optional)
#
#     # Video counter to keep track of which video is being uploaded
#     video_index = 0  # Start with the first video
#
#     # Loop to schedule 3 videos per day for 10 days (total 30 videos)
#     for day in range(6, 16):  # 10 days
#         for video_num in range(1, 4):  # 3 videos per day
#             if video_index < len(video_files):  # Ensure there are videos left to upload
#                 # Get the first video file
#                 video_filename = video_files[video_index]
#                 video_path = os.path.join(videos_folder, video_filename)
#
#                 # Construct the hour for scheduling (for example, "16", "17", "18")
#                 hour = f"0{16 + video_num}" if 16 + video_num < 10 else str(16 + video_num)
#
#                 # Upload the video to TikTok
#                 upload_to_tiktok_studio(
#                     video_path=video_path,
#                     description="Uploaded via remote debugging!",
#                     hour=hour,
#                     day=str(day)
#                 )
#
#                 # Move the uploaded video to the 'posted' folder
#                 # move_to_posted_folder(video_path, posted_folder)
#
#                 print(f"Posted {video_filename} for day {day}, hour {hour}")
#
#                 # Increment video_index for the next video
#                 video_index += 1
#             else:
#                 print("No more videos left to upload.")
#                 break  # Exit the loop if there are no more videos
