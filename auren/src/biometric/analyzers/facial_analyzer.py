"""Updated facial analyzer with complete type annotations."""

from typing import Optional, Tuple, List, Dict, Any
import numpy as np
import numpy.typing as npt
from pathlib import Path
import cv2
import mediapipe as mp

from src.protocols.mirage.mirage_protocol import BiometricScores

class FacialAnalyzer:
    """Facial biometric analysis with type safety."""
    
    def __init__(self) -> None:
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            min_detection_confidence=0.5
        )
    
    def analyze(self, image_path: str) -> BiometricScores:
        """Analyze facial biometrics from image."""
        landmarks = self._detect_landmarks(image_path)
        
        if landmarks is None:
            return BiometricScores()  # Return default scores
        
        scores = BiometricScores()
        scores.ptosis_score = self._calculate_ptosis(landmarks)
        scores.inflammation_score = self._calculate_inflammation(landmarks)
        scores.symmetry_score = self._calculate_symmetry(landmarks)
        
        return scores
    
    def _detect_landmarks(self, image_path: str) -> Optional[npt.NDArray[np.float64]]:
        """Detect facial landmarks from image."""
        image = cv2.imread(image_path)
        if image is None:
            return None
        
        results = self.face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        if not results.multi_face_landmarks:
            return None
        
        # Convert to numpy array
        landmarks = np.array([
            [lm.x * image.shape[1], lm.y * image.shape[0]]
            for lm in results.multi_face_landmarks[0].landmark
        ])
        
        return landmarks
    
    def _calculate_ptosis(self, landmarks: npt.NDArray[np.float64]) -> float:
        """Calculate ptosis score from eye landmarks."""
        # Eye indices for MediaPipe (different from dlib)
        left_eye_indices = [33, 160, 158, 133, 153, 144]
        right_eye_indices = [362, 385, 387, 263, 373, 380]
        
        left_ear = self._eye_aspect_ratio(landmarks[left_eye_indices])
        right_ear = self._eye_aspect_ratio(landmarks[right_eye_indices])
        
        # Convert EAR to ptosis score (0-10 scale)
        # Lower EAR = higher ptosis
        avg_ear = (left_ear + right_ear) / 2.0
        ptosis_score = max(0.0, min(10.0, (0.3 - avg_ear) * 33.33))
        
        return float(ptosis_score)
    
    def _eye_aspect_ratio(self, eye: npt.NDArray[np.float64]) -> float:
        """Calculate eye aspect ratio."""
        # Vertical distances
        A = float(np.linalg.norm(eye[1] - eye[5]))
        B = float(np.linalg.norm(eye[2] - eye[4]))
        
        # Horizontal distance
        C = float(np.linalg.norm(eye[0] - eye[3]))
        
        if C == 0:
            return 0.0
        
        ear = (A + B) / (2.0 * C)
        return float(ear)
    
    def _calculate_inflammation(self, landmarks: npt.NDArray[np.float64]) -> float:
        """Calculate inflammation score (placeholder for now)."""
        # TODO: Implement actual inflammation detection
        # This would require color analysis around eye areas
        return 2.0  # Default neutral score
    
    def _calculate_symmetry(self, landmarks: npt.NDArray[np.float64]) -> float:
        """Calculate facial symmetry score."""
        # Get face center
        center_x = float(np.mean(landmarks[:, 0]))
        
        # Mirror landmarks across center
        mirrored = landmarks.copy()
        mirrored[:, 0] = 2 * center_x - mirrored[:, 0]
        
        # Calculate differences
        differences = np.linalg.norm(landmarks - mirrored, axis=1)
        
        # Convert to 0-10 scale (lower difference = higher symmetry)
        avg_diff = float(np.mean(differences))
        symmetry_score = max(0.0, min(10.0, 10.0 - (avg_diff / 10.0)))
        
        return float(symmetry_score)
