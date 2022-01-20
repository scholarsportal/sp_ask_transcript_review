from base64 import encode
import pandas as pd

from review import generate_html_template_from_transcript, write_html_to_template 

if __name__ == '__main__':
    df = pd.read_excel(filepath="chatID_for_academic_year_2019-2020.xlsx", encode="utf-8")
    output = generate_html_template_from_transcript(df.ids.unique())
    filePath = "./templates/ask.html"
    write_html_to_template(output, filePath)