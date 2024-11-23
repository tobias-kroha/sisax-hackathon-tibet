#! /usr/bin/env python

from datetime import datetime
import glob
import aisisax.object_detection.lsa_interface as aisax_object_detection
import aisisax.llm.openai_connector as aisax_openai
import logging as l

import pandas as pd
import json
df = pd.DataFrame()

def process_images(image_paths):
    # Move the DataFrame creation and processing logic into this function
    df = pd.DataFrame(columns=['filename', 'timestamp', 'ppn', 'page_number', 
                             'arabic_numeral_present', 'arabic_numeral_int', 
                             'illustration_present', 'illustration_position', 
                             'illustration_with_text_below', 'tibetian_page_number', 
                             'chinese_char_present', 'chinese_page_number', 'box_present'])
    
    # configure logging
    l.basicConfig(level=l.INFO)

    # traverse all files in the assets directory, limit to 10 files
    for pImage in image_paths:
        l.info(f"Processing {pImage}")

        # extract ppl and page number from the filename
        ppn = pImage.split("/")[1]
        page_number = pImage.split("/")[2].split("_")[0]
        
        
        result=aisax_openai.generate_multimodal_answer("""You are an expert for interpreting Tibetan manuscripts. 
                                                   Attached you will find an image of a tibetan manuscript. 
                                                   Answer the following questions and respond as a pure JSON object the following format:
                                                   {
                                                   "chinese_char_present": "bool (Is there at least one Chinese character or number on the image?)",
                                                   "chinese_page_number": "bool (Does the image contain at least one chinese character or number, that is vertical oriented and is on the right side of the image outside of the tibet?)",
                                                   "arabic_numeral_present": "bool (Does the image contain an Arabic numeral?)",
                                                   "arabic_numeral_int": "Integer (If there is an Arabic numeral, which one?)",
                                                   "illustration_present": "bool (Does the image contain an illustration?)",   
                                                   "illustration_position": "string (If the image contains not an illustration say " ", else return the postion and say depending of the ilustrated area either left say 'l', either right say 'r', either center say 'c', either left AND right say 'lr', either left AND centered AND right say 'lcr', either left AND centered say 'lc', either right AND centered say 'rc'",
                                                   "illustration_with_text_below": "bool (Does the image contain an illustration with a caption?)",
                                                   "tibetian_page_number": "bool (Does the image contain a tibetian characters, that are vertical oriented and left aligned. If so say 'true', 'false' otherwise.)",
                                                   "box_present": "char (Is there a frame around the Text? Say 'N' for none, 'R' for Red and "B" for black!)",
                                                   }

                                                   """, image_path=pImage, temperature=0.5)

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
        result["ppn"] = ppn
        result["page_number"] = page_number

        # Append the result to the dataframe
        df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)

    return df

def main():
    # Process images from assets directory
    image_paths = glob.glob("assets/**/*.jpg", recursive=True)[:50]
    df = process_images(image_paths)
    
    # Save to Excel
    df.to_excel("tibet.xlsx")
    
    # Generate HTML output
    # Create an HTML table of dataframe df, including the images, link to them with local urls with the prefix "assets/"

    # Define a formatter function for the 'filename' column to include images and links
    def image_formatter(filename):
        return f'<a href="assets/{filename}"><img src="assets/{filename}" alt="{filename}""></a>'

    # Apply the formatter to the 'filename' column
    df['filename'] = df['filename'].apply(image_formatter)

    # Optionally, rename the 'filename' column to 'Image' for clarity in the HTML table
    df.rename(columns={'filename': 'Image'}, inplace=True)

    # Move the 'timestamp' column to the last position
    df['timestamp'] = df.pop('timestamp')

    # Convert the DataFrame to an HTML table
    html_table = df.to_html(escape=False, index=False)

    # Wrap the table in basic HTML structure
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tibetan Manuscript Analysis</title>
        <style>
            table {{
                width: 100%;
                border-collapse: collapse;
                max-height: 400px; /* Höhe des Containers */
                overflow-y: auto; /* Scrollen aktivieren */
                border: 1px solid #ccc; /* Optional: Rahmen */
            }}
            th, td {{
                border: 1px solid #dddddd;
                text-align: center;
                padding: 4px;
                font-size: 10px;
                font-family: Arial, sans-serif;
            }}
            th {{
                background-color: #f2f2f2;
                position: sticky; /* Fixiert den Kopf */
                top: 0; /* Bleibt oben */
                background-color: #f9f9f9; /* Hintergrundfarbe */
                z-index: 2; /* Sicherstellen, dass die th-Ebene über den td liegt */
                border: 1px solid #ddd; /* Optional: Rahmen */
                padding: 8px;
            }}
            img {{
                width: 250px;
                height: auto;
            }}
        </style>
    </head>
    <body>
        <h2>Tibetan Manuscript Analysis</h2>
        {html_table}
    </body>
    </html>
    """

    # Save the HTML content to a file
    with open("tibet.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("HTML table has been created and saved to 'tibet.html'.")

if __name__ == "__main__":
    main()


