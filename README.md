# AI Cover Letter Generator

A web application that generates professional cover letters using AI. Built with Django and Google's Gemini API.

## Features

- Modern, responsive UI using Tailwind CSS
- AI-powered cover letter generation using Google's Gemini
- Easy-to-use form interface
- Copy to clipboard functionality
- Loading states and error handling

## Setup Instructions

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
   You can get your API key from: https://makersuite.google.com/app/apikey

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

7. Open your browser and navigate to `http://localhost:8000`

## Usage

1. Fill in the form with:
   - Job Title
   - Company Name
   - Your Skills
   - Your Experience

2. Click "Generate Cover Letter"
3. Wait for the AI to generate your personalized cover letter
4. Use the "Copy to Clipboard" button to copy the generated text

## Technologies Used

- Django
- Google Gemini API
- Tailwind CSS
- JavaScript (Vanilla)
- HTML5 
