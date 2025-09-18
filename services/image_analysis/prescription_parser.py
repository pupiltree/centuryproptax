"""
Prescription Image Analysis using Gemini-2.5-Pro
Parses prescription images to extract medical test information and patient details.
"""

import asyncio
import base64
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from PIL import Image
from io import BytesIO
import structlog
import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
import google.generativeai as genai

logger = structlog.get_logger()

@dataclass
class PrescriptionData:
    """Parsed prescription data structure."""
    patient_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    prescribed_tests: List[str] = None
    doctor_name: Optional[str] = None
    hospital_clinic: Optional[str] = None
    prescription_date: Optional[str] = None
    additional_instructions: Optional[str] = None
    confidence_score: Optional[float] = None
    missing_fields: List[str] = None

    def __post_init__(self):
        if self.prescribed_tests is None:
            self.prescribed_tests = []
        if self.missing_fields is None:
            self.missing_fields = []


class PrescriptionImageParser:
    """Medical prescription image parser using Gemini-2.5-Pro for advanced image analysis."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        
        # Configure Google GenAI directly for proper image handling
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        
        # Initialize Gemini model directly for image analysis
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        
        # System prompt for prescription analysis
        self.system_prompt = self._get_prescription_analysis_prompt()
    
    def _get_prescription_analysis_prompt(self) -> str:
        """Comprehensive prompt for prescription image analysis."""
        return """You are an expert medical prescription analyzer. Your task is to carefully analyze prescription images and extract relevant information for medical test booking.

ANALYSIS GUIDELINES:
1. **Medical Test Identification**: Look for diagnostic tests, lab tests, imaging studies, or health screenings
2. **Patient Information**: Extract name, age, gender if clearly visible
3. **Doctor Information**: Identify prescribing doctor and clinic/hospital
4. **Date Information**: Find prescription date or consultation date
5. **Special Instructions**: Note any specific preparation instructions or urgency

ACCURACY REQUIREMENTS:
- Only extract information that is clearly visible and legible
- Mark fields as "unclear" if handwriting is illegible
- Distinguish between medications (ignore) and diagnostic tests (extract)
- Be conservative - better to say "not visible" than guess

MEDICAL TEST CATEGORIES TO IDENTIFY:
- Blood Tests: CBC, glucose, HbA1c, lipid profile, liver function, kidney function, thyroid tests
- Imaging: X-ray, ultrasound, CT scan, MRI, mammography
- Specialized Tests: ECG, stress test, bone density, colonoscopy, endoscopy
- Health Screenings: diabetes screening, cardiac assessment, cancer screening

RESPONSE FORMAT:
Return a JSON object with this exact structure:
{
    "patient_name": "string or null",
    "age": "number or null", 
    "gender": "male/female/other or null",
    "prescribed_tests": ["list of test names"],
    "doctor_name": "string or null",
    "hospital_clinic": "string or null", 
    "prescription_date": "YYYY-MM-DD or null",
    "additional_instructions": "string or null",
    "confidence_score": 0.0-1.0,
    "missing_fields": ["list of fields that couldn't be determined"],
    "analysis_notes": "Brief explanation of what was found/unclear"
}

CRITICAL: Focus only on diagnostic tests and medical investigations. Ignore medications, treatments, or therapies. If no diagnostic tests are found, return empty prescribed_tests array."""

    async def analyze_prescription_image(self, image_data: bytes, image_format: str = "jpeg") -> PrescriptionData:
        """
        Analyze prescription image and extract structured data.
        
        Args:
            image_data: Raw image bytes
            image_format: Image format (jpeg, png, etc.)
            
        Returns:
            PrescriptionData object with extracted information
        """
        try:
            self.logger.info("🔍 Starting prescription image analysis with Gemini-2.5-Pro")
            
            # Process image for optimal analysis
            processed_image = await self._preprocess_image(image_data)
            
            # Create proper Google GenAI image part using dictionary format
            mime_type = f"image/{image_format}"
            image_part = {'mime_type': mime_type, 'data': processed_image}
            
            # Create the prompt combining system instructions and user request
            full_prompt = f"""{self.system_prompt}

