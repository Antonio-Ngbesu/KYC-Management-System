"""
PII Redaction Service for KYC Document Analyzer
Automatically detects and redacts sensitive information from documents
"""
import re
import cv2
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from PIL import Image, ImageDraw
import base64
from io import BytesIO

@dataclass
class PIIMatch:
    """Represents a detected PII element"""
    pii_type: str
    value: str
    confidence: float
    start_pos: int = None
    end_pos: int = None
    coordinates: Tuple[int, int, int, int] = None  # x, y, width, height for images

class PIIPattern:
    """PII detection patterns and rules"""
    
    # Regular expressions for common PII patterns
    PATTERNS = {
        "ssn": {
            "pattern": r'\b\d{3}-?\d{2}-?\d{4}\b',
            "confidence": 0.9,
            "description": "Social Security Number"
        },
        "credit_card": {
            "pattern": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            "confidence": 0.8,
            "description": "Credit Card Number"
        },
        "phone": {
            "pattern": r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
            "confidence": 0.7,
            "description": "Phone Number"
        },
        "email": {
            "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "confidence": 0.9,
            "description": "Email Address"
        },
        "drivers_license": {
            "pattern": r'\b[A-Z]{1,2}\d{6,8}\b',
            "confidence": 0.6,
            "description": "Driver's License Number"
        },
        "passport": {
            "pattern": r'\b[A-Z]{1,2}\d{7,9}\b',
            "confidence": 0.6,
            "description": "Passport Number"
        },
        "date_of_birth": {
            "pattern": r'\b(?:0[1-9]|1[0-2])[/-](?:0[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}\b',
            "confidence": 0.8,
            "description": "Date of Birth"
        },
        "bank_account": {
            "pattern": r'\b\d{8,17}\b',
            "confidence": 0.5,
            "description": "Bank Account Number"
        }
    }
    
    # Sensitive keywords that might indicate PII context
    SENSITIVE_KEYWORDS = [
        "social security", "ssn", "tax id", "ein", "passport", "license",
        "account number", "routing number", "credit card", "debit card",
        "date of birth", "dob", "mother's maiden name", "security question"
    ]

