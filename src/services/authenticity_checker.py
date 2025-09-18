"""
Document Authenticity Verification Service
Detects signs of tampering, fraud, and validates document authenticity
"""
import cv2
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from PIL import Image, ExifTags
from io import BytesIO
import hashlib
import json
from datetime import datetime
from enum import Enum

class AuthenticityLevel(Enum):
    """Document authenticity confidence levels"""
    AUTHENTIC = "authentic"
    SUSPICIOUS = "suspicious"
    LIKELY_FRAUD = "likely_fraud"
    CONFIRMED_FRAUD = "confirmed_fraud"

class FraudIndicator(Enum):
    """Types of fraud indicators"""
    DIGITAL_TAMPERING = "digital_tampering"
    COPY_PASTE = "copy_paste"
    FONT_INCONSISTENCY = "font_inconsistency"
    RESOLUTION_MISMATCH = "resolution_mismatch"
    METADATA_ANOMALY = "metadata_anomaly"
    WATERMARK_MISSING = "watermark_missing"
    EDGE_ARTIFACTS = "edge_artifacts"
    COLOR_INCONSISTENCY = "color_inconsistency"
    DUPLICATE_DETECTION = "duplicate_detection"

@dataclass
class AuthenticityCheck:
    """Result of an authenticity check"""
    indicator_type: FraudIndicator
    confidence: float
    description: str
    severity: str  # low, medium, high, critical
    details: Dict[str, Any]
    coordinates: Optional[Tuple[int, int, int, int]] = None

