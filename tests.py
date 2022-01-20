import unittest
import pendulum
from lh3.api import *
from review import (
    generate_html_template_from_transcript, 
    write_html_to_template,
    retrieve_transcript,
    get_transcript,
    get_wait_and_duration,
    get_chat_metadata_for_header,
    line_by_line
)
import ipdb

class TestStringMethods(unittest.TestCase):

    def test_retrieve_transcript(self):
        client = Client()
        chat_id = int(2956045)
        transcript_metadata = client.one("chats", chat_id).get()
        transcript = retrieve_transcript(transcript_metadata, chat_id)
        #ipdb.set_trace()
        self.assertEqual(transcript[0].get('chat_id'), 2956045)

    def test_get_transcript(self):
        result = get_transcript(2956045)
        self.assertEqual(result[0].get('chat_id'), 2956045)

    def test_check_if_template_file_exist(self):
        filePath = "./templates/index.html"
        self.assertEqual(os.path.exists(filePath), True)

    def test_get_wait_and_duration(self):
        client = Client()
        this_chat = client.one("chats", 2956045).get()
        started = pendulum.parse(this_chat.get("started"))
        wait, duration = get_wait_and_duration(this_chat, started)
        self.assertEqual(wait.seconds, 54)
