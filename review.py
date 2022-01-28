# python 3.6+

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from lh3.api import *
from datetime import datetime
from bs4 import BeautifulSoup
import pendulum
from jinja2 import Environment, FileSystemLoader
import os
import datetime
import logging
from uuid import uuid4
import pandas as pd

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

root = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(root, "templates")
env = Environment(loader=FileSystemLoader(templates_dir))
template = env.get_template("index.html")


def write_html_to_template(output, filePath):
    """create an HTML file using the default HTML template

    Args:
        output ([string]):  HTML content
    """
    # if file exist
    
    if os.path.exists(filePath):
        os.remove(filePath)
        with open(filePath, "w", encoding="utf-8") as file:
            file.write(str(output))
    else:
        with open(filePath, "w", encoding="utf-8") as file:
            file.write(str(output))



def retrieve_transcript(transcript_metadata, chat_id):
    """Return a Transcript (dict) containing metadata
        The 'message' is the raw Transcript

    Args:
        transcript_metadata (dict): the Chat Transcript from LibraryH3lp
        chat_id (int): The chat ID

    Returns:
        dict: Return a Transcript (dict) containing metadata
    """
    queue_id = transcript_metadata["queue_id"]
    guest = transcript_metadata["guest"].get("jid")
    get_transcript = (
        transcript_metadata["transcript"] or "<div>No transcript found</div>"
    )
    soup = BeautifulSoup(get_transcript, "html.parser")
    divs = soup.find_all("div")
    transcript = list()
    counter = 1
    for div in divs[1::]:
        try:
            transcript.append(
                {
                    "chat_id": chat_id,
                    "message": str(div),
                    "counter": counter,
                    "chat_standalone_url": "https://ca.libraryh3lp.com/dashboard/queues/{0}/calls/REDACTED/{1}".format(
                        queue_id, chat_id
                    ),
                    "guest": guest,
                }
            )
            counter += 1
        except:
            pass
    return transcript


def get_transcript(chat_id):
    """Get the chat info from LibraryH3lp, then retrieve the Transcript out of the Chat.

    Args:
        chat_id (int): A single Chat ID

    Returns:
        list(dict): trancript + metadata
    """
    client = Client()
    chat_id = int(chat_id)
    transcript_metadata = client.one("chats", chat_id).get()
    transcript = retrieve_transcript(transcript_metadata, chat_id)
    queue_name = transcript_metadata.get("queue").get("name")
    started_date = parse(transcript_metadata.get("started")).strftime("%Y-%m-%d")
    logging.info("Retrieve transcript for {}".format(str(chat_id)))
    print("Retrieve transcript for {}".format(str(chat_id)))
    return transcript




def get_wait_and_duration(this_chat, started):
    """from the Chat time related metadata... 

    Args:
        this_chat (int): Chat metadata

    Returns:
        list: return the Wait Time and Duration Time of the Chat
    """
    ended = None
    accepted = None
    wait = None
    duration = None
    try:
        ended = pendulum.parse(this_chat.get("ended"))
    except:
        pass
    try:
        accepted = pendulum.parse(this_chat.get("accepted"))
    except:
        pass
    try:
        wait = accepted - started
    except:
        pass
    try:
        duration = ended - accepted
    except:
        pass

    return [wait, duration]

def get_chat_metadata_for_header(transcript, duration, wait):
    """Will generate the section that comes before the transcript on the HTML page. 
        It contains metadata information such as Duration and Wait Time of the chat 

    Args:
        transcript ([type]): [description]
        duration ([type]): [description]
        wait ([type]): [description]

    Returns:
        string: returning HTML
    """
    
    try:
        duration_in_second = str(datetime.timedelta(0, duration.seconds))
    except:
        duration_in_second = 0
    try:
        wait_in_second = str(datetime.timedelta(0, wait.seconds))
    except:
        wait_in_second = 0
    metadata_html = """
            <div class="container" style="float: right;overflow:hidden;">
            <ul style="overflow:hidden;">
            <li><em> Duration</em> : {0}</li>
            <li> <em>Wait</em>    : {1} </li>
            <li><a href="{2}" target="_blank">{3}</a></li>
            </ul>
        </div>
    """.format(
        duration_in_second
        ,
        wait_in_second
        ,
        transcript[0].get("chat_standalone_url"),
        transcript[0].get("chat_standalone_url"),
    )
    return metadata_html