class DocumentAuthenticityChecker:
    """Service for verifying document authenticity and detecting fraud"""
    
    def __init__(self):
        self.known_document_hashes = set()  # Store hashes of known authentic documents
        self.suspicious_patterns = self._load_suspicious_patterns()
    
    def verify_document_authenticity(self, image_data: bytes, document_type: str = "unknown") -> Dict[str, Any]:
        """Comprehensive authenticity verification using Azure AI and local analysis"""
        
        # Convert to image for analysis
        image = Image.open(BytesIO(image_data))
        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        checks = []
        
        # Azure AI Document Intelligence analysis
        azure_checks = self._analyze_with_azure_document_intelligence(image_data, document_type)
        checks.extend(azure_checks)
        
        # Local computer vision checks
        checks.extend(self._check_digital_tampering(image_cv))
        checks.extend(self._check_metadata_anomalies(image))
        checks.extend(self._check_resolution_consistency(image_cv))
        checks.extend(self._check_font_consistency(image_cv))
        checks.extend(self._check_edge_artifacts(image_cv))
        checks.extend(self._check_color_consistency(image_cv))
        checks.extend(self._check_duplicate_content(image_data))
        checks.extend(self._check_watermarks(image_cv, document_type))
        
        # Calculate overall authenticity score
        authenticity_result = self._calculate_authenticity_score(checks)
        
        return {
            "document_authenticity": authenticity_result["level"],
            "confidence_score": authenticity_result["score"],
            "fraud_indicators": len(checks),
            "checks_performed": len(checks),
            "azure_analysis_used": len(azure_checks) > 0,
            "detailed_checks": [
                {
                    "type": check.indicator_type.value,
                    "confidence": check.confidence,
                    "severity": check.severity,
                    "description": check.description,
                    "details": check.details
                } for check in checks
            ],
            "recommendations": self._generate_authenticity_recommendations(checks),
            "risk_assessment": self._assess_fraud_risk(checks)
        }
    
    def _analyze_with_azure_document_intelligence(self, image_data: bytes, document_type: str) -> List[AuthenticityCheck]:
        """Use Azure Document Intelligence to analyze document authenticity"""
        checks = []
        
        try:
            import os
            from azure.ai.formrecognizer import DocumentAnalysisClient
            from azure.core.credentials import AzureKeyCredential
            
            # Get Azure credentials
            endpoint = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
            key = os.getenv("AZURE_FORM_RECOGNIZER_KEY")
            
            if not endpoint or not key:
                return checks
            
            # Create client
            client = DocumentAnalysisClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(key)
            )
            
            # Analyze document based on type
            model_id = self._get_document_intelligence_model(document_type)
            
            poller = client.begin_analyze_document(
                model_id=model_id,
                document=image_data
            )
            result = poller.result()
            
            # Analyze confidence scores and consistency
            if result.documents:
                doc = result.documents[0]
                
                # Check overall confidence
                if hasattr(doc, 'confidence') and doc.confidence < 0.7:
                    checks.append(AuthenticityCheck(
                        indicator_type=FraudIndicator.DIGITAL_TAMPERING,
                        confidence=1.0 - doc.confidence,
                        description=f"Low document recognition confidence from Azure AI: {doc.confidence:.2f}",
                        severity="medium",
                        details={"azure_confidence": doc.confidence, "model_used": model_id}
                    ))
                
                # Check field consistency
                inconsistent_fields = 0
                for field_name, field in doc.fields.items():
                    if hasattr(field, 'confidence') and field.confidence < 0.5:
                        inconsistent_fields += 1
                
                if inconsistent_fields > 2:
                    checks.append(AuthenticityCheck(
                        indicator_type=FraudIndicator.FONT_INCONSISTENCY,
                        confidence=min(inconsistent_fields / 5.0, 1.0),
                        description=f"Multiple fields with low confidence detected: {inconsistent_fields}",
                        severity="medium",
                        details={"low_confidence_fields": inconsistent_fields}
                    ))
            
            # Check for expected document structure
            if not result.documents or len(result.documents) == 0:
                checks.append(AuthenticityCheck(
                    indicator_type=FraudIndicator.DIGITAL_TAMPERING,
                    confidence=0.8,
                    description="Document structure not recognized by Azure AI",
                    severity="high",
                    details={"model_used": model_id, "documents_found": 0}
                ))
                
        except Exception as e:
            # Azure analysis failed - note this but don't fail the whole process
            checks.append(AuthenticityCheck(
                indicator_type=FraudIndicator.METADATA_ANOMALY,
                confidence=0.3,
                description=f"Azure Document Intelligence analysis failed: {str(e)}",
                severity="low",
                details={"error": str(e)}
            ))
        
        return checks
    
    def _get_document_intelligence_model(self, document_type: str) -> str:
        """Get appropriate Azure Document Intelligence model for document type"""
        
        model_mapping = {
            "passport": "prebuilt-idDocument",
            "drivers_license": "prebuilt-idDocument", 
            "national_id": "prebuilt-idDocument",
            "utility_bill": "prebuilt-document",
            "bank_statement": "prebuilt-document",
            "unknown": "prebuilt-document"
        }
        
        return model_mapping.get(document_type.lower(), "prebuilt-document")
    
    def _check_digital_tampering(self, image: np.ndarray) -> List[AuthenticityCheck]:
        """Detect signs of digital tampering"""
        checks = []
        
        # Error Level Analysis (ELA) - simplified version
        ela_result = self._perform_ela_analysis(image)
        if ela_result["tampering_detected"]:
            checks.append(AuthenticityCheck(
                indicator_type=FraudIndicator.DIGITAL_TAMPERING,
                confidence=ela_result["confidence"],
                description="Potential digital tampering detected through Error Level Analysis",
                severity="high",
                details=ela_result,
                coordinates=ela_result.get("suspicious_regions")
            ))
        
        # Check for copy-paste artifacts
        copy_paste_result = self._detect_copy_paste(image)
        if copy_paste_result["detected"]:
            checks.append(AuthenticityCheck(
                indicator_type=FraudIndicator.COPY_PASTE,
                confidence=copy_paste_result["confidence"],
                description="Copy-paste artifacts detected",
                severity="high",
                details=copy_paste_result
            ))
        
        return checks
    
    def _check_metadata_anomalies(self, image: Image) -> List[AuthenticityCheck]:
        """Check for suspicious metadata"""
        checks = []
        
        try:
            exif_data = image._getexif() if hasattr(image, '_getexif') else None
            
            if exif_data:
                # Check for editing software signatures
                software_tags = []
                for tag_id, value in exif_data.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    if tag in ['Software', 'ProcessingSoftware', 'CreatorTool']:
                        software_tags.append(str(value).lower())
                
                # Flag common editing software
                suspicious_software = ['photoshop', 'gimp', 'paint.net', 'canva', 'pixlr']
                found_suspicious = [s for s in suspicious_software if any(s in tag for tag in software_tags)]
                
                if found_suspicious:
                    checks.append(AuthenticityCheck(
                        indicator_type=FraudIndicator.METADATA_ANOMALY,
                        confidence=0.7,
                        description=f"Document processed with editing software: {', '.join(found_suspicious)}",
                        severity="medium",
                        details={"editing_software": found_suspicious, "software_tags": software_tags}
                    ))
                
                # Check for missing expected metadata
                expected_tags = ['DateTime', 'Make', 'Model']
                missing_tags = [tag for tag in expected_tags if tag not in [ExifTags.TAGS.get(k) for k in exif_data.keys()]]
                
                if len(missing_tags) >= 2:
                    checks.append(AuthenticityCheck(
                        indicator_type=FraudIndicator.METADATA_ANOMALY,
                        confidence=0.5,
                        description="Missing expected camera metadata",
                        severity="low",
                        details={"missing_tags": missing_tags}
                    ))
        
        except Exception as e:
            # Metadata extraction failed - could be suspicious
            checks.append(AuthenticityCheck(
                indicator_type=FraudIndicator.METADATA_ANOMALY,
                confidence=0.3,
                description="Unable to extract metadata - potentially stripped",
                severity="low",
                details={"error": str(e)}
            ))
        
        return checks
    
    def _check_resolution_consistency(self, image: np.ndarray) -> List[AuthenticityCheck]:
        """Check for resolution inconsistencies that might indicate tampering"""
        checks = []
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Ensure image is large enough for analysis
            if gray.shape[0] < 100 or gray.shape[1] < 100:
                return checks  # Skip analysis for very small images
            
            # Divide image into regions and check for resolution inconsistencies
            regions = self._divide_into_regions(gray, 4, 4)  # 4x4 grid
            resolutions = []
            
            for region in regions:
                if region.size == 0 or region.shape[0] < 10 or region.shape[1] < 10:
                    continue  # Skip invalid regions
                
                # Estimate local resolution using gradient analysis
                grad_x = cv2.Sobel(region, cv2.CV_64F, 1, 0, ksize=3)
                grad_y = cv2.Sobel(region, cv2.CV_64F, 0, 1, ksize=3)
                magnitude = np.sqrt(grad_x**2 + grad_y**2)
                resolution_score = np.mean(magnitude)
                resolutions.append(resolution_score)
            
            if len(resolutions) < 2:
                return checks  # Need at least 2 regions for comparison
            
            # Check for significant variations
            resolution_std = np.std(resolutions)
            resolution_mean = np.mean(resolutions)
            
            if resolution_mean > 0 and resolution_std > resolution_mean * 0.3:  # Threshold for inconsistency
                checks.append(AuthenticityCheck(
                    indicator_type=FraudIndicator.RESOLUTION_MISMATCH,
                    confidence=min(resolution_std / resolution_mean, 1.0),
                    description="Inconsistent resolution across document regions",
                    severity="medium",
                    details={
                        "resolution_variance": float(resolution_std),
                        "mean_resolution": float(resolution_mean),
                        "regions_analyzed": len(regions)
                    }
                ))
        
        except Exception as e:
            # Log error but don't fail the whole authenticity check
            checks.append(AuthenticityCheck(
                indicator_type=FraudIndicator.DIGITAL_TAMPERING,
                confidence=0.1,
                description=f"Resolution analysis failed: {str(e)}",
                severity="low",
                details={"error": str(e)}
            ))
        
        return checks
    
    def _check_font_consistency(self, image: np.ndarray) -> List[AuthenticityCheck]:
        """Check for font inconsistencies that might indicate tampering"""
        checks = []
        
        # This is a simplified implementation
        # In practice, you'd use more sophisticated text analysis
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Find text regions
        text_regions = self._find_text_regions(gray)
        
        if len(text_regions) > 1:
            # Analyze font characteristics in different regions
            font_characteristics = []
            
            for region in text_regions:
                # Extract font features (simplified)
                features = self._extract_font_features(region)
                font_characteristics.append(features)
            
            # Check for inconsistencies
            if self._detect_font_inconsistencies(font_characteristics):
                checks.append(AuthenticityCheck(
                    indicator_type=FraudIndicator.FONT_INCONSISTENCY,
                    confidence=0.6,
                    description="Inconsistent font characteristics detected",
                    severity="medium",
                    details={"text_regions_found": len(text_regions)}
                ))
        
        return checks
    
    def _check_edge_artifacts(self, image: np.ndarray) -> List[AuthenticityCheck]:
        """Check for edge artifacts that might indicate tampering"""
        checks = []
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect edges
        edges = cv2.Canny(gray, 50, 150)
        
        # Look for suspicious edge patterns
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        suspicious_edges = 0
        for contour in contours:
            # Check for unnaturally straight edges or perfect rectangles
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            if len(approx) == 4:  # Rectangle
                # Check if it's suspiciously perfect
                area = cv2.contourArea(contour)
                if area > 1000:  # Only consider significant rectangles
                    suspicious_edges += 1
        
        if suspicious_edges > 3:  # Threshold for suspicion
            checks.append(AuthenticityCheck(
                indicator_type=FraudIndicator.EDGE_ARTIFACTS,
                confidence=min(suspicious_edges / 10.0, 1.0),
                description="Suspicious edge artifacts detected",
                severity="low",
                details={"suspicious_rectangles": suspicious_edges}
            ))
        
        return checks
    
    def _check_color_consistency(self, image: np.ndarray) -> List[AuthenticityCheck]:
        """Check for color inconsistencies"""
        checks = []
        
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Analyze color distribution in different regions
        regions = self._divide_into_regions(hsv, 3, 3)
        color_stats = []
        
        for region in regions:
            h_mean = np.mean(region[:, :, 0])
            s_mean = np.mean(region[:, :, 1])
            v_mean = np.mean(region[:, :, 2])
            color_stats.append((h_mean, s_mean, v_mean))
        
        # Check for unusual color variations
        h_std = np.std([stat[0] for stat in color_stats])
        s_std = np.std([stat[1] for stat in color_stats])
        
        if h_std > 30 or s_std > 50:  # Thresholds for color inconsistency
            checks.append(AuthenticityCheck(
                indicator_type=FraudIndicator.COLOR_INCONSISTENCY,
                confidence=min((h_std + s_std) / 100.0, 1.0),
                description="Unusual color variations detected",
                severity="low",
                details={"hue_variance": float(h_std), "saturation_variance": float(s_std)}
            ))
        
        return checks
    
    def _check_duplicate_content(self, image_data: bytes) -> List[AuthenticityCheck]:
        """Check for duplicate document submission"""
        checks = []
        
        # Create hash of the image
        image_hash = hashlib.sha256(image_data).hexdigest()
        
        if image_hash in self.known_document_hashes:
            checks.append(AuthenticityCheck(
                indicator_type=FraudIndicator.DUPLICATE_DETECTION,
                confidence=1.0,
                description="Duplicate document detected",
                severity="critical",
                details={"hash": image_hash}
            ))
        else:
            # Add to known hashes for future checks
            self.known_document_hashes.add(image_hash)
        
        return checks
    
    def _check_watermarks(self, image: np.ndarray, document_type: str) -> List[AuthenticityCheck]:
        """Check for expected watermarks or security features"""
        checks = []
        
        # This would be implemented based on known watermark patterns
        # for different document types
        expected_watermarks = self._get_expected_watermarks(document_type)
        
        if expected_watermarks:
            watermark_detected = self._detect_watermarks(image, expected_watermarks)
            
            if not watermark_detected:
                checks.append(AuthenticityCheck(
                    indicator_type=FraudIndicator.WATERMARK_MISSING,
                    confidence=0.8,
                    description=f"Expected watermark not found for {document_type}",
                    severity="high",
                    details={"document_type": document_type, "expected_features": expected_watermarks}
                ))
        
        return checks
    
    def _perform_ela_analysis(self, image: np.ndarray) -> Dict[str, Any]:
        """Simplified Error Level Analysis"""
        # This is a basic implementation - real ELA is more complex
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply JPEG compression and measure differences
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        _, compressed = cv2.imencode('.jpg', gray, encode_param)
        decompressed = cv2.imdecode(compressed, cv2.IMREAD_GRAYSCALE)
        
        # Calculate difference
        diff = cv2.absdiff(gray, decompressed)
        
        # Analyze difference patterns
        mean_diff = np.mean(diff)
        std_diff = np.std(diff)
        
        tampering_detected = std_diff > 10 and mean_diff > 5  # Simple thresholds
        
        return {
            "tampering_detected": tampering_detected,
            "confidence": min(std_diff / 20.0, 1.0),
            "mean_difference": float(mean_diff),
            "std_difference": float(std_diff)
        }
    
    def _detect_copy_paste(self, image: np.ndarray) -> Dict[str, Any]:
        """Detect copy-paste artifacts using feature matching"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Use ORB detector to find keypoints
        orb = cv2.ORB_create()
        kp, des = orb.detectAndCompute(gray, None)
        
        if des is None or len(des) < 10:
            return {"detected": False, "confidence": 0.0}
        
        # Match features against themselves to find duplicates
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des, des)
        
        # Filter out self-matches and very close matches
        filtered_matches = []
        for match in matches:
            if match.queryIdx != match.trainIdx:
                pt1 = kp[match.queryIdx].pt
                pt2 = kp[match.trainIdx].pt
                distance = np.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
                if distance > 50:  # Minimum distance threshold
                    filtered_matches.append(match)
        
        # If too many similar features found far apart, might indicate copy-paste
        detected = len(filtered_matches) > 20
        confidence = min(len(filtered_matches) / 50.0, 1.0)
        
        return {
            "detected": detected,
            "confidence": confidence,
            "similar_features": len(filtered_matches)
        }
    
    def _divide_into_regions(self, image: np.ndarray, rows: int, cols: int) -> List[np.ndarray]:
        """Divide image into grid regions"""
        h, w = image.shape[:2]
        
        # Ensure minimum size for regions
        if h < rows * 10 or w < cols * 10:
            # If image is too small, return the whole image as single region
            return [image]
        
        regions = []
        
        for i in range(rows):
            for j in range(cols):
                y1 = i * h // rows
                y2 = (i + 1) * h // rows
                x1 = j * w // cols
                x2 = (j + 1) * w // cols
                
                # Ensure region has valid dimensions
                if y2 > y1 and x2 > x1:
                    region = image[y1:y2, x1:x2]
                    if region.size > 0:  # Ensure region is not empty
                        regions.append(region)
        
        return regions if regions else [image]
    
    def _find_text_regions(self, gray_image: np.ndarray) -> List[np.ndarray]:
        """Find regions containing text"""
        # Use MSER (Maximally Stable Extremal Regions) to find text-like regions
        mser = cv2.MSER_create()
        regions, _ = mser.detectRegions(gray_image)
        
        text_regions = []
        for region in regions:
            if len(region) > 50:  # Filter small regions
                x, y, w, h = cv2.boundingRect(region)
                text_regions.append(gray_image[y:y+h, x:x+w])
        
        return text_regions
    
    def _extract_font_features(self, text_region: np.ndarray) -> Dict[str, float]:
        """Extract font characteristics from text region"""
        # Simplified font feature extraction
        return {
            "stroke_width": float(np.mean(cv2.morphologyEx(text_region, cv2.MORPH_CLOSE, np.ones((3,3))))),
            "character_height": float(text_region.shape[0]),
            "contrast": float(np.std(text_region))
        }
    
    def _detect_font_inconsistencies(self, font_characteristics: List[Dict[str, float]]) -> bool:
        """Detect inconsistencies in font characteristics"""
        if len(font_characteristics) < 2:
            return False
        
        # Check for significant variations in stroke width
        stroke_widths = [fc["stroke_width"] for fc in font_characteristics]
        stroke_std = np.std(stroke_widths)
        stroke_mean = np.mean(stroke_widths)
        
        return stroke_std > stroke_mean * 0.5  # Threshold for inconsistency
    
    def _get_expected_watermarks(self, document_type: str) -> List[str]:
        """Get expected watermarks for document type"""
        watermark_map = {
            "passport": ["passport_seal", "country_watermark"],
            "drivers_license": ["state_seal", "hologram"],
            "id_card": ["government_seal"],
            "birth_certificate": ["official_seal"]
        }
        return watermark_map.get(document_type.lower(), [])
    
    def _detect_watermarks(self, image: np.ndarray, expected_watermarks: List[str]) -> bool:
        """Detect specific watermarks (simplified implementation)"""
        # This would use template matching or ML models to detect specific watermarks
        # For now, return a mock result
        return False  # Placeholder
    
    def _calculate_authenticity_score(self, checks: List[AuthenticityCheck]) -> Dict[str, Any]:
        """Calculate overall authenticity score"""
        if not checks:
            return {"level": AuthenticityLevel.AUTHENTIC, "score": 1.0}
        
        # Weight checks by severity
        severity_weights = {"low": 1, "medium": 2, "high": 3, "critical": 5}
        
        total_weight = 0
        weighted_score = 0
        
        for check in checks:
            weight = severity_weights[check.severity]
            total_weight += weight
            weighted_score += weight * check.confidence
        
        average_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # Determine authenticity level
        if average_score < 0.3:
            level = AuthenticityLevel.AUTHENTIC
        elif average_score < 0.6:
            level = AuthenticityLevel.SUSPICIOUS
        elif average_score < 0.8:
            level = AuthenticityLevel.LIKELY_FRAUD
        else:
            level = AuthenticityLevel.CONFIRMED_FRAUD
        
        return {"level": level, "score": 1.0 - average_score}
    
    def _generate_authenticity_recommendations(self, checks: List[AuthenticityCheck]) -> List[str]:
        """Generate recommendations based on authenticity checks"""
        recommendations = []
        
        if not checks:
            recommendations.append("Document appears authentic - no fraud indicators detected")
            return recommendations
        
        high_severity_checks = [c for c in checks if c.severity in ["high", "critical"]]
        
        if high_severity_checks:
            recommendations.append("Manual review required - high-risk fraud indicators detected")
            recommendations.append("Consider requesting additional documentation")
        
        indicator_types = [c.indicator_type for c in checks]
        
        if FraudIndicator.DIGITAL_TAMPERING in indicator_types:
            recommendations.append("Digital tampering detected - verify document source")
        
        if FraudIndicator.DUPLICATE_DETECTION in indicator_types:
            recommendations.append("Duplicate document submitted - investigate potential fraud")
        
        if FraudIndicator.METADATA_ANOMALY in indicator_types:
            recommendations.append("Metadata inconsistencies found - request original document")
        
        return recommendations
    
    def _assess_fraud_risk(self, checks: List[AuthenticityCheck]) -> str:
        """Assess overall fraud risk"""
        if not checks:
            return "LOW"
        
        critical_checks = [c for c in checks if c.severity == "critical"]
        high_checks = [c for c in checks if c.severity == "high"]
        
        if critical_checks:
            return "CRITICAL"
        elif len(high_checks) >= 2:
            return "HIGH"
        elif len(checks) >= 4:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _load_suspicious_patterns(self) -> Dict[str, Any]:
        """Load known suspicious patterns"""
        # This would load from a database or configuration file
        return {
            "known_fraud_signatures": [],
            "suspicious_software_signatures": ["photoshop", "gimp"],
            "common_tampering_patterns": []
        }

# Global authenticity checker instance
authenticity_checker = DocumentAuthenticityChecker()

# Convenience function
def verify_document_authenticity(image_data: bytes, document_type: str = "unknown") -> Dict[str, Any]:
    """Verify document authenticity and detect fraud indicators"""
    return authenticity_checker.verify_document_authenticity(image_data, document_type)
