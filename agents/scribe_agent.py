# agents/scribe_agent.py
import io
import base64
from typing import List, Dict, Any
from google.cloud import vision
from google.cloud import speech
from google.cloud import storage
import vertexai
from vertexai.generative_models import GenerativeModel
import PyPDF2

class ScribeAgent:
    def __init__(self, project_id: str, region: str):
        self.project_id = project_id
        self.region = region
        self.vision_client = vision.ImageAnnotatorClient()
        self.speech_client = speech.SpeechClient()
        self.storage_client = storage.Client(project=project_id)
        
        # Initialize Gemini
        vertexai.init(project=project_id, location=region)
        self.gemini_model = GenerativeModel("gemini-1.5-pro")
    
    async def process_document(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Process different document types"""
        if file_type.lower() == 'pdf':
            return await self._process_pdf(file_path)
        elif file_type.lower() in ['jpg', 'jpeg', 'png']:
            return await self._process_image(file_path)
        elif file_type.lower() in ['mp3', 'wav', 'm4a']:
            return await self._process_audio(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    async def _process_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text from PDF using vision API for images and PyPDF2 for text"""
        extracted_text = []
        
        # Try text extraction first
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text.strip():
                        extracted_text.append(text)
        except Exception as e:
            print(f"Text extraction failed: {e}")
        
        # If no text found, use OCR
        if not extracted_text:
            extracted_text = await self._ocr_pdf(file_path)
        
        # Use Gemini to clean and structure the text
        combined_text = "\n".join(extracted_text)
        cleaned_text = await self._clean_text_with_gemini(combined_text)
        
        return {
            "content_type": "document",
            "raw_text": combined_text,
            "cleaned_text": cleaned_text,
            "page_count": len(extracted_text)
        }
    
    async def _ocr_pdf(self, file_path: str) -> List[str]:
        """Use Cloud Vision API for OCR"""
        # Convert PDF to images and process with Vision API
        # This is a simplified version - you'd need pdf2image for production
        with open(file_path, "rb") as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        response = self.vision_client.text_detection(image=image)
        texts = response.text_annotations
        
        if texts:
            return [texts[0].description]
        return []
    
    async def _process_image(self, file_path: str) -> Dict[str, Any]:
        """Process image with OCR"""
        with open(file_path, "rb") as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        response = self.vision_client.text_detection(image=image)
        
        if response.text_annotations:
            extracted_text = response.text_annotations[0].description
            cleaned_text = await self._clean_text_with_gemini(extracted_text)
            
            return {
                "content_type": "image",
                "raw_text": extracted_text,
                "cleaned_text": cleaned_text
            }
        
        return {"content_type": "image", "raw_text": "", "cleaned_text": ""}
    
    async def _process_audio(self, file_path: str) -> Dict[str, Any]:
        """Process audio with Speech-to-Text"""
        with open(file_path, "rb") as audio_file:
            content = audio_file.read()
        
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
            enable_speaker_diarization=True,
            diarization_speaker_count=2,
            enable_automatic_punctuation=True
        )
        
        response = self.speech_client.recognize(config=config, audio=audio)
        
        transcript_parts = []
        for result in response.results:
            transcript_parts.append(result.alternatives[0].transcript)
        
        full_transcript = " ".join(transcript_parts)
        cleaned_transcript = await self._clean_text_with_gemini(full_transcript)
        
        return {
            "content_type": "audio",
            "raw_text": full_transcript,
            "cleaned_text": cleaned_transcript,
            "speaker_info": self._extract_speaker_info(response)
        }
    
    async def _clean_text_with_gemini(self, text: str) -> str:
        """Use Gemini to clean and structure extracted text"""
        prompt = f"""
        Clean and structure the following extracted text from a startup pitch deck or call transcript.
        Remove OCR errors, fix formatting, and make it readable while preserving all important information.
        
        Text to clean:
        {text}
        
        Return only the cleaned, well-formatted text.
        """
        
        response = await self.gemini_model.generate_content_async(prompt)
        return response.text
    
    def _extract_speaker_info(self, response) -> List[Dict]:
        """Extract speaker diarization information"""
        speakers = []
        for result in response.results:
            for word in result.alternatives[0].words:
                if hasattr(word, 'speaker_tag'):
                    speakers.append({
                        "word": word.word,
                        "speaker": word.speaker_tag,
                        "start_time": word.start_time.total_seconds(),
                        "end_time": word.end_time.total_seconds()
                    })
        return speakers
