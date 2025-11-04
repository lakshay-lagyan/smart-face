import io
import logging
import base64
import numpy as np
from PIL import Image
import cv2
from deepface import DeepFace
from typing import List, Tuple, Optional, Dict

logger = logging.getLogger(__name__)


class FaceRecognitionService:
    
    def __init__(self, config=None):
        self.config = config or {}
        self.model_name = self.config.get('FACE_MODEL', 'Facenet512')
        self.detector_backend = self.config.get('FACE_DETECTOR', 'mtcnn')
        self.threshold = self.config.get('FACE_RECOGNITION_THRESHOLD', 0.6)
        self.detection_confidence = self.config.get('FACE_DETECTION_CONFIDENCE', 0.9)
        
        # Supported image formats
        self.supported_formats = ['jpg', 'jpeg', 'png', 'webp']
        
        logger.info(f"[FaceRecognition] Initialized with model={self.model_name}, detector={self.detector_backend}")
    
    def base64_to_image(self, base64_str: str) -> np.ndarray:
        try:
            # Remove data URL prefix if present
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]
            
            # Decode base64
            image_data = base64.b64decode(base64_str)
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array
            img_array = np.array(image)
            
            # Convert RGB to BGR for OpenCV
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            return img_bgr
            
        except Exception as e:
            logger.error(f"[FaceRecognition] Base64 conversion error: {e}")
            raise ValueError(f"Invalid image data: {str(e)}")
    
    def preprocess_image(self, image: np.ndarray, max_size: int = 1024) -> np.ndarray:
        
        try:
            # Get image dimensions
            height, width = image.shape[:2]
            
            # Resize if too large (mobile images can be very large)
            if max(height, width) > max_size:
                scale = max_size / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
                logger.info(f"[FaceRecognition] Resized image from {width}x{height} to {new_width}x{new_height}")
            
            # Enhance image quality
            # Apply slight sharpening
            kernel = np.array([[-1,-1,-1],
                              [-1, 9,-1],
                              [-1,-1,-1]])
            image = cv2.filter2D(image, -1, kernel)
            
            # Normalize lighting using CLAHE
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            l = clahe.apply(l)
            enhanced = cv2.merge([l, a, b])
            image = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            
            return image
            
        except Exception as e:
            logger.warning(f"[FaceRecognition] Preprocessing failed: {e}, using original")
            return image
    
    def detect_faces(self, image: np.ndarray) -> List[Dict]:
        
        try:
            # Use DeepFace for detection
            faces = DeepFace.extract_faces(
                img_path=image,
                detector_backend=self.detector_backend,
                enforce_detection=False,
                align=True
            )
            
            detected_faces = []
            for face in faces:
                if face.get('confidence', 0) >= self.detection_confidence:
                    detected_faces.append({
                        'facial_area': face['facial_area'],
                        'confidence': face['confidence'],
                        'face': face['face']
                    })
            
            logger.info(f"[FaceRecognition] Detected {len(detected_faces)} faces with confidence >= {self.detection_confidence}")
            return detected_faces
            
        except Exception as e:
            logger.error(f"[FaceRecognition] Face detection error: {e}")
            return []
    
    def extract_embedding(self, image: np.ndarray, enhance: bool = True) -> Optional[np.ndarray]:
       
        try:
            # Preprocess if requested
            if enhance:
                image = self.preprocess_image(image)
            
            # Extract embedding using DeepFace
            embedding_objs = DeepFace.represent(
                img_path=image,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                enforce_detection=True,
                align=True,
                normalization='base'
            )
            
            if not embedding_objs:
                logger.warning("[FaceRecognition] No embedding extracted")
                return None
            
            # Get first face embedding
            embedding = np.array(embedding_objs[0]['embedding'])
            
            # Normalize embedding
            embedding = embedding / np.linalg.norm(embedding)
            
            logger.info(f"[FaceRecognition] Extracted embedding of dimension {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"[FaceRecognition] Embedding extraction error: {e}")
            return None
    
    def assess_image_quality(self, image: np.ndarray) -> Dict[str, float]:
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Measure sharpness (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness = min(laplacian_var / 100.0, 1.0)  # Normalize to 0-1
            
            # Measure brightness
            brightness = np.mean(gray) / 255.0
            
            # Measure contrast
            contrast = np.std(gray) / 128.0
            
            # Overall quality score
            quality = (sharpness * 0.4 + 
                      min(abs(brightness - 0.5) * 2, 1.0) * 0.3 +
                      min(contrast, 1.0) * 0.3)
            
            return {
                'quality_score': round(quality, 3),
                'sharpness': round(sharpness, 3),
                'brightness': round(brightness, 3),
                'contrast': round(contrast, 3)
            }
            
        except Exception as e:
            logger.error(f"[FaceRecognition] Quality assessment error: {e}")
            return {
                'quality_score': 0.5,
                'sharpness': 0.0,
                'brightness': 0.0,
                'contrast': 0.0
            }
    
    def process_enrollment_images(self, base64_images: List[str]) -> Tuple[Optional[np.ndarray], List[Dict]]:
        
        embeddings = []
        quality_reports = []
        
        for idx, base64_img in enumerate(base64_images):
            try:
                # Convert base64 to image
                image = self.base64_to_image(base64_img)
                
                # Assess quality
                quality = self.assess_image_quality(image)
                
                # Skip low quality images
                if quality['quality_score'] < 0.3:
                    logger.warning(f"[FaceRecognition] Image {idx+1} rejected: low quality ({quality['quality_score']})")
                    quality_reports.append({
                        'image_index': idx + 1,
                        'status': 'rejected',
                        'reason': 'Low quality',
                        **quality
                    })
                    continue
                
                # Extract embedding
                embedding = self.extract_embedding(image, enhance=True)
                
                if embedding is not None:
                    embeddings.append(embedding)
                    quality_reports.append({
                        'image_index': idx + 1,
                        'status': 'accepted',
                        **quality
                    })
                    logger.info(f"[FaceRecognition] Image {idx+1} processed successfully")
                else:
                    quality_reports.append({
                        'image_index': idx + 1,
                        'status': 'rejected',
                        'reason': 'No face detected',
                        **quality
                    })
                    
            except Exception as e:
                logger.error(f"[FaceRecognition] Error processing image {idx+1}: {e}")
                quality_reports.append({
                    'image_index': idx + 1,
                    'status': 'error',
                    'reason': str(e)
                })
        
        # Check if we have enough valid embeddings
        if not embeddings:
            logger.error("[FaceRecognition] No valid embeddings extracted")
            return None, quality_reports
        
        # Average embeddings
        averaged_embedding = np.mean(embeddings, axis=0)
        
        # Normalize
        averaged_embedding = averaged_embedding / np.linalg.norm(averaged_embedding)
        
        logger.info(f"[FaceRecognition] Created averaged embedding from {len(embeddings)} images")
        
        return averaged_embedding, quality_reports
    
    def verify_face(self, image: np.ndarray, stored_embedding: np.ndarray) -> Tuple[bool, float]:
        
        try:
            # Extract embedding from new image
            new_embedding = self.extract_embedding(image, enhance=True)
            
            if new_embedding is None:
                return False, 0.0
            
            # Calculate cosine similarity
            similarity = np.dot(new_embedding, stored_embedding)
            
            # Convert to distance (0-1, lower is better)
            distance = 1 - similarity
            
            # Check if match
            is_match = distance < self.threshold
            
            # Convert to confidence (0-1, higher is better)
            confidence = 1 - distance
            
            logger.info(f"[FaceRecognition] Verification: match={is_match}, confidence={confidence:.3f}")
            
            return is_match, float(confidence)
            
        except Exception as e:
            logger.error(f"[FaceRecognition] Verification error: {e}")
            return False, 0.0
    
    def batch_verify(self, image: np.ndarray, embeddings_dict: Dict[int, np.ndarray]) -> List[Tuple[int, float]]:
        
        try:
            # Extract embedding from new image
            new_embedding = self.extract_embedding(image, enhance=True)
            
            if new_embedding is None:
                return []
            
            matches = []
            
            for user_id, stored_embedding in embeddings_dict.items():
                # Calculate cosine similarity
                similarity = np.dot(new_embedding, stored_embedding)
                confidence = float(similarity)
                
                # Only include if above threshold
                distance = 1 - similarity
                if distance < self.threshold:
                    matches.append((user_id, confidence))
            
            # Sort by confidence (highest first)
            matches.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"[FaceRecognition] Batch verification: found {len(matches)} matches")
            
            return matches
            
        except Exception as e:
            logger.error(f"[FaceRecognition] Batch verification error: {e}")
            return []


# Global instance
face_recognition_service = FaceRecognitionService()