def line_by_line(transcript, previous_timestamp,  operator, html_template, this_queue):
    """Parse each line of the Transcript

    Args:
        transcript (string): [description]
        previous_timestamp (string): [description]
        operator (string): [description]
        html_template (string): [description]
        this_queue (string): [description]

    Returns:
        [type]: HTML Template that will be written to the final file.
    """
    for message in transcript:
        line_to_add = message.get("message")
        try:
            if previous_timestamp == None:
                previous_timestamp = datetime.time.fromisoformat(
                    (line_to_add[5:10]).strip()
                )
            current_timestamp = datetime.time.fromisoformat((line_to_add[5:10]).strip())
            previous_timestamp = datetime.datetime(
                2011, 11, 11, previous_timestamp.hour, previous_timestamp.minute
            )
            current_timestamp = datetime.datetime(
                2011, 11, 11, current_timestamp.hour, current_timestamp.minute
            )
            timedelta_obj = relativedelta(previous_timestamp, current_timestamp)
        except:
            pass
        if timedelta_obj.minutes >= 5:
            line_to_add = line_to_add.replace(
                current_timestamp,
                """<b style="color:white; background-color:tomato">{0}} [+5] </b>""".format(
                    current_timestamp
                ),
            )
        if operator:
            line_to_add = line_to_add.replace(operator, "operator", 1)
            # import sys; sys.exit()
            # print(line_to_add)
        line_to_add = line_to_add.replace(
            this_queue, "system@chat.ca.libraryh3lp.com", 1
        )
        logging.info("Adding a line")
        html_template.append("<tr><td>" + line_to_add + "</td></tr>")
    return html_template


def generate_html_template_from_transcript(chat_ids, filePath, chat_per_page):
    """This is the main function of the script. 

    Args:
        chat_ids (list): A list of Chat IDS

    Returns:
        string: the complete HTML
    """
    html_template = []
    counter = 1
    total_chat_so_far_on_this_page = 0
    tracking_guest_id = []

    for chat in chat_ids[0::]:
        try:
            client = Client()
            this_chat = client.one("chats", chat).get()
            try:
                operator = this_chat.get("operator").get("name")
            except:
                operator = "None"
            guest_id = this_chat.get('guest').get('jid')
            chat_id = this_chat.get('guest').get('id')
            
            tracking_guest_id.append({"guestID":guest_id, "chat_id":chat_id })

            this_queue = this_chat.get("queue").get("name") + "@chat.ca.libraryh3lp.com"
            started = pendulum.parse(this_chat.get("started"))
            

            wait, duration = get_wait_and_duration(this_chat, started)
            previous_timestamp = None
            

            divider = """<div style="background-color: rgb(209, 241, 231); padding:20px 0px; margin:50px 0"></div>"""
            row_bg_and_h2 = """<div class='row bg-light '><h2 class="text-center"> Chat #"""
            if (counter % 2) == 0:
                row_bg_and_h2 = """<div class='row bg-light-blue'><h2 class="text-center"> Chat #"""
            transcript = get_transcript(chat)
            metadata_html = get_chat_metadata_for_header(transcript, duration, wait)

            html_template.append(
                row_bg_and_h2
                + str(counter)
                + "</h2>"
                + metadata_html
                + '<div class="table-responsive">'
                + '<table class="table mb-0 table-hover">'
            )
            html_template = line_by_line(transcript, previous_timestamp, operator, html_template, this_queue)

            html_template.append("</table></div></div>" + divider)
            # add HTML table for Metadata (or prepend)
            counter += 1

            if counter == chat_per_page+1:
                html = "".join(html_template)
                output = template.render(transcript=html)
                random_string = str(uuid4())[0:3]
                filename = filePath + "-" + random_string 
                print("printint a file: {0}".format(filename))
                write_html_to_template(output, filename+".html")
                df = pd.DataFrame(tracking_guest_id)
                df.to_excel(filename+".xlsx")
                print("printint a file: {0}".format(filename+".xlsx"))
                
                html_template = []
                tracking_guest_id = []
                counter = 1
        except:
            pass






if __name__ == '__main__':
    chat_ids = [2624301, 2666584, 2956045, 2544399]
    filePath = "./output/ask"
    chat_per_page = 2
    generate_html_template_from_transcript(chat_ids, filePath, chat_per_page)
    
    
    

