from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai
import os
from dotenv import load_dotenv
import PyPDF2
import io
from datetime import datetime
import re
import docx
import fitz  # PyMuPDF

load_dotenv()

# Update the environment variable name to match the .env file
GOOGLE_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

def extract_text_from_pdf(pdf_file):
    try:
        # Use PyMuPDF to extract text
        doc = fitz.open(stream=pdf_file, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF with PyMuPDF: {str(e)}")
        return None

def extract_text_from_docx(docx_file):
    try:
        doc = docx.Document(docx_file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {str(e)}")
        return None

def extract_info_from_cv(cv_text):
    # Check if cv_text is None or empty
    if not cv_text:
        return {}
        
    # Initialize extracted information
    info = {
        'full_name': '',
        'email': '',
        'phone': '',
        'address': '',
        'skills': '',
        'experience': ''
    }
    
    try:
        # Extract email
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        email_match = re.search(email_pattern, cv_text)
        if email_match:
            info['email'] = email_match.group(0)
        
        # Extract phone number (various formats)
        phone_pattern = r'(?:(?:\+\d{1,3})?[-.\s]?)?(?:\(?\d{2,3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}'
        phone_match = re.search(phone_pattern, cv_text)
        if phone_match:
            info['phone'] = phone_match.group(0)
        
        # Extract name (look for capitalized words at the start)
        name_pattern = r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+'
        name_match = re.search(name_pattern, cv_text)
        if name_match:
            info['full_name'] = name_match.group(0)
        
        # Extract address (look for common address patterns)
        address_pattern = r'\d+\s+\w+\s+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Lane|Ln|Drive|Dr|Court|Ct|Square|Sq|Loop|Lp|Terrace|Ter|Place|Pl|Trail|Trl|Parkway|Pkwy|Commons|Cmns)\b.*'
        address_match = re.search(address_pattern, cv_text, re.IGNORECASE)
        if address_match:
            info['address'] = address_match.group(0)
        
        # Extract skills (look for common skill indicators)
        skills_section = re.search(r'(?i)(?:skills|expertise|competencies)(.*?)(?=\n\n|\Z)', cv_text, re.DOTALL)
        if skills_section:
            info['skills'] = skills_section.group(1).strip()
        
        # Extract experience
        experience_section = re.search(r'(?i)(?:experience|work history|professional experience)(.*?)(?=\n\n|\Z)', cv_text, re.DOTALL)
        if experience_section:
            info['experience'] = experience_section.group(1).strip()
        
        return info
    except Exception as e:
        print(f"Error extracting info from CV: {str(e)}")
        return {}

def home(request):
    return render(request, 'generator/index.html')

@csrf_exempt
def generate_cover_letter(request):
    if request.method == 'POST':
        # Check if this is just a CV processing request or a full cover letter generation
        is_cv_processing = 'cv_file' in request.FILES and len(request.POST) <= 1  # Only CSRF token in POST
        
        try:
            # Get CV file if uploaded
            cv_text = ""
            cv_info = {}
            
            if 'cv_file' in request.FILES:
                cv_file = request.FILES['cv_file']
                print(f"Processing file: {cv_file.name}, size: {cv_file.size}, content_type: {cv_file.content_type}")
                
                # Store file in memory
                file_content = cv_file.read()
                
                # Get file extension
                file_extension = cv_file.name.lower().split('.')[-1]
                print(f"File extension: {file_extension}")
                
                if file_extension == 'pdf':
                    try:
                        # Create a new BytesIO object from the content
                        file_buffer = io.BytesIO(file_content)
                        cv_text = extract_text_from_pdf(file_buffer)
                        print(f"Extracted PDF text length: {len(cv_text) if cv_text else 0}")
                        
                        if not cv_text:
                            print("Could not extract text from PDF")
                            if is_cv_processing:
                                return JsonResponse({
                                    'status': 'error',
                                    'message': 'Could not extract text from PDF. The file may be corrupted or password-protected.'
                                })
                    except Exception as e:
                        print(f"PDF extraction error: {str(e)}")
                        if is_cv_processing:
                            return JsonResponse({
                                'status': 'error',
                                'message': f'Error processing PDF: {str(e)}'
                            })
                elif file_extension == 'txt':
                    try:
                        cv_text = file_content.decode('utf-8', errors='ignore')
                        print(f"Extracted TXT text length: {len(cv_text)}")
                    except Exception as e:
                        print(f"TXT extraction error: {str(e)}")
                        if is_cv_processing:
                            return JsonResponse({
                                'status': 'error',
                                'message': f'Error processing text file: {str(e)}'
                            })
                elif file_extension == 'docx':
                    try:
                        # Create a new BytesIO object from the content
                        file_buffer = io.BytesIO(file_content)
                        cv_text = extract_text_from_docx(file_buffer)
                        print(f"Extracted DOCX text length: {len(cv_text) if cv_text else 0}")
                        
                        if not cv_text:
                            print("Could not extract text from DOCX")
                            if is_cv_processing:
                                return JsonResponse({
                                    'status': 'error',
                                    'message': 'Could not extract text from DOCX file.'
                                })
                    except Exception as e:
                        print(f"DOCX extraction error: {str(e)}")
                        if is_cv_processing:
                            return JsonResponse({
                                'status': 'error',
                                'message': f'Error processing DOCX file: {str(e)}'
                            })
                else:
                    print(f"Unsupported file extension: {file_extension}")
                    if is_cv_processing:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Unsupported file format. Please upload a PDF, DOCX, or TXT file.'
                        })
                
                # Extract information from CV
                if cv_text:
                    cv_info = extract_info_from_cv(cv_text)
                    print(f"Extracted CV info: {cv_info}")
                    
                    # If this is just a CV processing request, return the extracted info
                    if is_cv_processing:
                        return JsonResponse({
                            'status': 'success',
                            'cv_info': cv_info
                        })
                elif is_cv_processing:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Could not extract any text from the uploaded file.'
                    })
            
            # If no CV file or this is a full cover letter request, proceed with generation
            
            # Get form data, use CV info if available
            full_name = request.POST.get('full_name', cv_info.get('full_name', ''))
            email = request.POST.get('email', cv_info.get('email', ''))
            phone = request.POST.get('phone', cv_info.get('phone', ''))
            address = request.POST.get('address', cv_info.get('address', ''))
            job_title = request.POST.get('job_title', '')
            company_name = request.POST.get('company_name', '')
            hiring_manager = request.POST.get('hiring_manager', '')
            company_address = request.POST.get('company_address', '')
            letter_date = request.POST.get('letter_date', '')
            skills = request.POST.get('skills', cv_info.get('skills', ''))
            experience = request.POST.get('experience', cv_info.get('experience', ''))
            
            # Configure the model
            model = genai.GenerativeModel('gemini-1.5-pro')
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
            
            # Format the date
            formatted_date = ""
            if letter_date:
                date_obj = datetime.strptime(letter_date, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%B %d, %Y')
            
            # Create the prompt
            prompt = f"""Generate a professional cover letter with the following information:

Personal Information:
- Name: {full_name}
- Email: {email}
- Phone: {phone}
- Address: {address}

Company Information:
- Job Title: {job_title}
- Company Name: {company_name}
- Hiring Manager: {hiring_manager}
- Company Address: {company_address}
- Date: {formatted_date}

Skills and Experience:
{skills}
{experience}

CV Content (if provided):
{cv_text}

Format the cover letter professionally with:
1. Proper date (use the provided date: {formatted_date})
2. Sender's address
3. Company address
4. Salutation
5. Three well-structured paragraphs:
   - Introduction and interest in the position
   - Relevant skills and experience
   - Closing and call to action
6. Professional closing
7. Signature line

Make the cover letter concise, engaging, and tailored to the specific job and company. Use formal business language and maintain a professional tone throughout."""

            # Generate the cover letter
            response = model.generate_content(prompt)
            
            # Format the response
            cover_letter = response.text
            
            return JsonResponse({
                'status': 'success',
                'cover_letter': cover_letter,
                'cv_info': cv_info  # Return extracted CV info to pre-fill form
            })
            
        except Exception as e:
            print(f"Error generating cover letter: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })
