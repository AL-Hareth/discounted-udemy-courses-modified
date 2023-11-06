from flask import Flask, jsonify, render_template
import datetime

# These three imports are here for the code in the exec(), Don't listen to your linter
import threading
import time
from tqdm import tqdm

from reader import get_lines_array
from base import Udemy, Scraper

app = Flask(__name__)

scraper_dict: dict = {
    "Udemy Freebies": "uf",
    # "Tutorial Bar": "tb",
    "Real Discount": "rd",
    # "Course Vania": "cv",
    # "IDownloadCoupons": "idc",
    # "E-next": "en",
    "Discudemy": "du",
}

def create_scraping_thread(site: str, scraper):
    code_name = scraper_dict[site]
    exec(
        f"""
try:
    threading.Thread(target=scraper.{code_name},daemon=True).start()
    while scraper.{code_name}_length == 0:
        pass
    if scraper.{code_name}_length == -1:
        raise Exception("Error in: "+site)
    {code_name}_bar = tqdm(total=scraper.{code_name}_length-1, desc=site)
    prev_progress=0
    while not prev_progress == scraper.{code_name}_length-1:
        {code_name}_bar.update(scraper.{code_name}_progress-prev_progress)
        prev_progress = scraper.{code_name}_progress
        time.sleep(0.5)
    {code_name}_bar.close()
except Exception as e:
    e = scraper.{code_name}_error
    print(e)
    print("\\nUnknown Error in: "+site+" "+str(VERSION))
"""
)

last_updated = datetime.datetime.now()
updating = False

def update_courses():
    udemy = Udemy("cli")
    udemy.load_settings()
    login_error = True

    while login_error:
        try:
            email, password = udemy.settings["email"], udemy.settings["password"]
            udemy.manual_login(email, password)
            udemy.get_session_info()
            udemy.settings["email"], udemy.settings["password"] = email, password
            login_error = False
        except:
            return "Login error"
        udemy.save_settings()
    if udemy.is_user_dumb():
        return "Settings are empty"
    else:
        scraper = Scraper(udemy.sites)
        links = scraper.get_scraped_courses(create_scraping_thread, scraper)

        with open("output.txt", "w") as f:
            for link in links:
                f.write(link + "\n")

    global last_updated
    global updating
    last_updated = datetime.datetime.now()
    updating = False
    print("finished updating courses")

@app.route("/")
def index():
    global updating

    current_time = datetime.datetime.now()
    # Check that we are on the same day and we are more than 5 hours from the last update
    if last_updated.hour + 5 < current_time.hour:
        updating = True
        update_thread = threading.Thread(target=update_courses)
        update_thread.start()

        return render_template("loading.html")

    if updating:
        return render_template("loading.html")

    lines_array = get_lines_array("./output.txt")
    return render_template("index.html", courses=lines_array)

@app.route("/force-update")
def force_update():
    update_courses()
    return "Updated"

@app.route("/courses")
def get_courses():
    current_time = datetime.datetime.now()

    # Check that we are on the same day and we are more than 5 hours from the last update
    if last_updated.hour + 5 < current_time.hour:
        update_courses()

    lines_array = get_lines_array("./output.txt")
    return jsonify(lines_array)

if __name__ == "__main__":
    app.run(debug=True)
    # app.run(host="0.0.0.0") # Running on local network