Please analyze this medical prescription image and extract all diagnostic test information along with patient and doctor details. Focus specifically on tests that can be booked at a diagnostic center."""
            
            # Generate content using proper Google GenAI SDK format
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self.model.generate_content([full_prompt, image_part])
                )
            except Exception as direct_error:
                self.logger.error(f"Direct Gemini API call failed: {direct_error}")
                # Try sync approach
                try:
                    response = self.model.generate_content([full_prompt, image_part])
                except Exception as sync_error:
                    self.logger.error(f"Both async and sync Gemini calls failed: {sync_error}")
                    raise direct_error
            
            self.logger.info("✅ Gemini-2.5-Pro image analysis completed", 
                           response_length=len(response.text) if response.text else 0)
            
            # Parse structured response
            prescription_data = await self._parse_analysis_response(response.text)
            
            self.logger.info("📋 Prescription data extracted successfully",
                           patient_name=prescription_data.patient_name,
                           tests_found=len(prescription_data.prescribed_tests),
                           confidence=prescription_data.confidence_score)
            
            return prescription_data
            
        except Exception as e:
            self.logger.error("❌ Prescription image analysis failed", error=str(e))
            # Return empty prescription data with error info
            return PrescriptionData(
                missing_fields=["all_fields"],
                confidence_score=0.0
            )
    
    async def _preprocess_image(self, image_data: bytes) -> bytes:
        """Optimize image for better OCR and analysis."""
        try:
            # Load image
            image = Image.open(BytesIO(image_data))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (Gemini works well with images up to 4MB)
            max_size = (2048, 2048)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save processed image to bytes
            output = BytesIO()
            image.save(output, format='JPEG', quality=95, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            self.logger.warning(f"Image preprocessing failed, using original: {e}")
            return image_data
    
    async def _parse_analysis_response(self, response_content: str) -> PrescriptionData:
        """Parse Gemini response into structured prescription data."""
        try:
            # Clean response (remove markdown formatting if present)
            json_str = response_content.strip()
            if json_str.startswith("```json"):
                json_str = json_str.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON
            parsed_data = json.loads(json_str)
            
            # Create PrescriptionData object
            return PrescriptionData(
                patient_name=parsed_data.get("patient_name"),
                age=parsed_data.get("age"),
                gender=parsed_data.get("gender"),
                prescribed_tests=parsed_data.get("prescribed_tests", []),
                doctor_name=parsed_data.get("doctor_name"),
                hospital_clinic=parsed_data.get("hospital_clinic"),
                prescription_date=parsed_data.get("prescription_date"),
                additional_instructions=parsed_data.get("additional_instructions"),
                confidence_score=parsed_data.get("confidence_score", 0.0),
                missing_fields=parsed_data.get("missing_fields", [])
            )
            
        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse JSON response from Gemini", error=str(e))
            # Try to extract tests using fallback method
            return await self._fallback_text_extraction(response_content)
        
        except Exception as e:
            self.logger.error("Error parsing analysis response", error=str(e))
            return PrescriptionData(confidence_score=0.0)
    
    async def _fallback_text_extraction(self, response_text: str) -> PrescriptionData:
        """Fallback method to extract basic info if JSON parsing fails."""
        try:
            self.logger.info("📝 Using fallback text extraction")
            
            # Extract basic information using keyword matching
            prescribed_tests = []
            common_tests = [
                "CBC", "Complete Blood Count", "Blood Sugar", "HbA1c", "Lipid Profile",
                "Liver Function", "Kidney Function", "Thyroid", "TSH", "T3", "T4",
                "X-ray", "Ultrasound", "CT Scan", "MRI", "ECG", "Echo", "TMT",
                "Glucose", "Cholesterol", "Urine", "Stool", "ESR", "CRP"
            ]
            
            response_lower = response_text.lower()
            for test in common_tests:
                if test.lower() in response_lower:
                    prescribed_tests.append(test)
            
            return PrescriptionData(
                prescribed_tests=list(set(prescribed_tests)),  # Remove duplicates
                confidence_score=0.3,  # Low confidence for fallback
                missing_fields=["patient_name", "age", "gender", "doctor_name"]
            )
            
        except Exception as e:
            self.logger.error("Fallback extraction also failed", error=str(e))
            return PrescriptionData(confidence_score=0.0)

    def validate_prescription_data(self, prescription_data: PrescriptionData) -> Dict[str, Any]:
        """
        Validate extracted prescription data and identify missing critical fields.
        
        Returns:
            Dictionary with validation results and required user inputs
        """
        missing_critical = []
        missing_optional = []
        
        # Critical fields for booking
        if not prescription_data.patient_name:
            missing_critical.append("patient_name")
        
        if not prescription_data.age:
            missing_critical.append("age")
            
        if not prescription_data.gender:
            missing_critical.append("gender")
            
        if not prescription_data.prescribed_tests:
            missing_critical.append("prescribed_tests")
        
        # Optional but helpful fields
        if not prescription_data.doctor_name:
            missing_optional.append("doctor_name")
            
        if not prescription_data.prescription_date:
            missing_optional.append("prescription_date")
        
        return {
            "is_valid": len(missing_critical) == 0,
            "missing_critical": missing_critical,
            "missing_optional": missing_optional,
            "confidence_score": prescription_data.confidence_score,
            "extracted_tests": prescription_data.prescribed_tests,
            "needs_user_input": len(missing_critical) > 0
        }


# Global parser instance
_global_prescription_parser = None

def get_prescription_parser() -> PrescriptionImageParser:
    """Get or create global prescription parser instance."""
    global _global_prescription_parser
    if _global_prescription_parser is None:
        _global_prescription_parser = PrescriptionImageParser()
        logger.info("🏥 Created prescription image parser with Gemini-2.5-Pro")
    return _global_prescription_parser


# Convenience function for direct analysis
async def analyze_prescription_image(image_data: bytes, image_format: str = "jpeg") -> PrescriptionData:
    """
    Direct function to analyze prescription image.
    
    Args:
        image_data: Raw image bytes
        image_format: Image format (jpeg, png, webp, etc.)
        
    Returns:
        PrescriptionData with extracted information
    """
    parser = get_prescription_parser()
    return await parser.analyze_prescription_image(image_data, image_format)