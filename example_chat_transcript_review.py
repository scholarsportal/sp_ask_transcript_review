from base64 import encode
import pandas as pd
import ipdb, time
import logging
logging.basicConfig(filename='log.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

from review import generate_html_template_from_transcript, write_html_to_template 

if __name__ == '__main__':
    df = pd.read_excel("chatID_for_academic_year_2020-2021.xlsx")
    df = df[0:500]
    sections = [0, 60, 120, 180, 240, 300, 360, 420, 480, 500]
    counter = 0
    for number in sections:
        logging.info("Starting to retrieve chat from {}-{}".format(str(sections[counter]+1), str(sections[counter+1]-1)))
        print("Starting to retrive chat from {}-{}".format(str(sections[counter]+1), str(sections[counter+1]-1)))
        for item in range(0,1):
            output = generate_html_template_from_transcript(df.id[sections[counter]:sections[counter+1]])
            filePath = "./templates/chat-{0}-{1}.html".format(str(sections[counter]+1), str(sections[counter+1]-1))
            write_html_to_template(output, filePath)
        counter +=1
        time.sleep(5)