# Claude_Author: AI-Powered Book Generation

This project uses the power of artificial intelligence to generate complete book drafts, including cover images, based on user input and preferences. 

## Features

* **AI-driven content creation:** Leverages the Anthropic API to generate the book's plot, chapters, and even chapter titles, based on user-provided writing style and book description.
* **Automatic cover image generation:** Employs the Stability API to create a unique cover image that reflects the book's plot and themes.
* **EPUB export:**  Generates the finished book as an EPUB file, ready for reading on various e-readers or ebook platforms.
* **Customizable:** Allows users to specify the writing style, provide a high-level book description, and determine the number of chapters.

## Technologies Used

* **Python:** The primary programming language for the project.
* **Anthropic API:**  Provides AI-powered text generation capabilities.
* **Stability API:**  Enables the creation of AI-generated images based on text prompts.
* **EbookLib:** A Python library for generating EPUB files. 
* **python-dotenv:** Used to manage environment variables for API keys.

## Installation and Setup

1. **Clone the repository:**
    ```bash
    git clone https://github.com/EDDARI/Claude_Author.git
   ```

2. **Install dependencies:**
   ```bash
   pip install EbookLib
   ```

3. **Set up API keys:** 
    - Create a `.env` file in the project's root directory.
    - Add your Anthropic API key and Stability API key to the `.env` file in the following format:

    ```bash
    ANTHROPIC_API_KEY=your_anthropic_api_key
    STABILITY_API_KEY=your_stability_api_key
    ```

## Usage

1. Run the `Claude_Author.py` script.
2. Follow the prompts to input the desired writing style, book description, and number of chapters.
3. The script will generate the book content, create a cover image, and save the final output as an EPUB file with the generated title (e.g., `MyBookTitle.epub`).

## Notes

* Be mindful of API rate limits, especially when generating longer books.
* Consider implementing content filtering mechanisms for the AI-generated content.
* Explore the code and experiment with different options to customize the book generation process.

## Disclaimer

This project is intended for experimental and creative purposes.  The quality and suitability of the generated content may vary, and it's recommended to review and edit the output as needed.
