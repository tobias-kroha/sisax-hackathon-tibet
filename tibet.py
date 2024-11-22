#! /usr/bin/env python

from datetime import datetime
import glob
import aisisax.object_detection.lsa_interface as aisax_object_detection
import aisisax.llm.openai_connector as aisax_openai
import logging as l

import pandas as pd
import json
df = pd.DataFrame()

# Create columns filename, stempel, seitenzahl, chinesische_zahl, arabische_zahl, illustrationen, illustrationen_beschriftung
df = pd.DataFrame(columns=['filename', 'timestamp','arabic_numeral_present', 'arabic_numeral_int', 'illustration_present',])

# configure logging
l.basicConfig(level=l.INFO)

# traverse all files in the assets directory
for pImage in glob.glob("assets/**/*.jpg", recursive=True):
    l.info(f"Processing {pImage}")
    
    result = aisax_openai.generate_multimodal_answer("""You are an expert for interpreting Tibetan manuscripts. 
                                               Attached you will find an image of a tibetan manuscript. 
                                               Answer the following questions and respond as a pure JSON object the following format:
                                               {
                                               "arabic_numeral_present": "bool (Does the image contain an Arabic numeral?)",
                                               "arabic_numeral_int": "Integer (If there is an Arabic numeral, which one?)",
                                               "illustration_present": "bool (Does the image contain an illustration?)",
                                               "illustration_with_text_below": "bool (Does the image contain an illustration with a caption?)",
                                               "chinese_char_present": "bool (Are there chinese characters?)",
                                               "chinese_char_position": "char (Where are the chinese characters? Say 'L' for left, 'R' for right!)",
                                               "box_present": "char (Is there a frame around the Text? Say 'N' for none, 'R' for Red and \"B\" for black!)",
                                               }

                                               """, image_path=pImage)

    # Log the raw result for debugging
    l.debug(f"Raw result before processing:\n{result}")

    # Remove first and last line
    result = result.split("\n")[1:-1]
    result = "\n".join(result)

    # Log the processed result
    l.debug(f"Processed result for JSON parsing:\n{result}")

    try:
        result = json.loads(result)
    except json.JSONDecodeError as e:
        l.error(f"JSON decoding failed for {pImage}: {e}")
        l.error(f"Result content:\n{result}")
        continue  # Skip to the next image

    # Strip "assets/" from the beginning of the filename
    result["filename"] = pImage.replace("assets/", "")
    result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Append the result to the dataframe
    df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)

print(df.to_excel("tibet.xlsx"))
