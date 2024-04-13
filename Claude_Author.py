import time
import re
import os
from ebooklib import epub
import base64
import requests
import json
from dotenv import load_dotenv
from collections import namedtuple
import logging

# Load environment variables from .env file
load_dotenv()

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
STABILITY_API_KEY = os.getenv('STABILITY_API_KEY')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Define custom exceptions
class MissingAPIKeyError(Exception):
    pass

class APIResponseError(Exception):
    pass

def remove_first_line(test_string):
    if test_string.startswith("Here") and test_string.split("\n")[0].strip().endswith(":"):
        return re.sub(r'^.*\n', '', test_string, count=1)
    return test_string

def generate_text(prompt, model="claude-3-haiku-20240307", max_tokens=2000, temperature=0.7):
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": "You are a world-class author. Write the requested content with great skill and attention to detail.",
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
        response.raise_for_status()
        response_text = response.json()['content'][0]['text']
        return response_text.strip()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error generating text: {e}")
        raise APIResponseError("Error occurred while generating text. Please try again later.")
    except KeyError:
        logging.error("Unexpected response format from the Anthropic API.")
        raise APIResponseError("Unexpected response from the Anthropic API.")

def generate_cover_prompt(plot):
    response = generate_text(f"Plot: {plot}\n\n--\n\nDescribe the cover we should create, based on the plot. This should be two sentences long, maximum.")
    return response

def generate_title(plot):
    response = generate_text(f"Here is the plot for the book: {plot}\n\n--\n\nRespond with a great title for this book. Only respond with the title, nothing else is allowed.")
    return remove_first_line(response)

def create_cover_image(plot, output_path='cover.png'):
    plot_prompt = generate_cover_prompt(plot)

    engine_id = "stable-diffusion-xl-beta-v2-2-2"
    api_host = os.getenv('API_HOST', 'https://api.stability.ai')
    api_key = STABILITY_API_KEY

    if api_key is None:
        raise MissingAPIKeyError("Stability API key is missing.")

    try:
        response = requests.post(
            f"{api_host}/v1/generation/{engine_id}/text-to-image",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "text_prompts": [
                    {
                        "text": plot_prompt
                    }
                ],
                "cfg_scale": 7,
                "clip_guidance_preset": "FAST_BLUE",
                "height": 768,
                "width": 512,
                "samples": 1,
                "steps": 30,
            },
        )
        response.raise_for_status()

        data = response.json()
        for i, image in enumerate(data["artifacts"]):
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(image["base64"]))
    except requests.exceptions.RequestException as e:
        logging.error(f"Error creating cover image: {e}")
        raise APIResponseError("Error occurred while creating the cover image. Please try again later.")
    except KeyError:
        logging.error("Unexpected response format from the Stability API.")
        raise APIResponseError("Unexpected response from the Stability API.")

def generate_chapter_title(chapter_content):
    response = generate_text(f"Chapter Content:\n\n{chapter_content}\n\n--\n\nGenerate a concise and engaging title for this chapter based on its content. Respond with the title only, nothing else.")
    return remove_first_line(response)

def create_epub(title, author, chapters, cover_image_path='cover.png'):
    book = epub.EpubBook()
    # Set metadata
    book.set_identifier('id123456')
    book.set_title(title)
    book.set_language('en')
    book.add_author(author)
    # Add cover image
    with open(cover_image_path, 'rb') as cover_file:
        cover_image = cover_file.read()
    book.set_cover('cover.png', cover_image)
    # Create chapters and add them to the book
    epub_chapters = []
    for i, chapter_content in enumerate(chapters):
        chapter_title = generate_chapter_title(chapter_content)
        chapter_file_name = f'chapter_{i+1}.xhtml'
        epub_chapter = epub.EpubHtml(title=chapter_title, file_name=chapter_file_name, lang='en')
        # Add paragraph breaks
        formatted_content = ''.join(f'<p>{paragraph.strip()}</p>' for paragraph in chapter_content.split('\n') if paragraph.strip())
        epub_chapter.content = f'<h1>{chapter_title}</h1>{formatted_content}'
        book.add_item(epub_chapter)
        epub_chapters.append(epub_chapter)

    # Define Table of Contents
    book.toc = (epub_chapters)

    # Add default NCX and Nav files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Define CSS style
    style = '''
    @namespace epub "http://www.idpf.org/2007/ops";
    body {
        font-family: Cambria, Liberation Serif, serif;
    }
    h1 {
        text-align: left;
        text-transform: uppercase;
        font-weight: 200;
    }
    '''

    # Add CSS file
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # Create spine
    book.spine = ['nav'] + epub_chapters

    # Save the EPUB file
    epub.write_epub(f'{title}.epub', book)

def generate_book(writing_style, book_description, num_chapters, max_chapter_length=256):
    logging.info("Generating plot outline...")
    plot_prompt = f"Create a detailed plot outline for a {num_chapters}-chapter book in the {writing_style} style, based on the following description:\n\n{book_description}\n\nEach chapter should be at least {max_chapter_length} paragraphs long."
    plot_outline = generate_text(plot_prompt)
    logging.info("Plot outline generated.")

    chapters = []
    for i in range(num_chapters):
        logging.info(f"Generating chapter {i+1}...")
        chapter_prompt = f"Previous Chapters:\n\n{' '.join(chapters)}\n\nWriting style: `{writing_style}`\n\nPlot Outline:\n\n{plot_outline}\n\nWrite chapter {i+1} of the book, ensuring it follows the plot outline and builds upon the previous chapters. The chapter should be at least {max_chapter_length} paragraphs long."
        chapter = generate_text(chapter_prompt, max_tokens=4000)
        chapters.append(remove_first_line(chapter))
        logging.info(f"Chapter {i+1} generated.")
        time.sleep(1)  # Add a short delay to avoid hitting rate limits

    logging.info("Compiling the book...")
    book = "\n\n".join(chapters)
    logging.info("Book generated!")

    return plot_outline, book, chapters

# User input
writing_style = input("Enter the desired writing style: ")
book_description = input("Enter a high-level description of the book: ")
num_chapters = int(input("Enter the number of chapters: "))
max_chapter_length = int(input("Enter the minimum number of paragraphs per chapter: "))

try:
    # Generate the book
    plot_outline, book, chapters = generate_book(writing_style, book_description, num_chapters, max_chapter_length)

    title = generate_title(plot_outline)

    # Save the book to a file
    with open(f"{title}.txt", "w") as file:
        file.write(book)

    create_cover_image(plot_outline)

    # Create the EPUB file
    create_epub(title, 'AI', chapters, 'cover.png')

    logging.info(f"Book saved as '{title}.txt'.")
except MissingAPIKeyError as e:
    logging.error(e)
    print("Error: Please make sure the Anthropic and Stability API keys are set in the .env file.")
except APIResponseError as e:
    logging.error(e)
    print("Error: An issue occurred while generating the content. Please try again later.")
except Exception as e:
    logging.error(f"Unexpected error: {e}")
    print("An unexpected error occurred. Please check the logs for more information.")