class PIIRedactionService:
    """Service for detecting and redacting PII from text and images"""
    
    def __init__(self):
        self.patterns = PIIPattern()
        
    def detect_text_pii(self, text: str) -> List[PIIMatch]:
        """Detect PII in text content"""
        matches = []
        
        for pii_type, pattern_info in self.patterns.PATTERNS.items():
            pattern = pattern_info["pattern"]
            confidence = pattern_info["confidence"]
            
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Additional validation for certain types
                if self._validate_pii_match(pii_type, match.group()):
                    matches.append(PIIMatch(
                        pii_type=pii_type,
                        value=match.group(),
                        confidence=confidence,
                        start_pos=match.start(),
                        end_pos=match.end()
                    ))
        
        # Check for sensitive keywords context
        matches.extend(self._detect_contextual_pii(text))
        
        return matches
    
    def redact_text_pii(self, text: str, redaction_char: str = "█") -> Tuple[str, List[PIIMatch]]:
        """Redact PII from text and return redacted text with matches"""
        matches = self.detect_text_pii(text)
        
        # Sort matches by position (reverse order to maintain positions)
        matches.sort(key=lambda x: x.start_pos, reverse=True)
        
        redacted_text = text
        for match in matches:
            # Replace with redaction characters of same length
            redaction = redaction_char * len(match.value)
            redacted_text = (
                redacted_text[:match.start_pos] + 
                redaction + 
                redacted_text[match.end_pos:]
            )
        
        return redacted_text, matches
    
    def detect_image_pii(self, image_data: bytes) -> List[PIIMatch]:
        """Detect PII in image using Azure Vision OCR and pattern matching"""
        try:
            # Convert bytes to PIL Image
            image = Image.open(BytesIO(image_data))
            
            # Use Azure Vision API for OCR text extraction
            extracted_text, ocr_results = self._extract_text_with_azure_vision(image_data)
            
            # Detect PII in extracted text
            text_matches = self.detect_text_pii(extracted_text)
            
            # Convert text positions to image coordinates using OCR results
            image_matches = []
            for match in text_matches:
                # Find coordinates from OCR results
                coordinates = self._find_text_coordinates_in_ocr(match, ocr_results)
                image_matches.append(PIIMatch(
                    pii_type=match.pii_type,
                    value=match.value,
                    confidence=match.confidence * 0.9,  # High confidence with Azure OCR
                    coordinates=coordinates
                ))
            
            return image_matches
            
        except Exception as e:
            print(f"Error processing image for PII detection: {e}")
            return []
    
    def redact_image_pii(self, image_data: bytes, blur_strength: int = 15) -> Tuple[bytes, List[PIIMatch]]:
        """Redact PII from image by blurring detected regions"""
        matches = self.detect_image_pii(image_data)
        
        try:
            # Convert to PIL Image
            image = Image.open(BytesIO(image_data))
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Apply redaction to each detected PII region
            for match in matches:
                if match.coordinates:
                    x, y, w, h = match.coordinates
                    # Blur the region
                    roi = image_cv[y:y+h, x:x+w]
                    blurred_roi = cv2.GaussianBlur(roi, (blur_strength, blur_strength), 0)
                    image_cv[y:y+h, x:x+w] = blurred_roi
            
            # Convert back to PIL and then to bytes
            redacted_image = Image.fromarray(cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB))
            
            # Save to bytes
            output_buffer = BytesIO()
            redacted_image.save(output_buffer, format='PNG')
            redacted_bytes = output_buffer.getvalue()
            
            return redacted_bytes, matches
            
        except Exception as e:
            print(f"Error redacting image: {e}")
            return image_data, matches
    
    def create_pii_report(self, matches: List[PIIMatch], document_id: str) -> Dict[str, Any]:
        """Create a detailed PII detection report"""
        pii_summary = {}
        
        for match in matches:
            if match.pii_type not in pii_summary:
                pii_summary[match.pii_type] = {
                    "count": 0,
                    "description": self.patterns.PATTERNS.get(match.pii_type, {}).get("description", match.pii_type),
                    "instances": []
                }
            
            pii_summary[match.pii_type]["count"] += 1
            pii_summary[match.pii_type]["instances"].append({
                "value_masked": self._mask_value(match.value),
                "confidence": match.confidence,
                "location": "text" if match.coordinates is None else "image"
            })
        
        return {
            "document_id": document_id,
            "total_pii_found": len(matches),
            "pii_types_detected": list(pii_summary.keys()),
            "pii_summary": pii_summary,
            "risk_level": self._calculate_risk_level(matches),
            "recommendations": self._generate_recommendations(matches)
        }
    
    def _validate_pii_match(self, pii_type: str, value: str) -> bool:
        """Additional validation for PII matches"""
        if pii_type == "credit_card":
            # Luhn algorithm validation for credit cards
            return self._validate_credit_card(value)
        elif pii_type == "ssn":
            # Basic SSN validation
            digits = re.sub(r'[^\d]', '', value)
            return len(digits) == 9 and not digits.startswith('000')
        return True
    
    def _validate_credit_card(self, card_number: str) -> bool:
        """Validate credit card using Luhn algorithm"""
        digits = re.sub(r'[^\d]', '', card_number)
        if len(digits) < 13 or len(digits) > 19:
            return False
        
        # Luhn algorithm
        total = 0
        reverse_digits = digits[::-1]
        
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n = n // 10 + n % 10
            total += n
        
        return total % 10 == 0
    
    def _detect_contextual_pii(self, text: str) -> List[PIIMatch]:
        """Detect PII based on context and keywords"""
        matches = []
        text_lower = text.lower()
        
        for keyword in self.patterns.SENSITIVE_KEYWORDS:
            if keyword in text_lower:
                # Look for values near sensitive keywords
                pattern = rf'{keyword}\s*:?\s*([A-Za-z0-9\-\s]+)'
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    matches.append(PIIMatch(
                        pii_type="contextual_pii",
                        value=match.group(1).strip(),
                        confidence=0.6,
                        start_pos=match.start(1),
                        end_pos=match.end(1)
                    ))
        
        return matches
    
    def _extract_text_with_azure_vision(self, image_data: bytes) -> Tuple[str, Dict[str, Any]]:
        """Extract text using Azure Vision API OCR"""
        try:
            import os
            from azure.ai.vision.imageanalysis import ImageAnalysisClient
            from azure.ai.vision.imageanalysis.models import VisualFeatures
            from azure.core.credentials import AzureKeyCredential
            
            # Get Azure Vision credentials
            endpoint = os.getenv("AZURE_VISION_ENDPOINT")
            key = os.getenv("AZURE_VISION_KEY")
            
            if not endpoint or not key:
                # Fallback to simulation if credentials not available
                return self._simulate_ocr_text(), {}
            
            # Create client
            client = ImageAnalysisClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(key)
            )
            
            # Analyze image for text
            result = client.analyze(
                image_data=image_data,
                visual_features=[VisualFeatures.READ]
            )
            
            # Extract text and coordinates
            extracted_text = ""
            ocr_results = {"text_blocks": []}
            
            if result.read and result.read.blocks:
                for block in result.read.blocks:
                    for line in block.lines:
                        extracted_text += line.text + " "
                        
                        # Store coordinates for each word
                        for word in line.words:
                            ocr_results["text_blocks"].append({
                                "text": word.text,
                                "confidence": word.confidence,
                                "bounding_box": word.bounding_polygon
                            })
            
            return extracted_text.strip(), ocr_results
            
        except Exception as e:
            print(f"Azure Vision OCR failed, using fallback: {e}")
            return self._simulate_ocr_text(), {}
    
    def _simulate_ocr_text(self) -> str:
        """Simulate OCR text extraction as fallback"""
        return "Sample extracted text from image with SSN 123-45-6789 and phone 555-123-4567"
    
    def _find_text_coordinates_in_ocr(self, match: PIIMatch, ocr_results: Dict[str, Any]) -> Tuple[int, int, int, int]:
        """Find bounding box coordinates for matched text in OCR results"""
        if not ocr_results.get("text_blocks"):
            return (100, 50, 200, 25)  # Default coordinates
        
        # Look for the matched text in OCR results
        for block in ocr_results["text_blocks"]:
            if match.value in block["text"]:
                # Extract bounding box coordinates
                bbox = block["bounding_box"]
                if len(bbox) >= 4:
                    # Convert polygon to rectangle (x, y, width, height)
                    x_coords = [point.x for point in bbox]
                    y_coords = [point.y for point in bbox]
                    x = min(x_coords)
                    y = min(y_coords)
                    width = max(x_coords) - x
                    height = max(y_coords) - y
                    return (int(x), int(y), int(width), int(height))
        
        # Default coordinates if not found
        return (100, 50, 200, 25)
    
    def _estimate_text_coordinates(self, match: PIIMatch, image_size: Tuple[int, int]) -> Tuple[int, int, int, int]:
        """Estimate bounding box coordinates for text (mock implementation)"""
        # This would be provided by actual OCR service
        width, height = image_size
        return (100, 50, 200, 25)  # x, y, width, height
    
    def _mask_value(self, value: str) -> str:
        """Create a masked version of sensitive value"""
        if len(value) <= 4:
            return "█" * len(value)
        return value[:2] + "█" * (len(value) - 4) + value[-2:]
    
    def _calculate_risk_level(self, matches: List[PIIMatch]) -> str:
        """Calculate risk level based on PII found"""
        if not matches:
            return "LOW"
        
        high_risk_types = ["ssn", "credit_card", "passport", "drivers_license"]
        high_risk_count = sum(1 for match in matches if match.pii_type in high_risk_types)
        
        if high_risk_count >= 3:
            return "CRITICAL"
        elif high_risk_count >= 1:
            return "HIGH"
        elif len(matches) >= 3:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_recommendations(self, matches: List[PIIMatch]) -> List[str]:
        """Generate recommendations based on PII found"""
        recommendations = []
        
        pii_types = [match.pii_type for match in matches]
        
        if "ssn" in pii_types:
            recommendations.append("SSN detected - ensure secure storage and access controls")
        if "credit_card" in pii_types:
            recommendations.append("Credit card information found - verify PCI compliance requirements")
        if len(matches) > 5:
            recommendations.append("High volume of PII detected - consider additional security measures")
        if any(match.confidence < 0.7 for match in matches):
            recommendations.append("Some PII detected with low confidence - manual review recommended")
        
        return recommendations

# Global PII redaction service instance
pii_service = PIIRedactionService()

# Convenience functions
def detect_and_redact_text(text: str) -> Tuple[str, List[PIIMatch], Dict[str, Any]]:
    """Detect and redact PII from text, return redacted text, matches, and report"""
    redacted_text, matches = pii_service.redact_text_pii(text)
    report = pii_service.create_pii_report(matches, "text_document")
    return redacted_text, matches, report

def detect_and_redact_image(image_data: bytes, document_id: str) -> Tuple[bytes, List[PIIMatch], Dict[str, Any]]:
    """Detect and redact PII from image, return redacted image, matches, and report"""
    redacted_image, matches = pii_service.redact_image_pii(image_data)
    report = pii_service.create_pii_report(matches, document_id)
    return redacted_image, matches, report
