"""
Confidence Scorer for OpenAI Email Responses
Determines whether AI-generated responses can be auto-sent or need human review.
"""

import re
import logging
from typing import Dict, Tuple, List

logger = logging.getLogger(__name__)

class ConfidenceScorer:
    """
    Scores the confidence of AI-generated email responses.
    """
    
    def __init__(self):
        # High confidence keywords that indicate clear intent
        self.high_confidence_keywords = [
            'invoice', 'receipt', 'payment', 'ctn', 'bl', 'container',
            'price', 'cost', 'fee', 'how much', 'when', 'where',
            'status', 'track', 'document', 'contact'
        ]
        
        # Low confidence indicators
        self.low_confidence_indicators = [
            'urgent', 'emergency', 'problem', 'issue', 'wrong', 'error',
            'complaint', 'refund', 'cancel', 'dispute', 'legal',
            'not received', 'missing', 'damaged', 'lost'
        ]
        
        # BL number patterns
        self.bl_pattern = r'\bBL\d{3,}\b'
        
        # Response quality indicators
        self.quality_indicators = {
            'has_greeting': False,
            'has_clear_structure': False,
            'has_action_items': False,
            'has_contact_info': False,
            'response_length': 0
        }
    
    def extract_bl_numbers(self, text: str) -> List[str]:
        """Extract BL numbers from text."""
        return re.findall(self.bl_pattern, text, re.IGNORECASE)
    
    def analyze_response_quality(self, response: str) -> Dict:
        """Analyze the quality of the AI response."""
        quality = {
            'has_greeting': any(greeting in response.lower() for greeting in ['thank you', 'dear', 'hello', 'hi']),
            'has_clear_structure': len(response.split('\n\n')) >= 2,
            'has_action_items': any(item in response.lower() for item in ['please', 'next', 'step', 'provide']),
            'has_contact_info': any(contact in response.lower() for contact in ['contact', 'email', 'phone', 'call']),
            'response_length': len(response)
        }
        return quality
    
    def calculate_confidence_score(self, 
                                 original_email: str, 
                                 ai_response: str, 
                                 classification: str,
                                 bl_numbers: List[str]) -> Tuple[float, Dict]:
        """
        Calculate confidence score for AI response.
        
        Returns:
            (confidence_score, reasoning_dict)
        """
        score = 0.0
        reasoning = {}
        
        # Base score based on classification
        classification_scores = {
            'invoice_request': 0.8,
            'payment_receipt': 0.9,
            'general_enquiry': 0.7
        }
        score += classification_scores.get(classification, 0.5)
        reasoning['classification_score'] = classification_scores.get(classification, 0.5)
        
        # BL number presence (higher confidence if BL numbers found)
        if bl_numbers:
            score += 0.1
            reasoning['bl_numbers_found'] = True
        else:
            reasoning['bl_numbers_found'] = False
        
        # High confidence keywords in original email
        high_conf_count = sum(1 for keyword in self.high_confidence_keywords 
                             if keyword.lower() in original_email.lower())
        if high_conf_count > 0:
            score += min(0.1 * high_conf_count, 0.3)
        reasoning['high_confidence_keywords'] = high_conf_count
        
        # Low confidence indicators (reduce score)
        low_conf_count = sum(1 for indicator in self.low_confidence_indicators 
                            if indicator.lower() in original_email.lower())
        if low_conf_count > 0:
            score -= min(0.2 * low_conf_count, 0.4)
        reasoning['low_confidence_indicators'] = low_conf_count
        
        # Response quality analysis
        quality = self.analyze_response_quality(ai_response)
        reasoning['response_quality'] = quality
        
        # Quality bonuses
        if quality['has_greeting']:
            score += 0.05
        if quality['has_clear_structure']:
            score += 0.05
        if quality['has_action_items']:
            score += 0.05
        if quality['response_length'] > 100:
            score += 0.05
        
        # Cap score between 0 and 1
        score = max(0.0, min(1.0, score))
        
        reasoning['final_score'] = score
        reasoning['auto_send_recommended'] = score >= 0.8
        
        return score, reasoning
    
    def get_auto_send_recommendation(self, 
                                   original_email: str, 
                                   ai_response: str, 
                                   classification: str,
                                   bl_numbers: List[str]) -> Dict:
        """
        Get auto-send recommendation with detailed reasoning.
        """
        score, reasoning = self.calculate_confidence_score(
            original_email, ai_response, classification, bl_numbers
        )
        
        recommendation = {
            'confidence_score': score,
            'auto_send': score >= 0.8,
            'reasoning': reasoning,
            'recommendation': self._get_recommendation_text(score, reasoning)
        }
        
        logger.info(f"Confidence Score: {score:.2f} - Auto-send: {recommendation['auto_send']}")
        
        return recommendation
    
    def _get_recommendation_text(self, score: float, reasoning: Dict) -> str:
        """Get human-readable recommendation text."""
        if score >= 0.9:
            return "HIGH CONFIDENCE - Safe to auto-send"
        elif score >= 0.8:
            return "GOOD CONFIDENCE - Recommended for auto-send"
        elif score >= 0.6:
            return "MODERATE CONFIDENCE - Review recommended"
        elif score >= 0.4:
            return "LOW CONFIDENCE - Manual review required"
        else:
            return "VERY LOW CONFIDENCE - Manual review essential"
    
    def should_auto_send(self, 
                        original_email: str, 
                        ai_response: str, 
                        classification: str,
                        bl_numbers: List[str]) -> bool:
        """
        Simple boolean check for auto-send.
        """
        score, _ = self.calculate_confidence_score(original_email, ai_response, classification, bl_numbers)
        return score >= 0.8

# Global instance
confidence_scorer = ConfidenceScorer() 