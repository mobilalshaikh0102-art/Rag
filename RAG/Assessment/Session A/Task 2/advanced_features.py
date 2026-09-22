"""
Advanced Features for Complaint Classifier
- Multi-label classification
- Confidence-based filtering  
- Active learning
- Production monitoring
- A/B testing framework
"""

import os
import sys
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict
import anthropic
from dotenv import load_dotenv

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()
from complaint_classifier import ComplaintCategory, Complaint, Classification, FewShotClassifier, is_mock_mode


# ============================================================================
# Feature 1: Multi-Label Classification
# ============================================================================

@dataclass
class MultiLabelClassification:
    """Result when a complaint maps to multiple categories"""
    complaint_id: str
    primary_category: ComplaintCategory
    secondary_categories: List[ComplaintCategory]
    confidence: float
    raw_response: str


class MultiLabelClassifier(FewShotClassifier):
    """
    Handles complaints that have multiple issues.
    Example: "Arrived late AND missing items AND poor quality"
    """
    
    def __init__(self, num_examples: int = 6, model: str = "claude-haiku-4-5-20251001"):
        super().__init__(num_examples=num_examples, model=model)
        self.use_case = "multi-label"
    
    def get_system_prompt(self) -> str:
        """System prompt for multi-label classification"""
        examples_text = self._format_examples()
        
        return f"""You are a complaint classifier for a food delivery platform.

Your task: Identify ALL issues in a complaint, ranked by severity.

Classify into these categories:
- 'Late Delivery': Order arrived after promised time
- 'Wrong Item': Received incorrect food items
- 'Missing Item': Part of order is missing
- 'Poor Quality': Food quality issues

Examples:
{examples_text}

Important:
1. Identify PRIMARY issue (most serious)
2. List any SECONDARY issues in order of severity
3. A complaint may have 1-4 issues

Response format:
{{
    "primary_category": "Late Delivery",
    "secondary_categories": ["Missing Item", "Poor Quality"],
    "confidence": 0.88,
    "reasoning": "Order was 2 hours late, missing drinks, food was cold"
}}"""
    
    def classify(self, complaint: Complaint) -> MultiLabelClassification:
        """Classify with multiple labels"""
        if self.mock_mode:
            msg_lower = complaint.message.lower()
            detected_cats = []
            if any(k in msg_lower for k in ["late", "hour", "waiting", "delay", "arrive", "pm", "minutes"]):
                detected_cats.append(ComplaintCategory.LATE_DELIVERY)
            if any(k in msg_lower for k in ["wrong", "different", "instead", "meat pizza"]):
                detected_cats.append(ComplaintCategory.WRONG_ITEM)
            if any(k in msg_lower for k in ["missing", "where", "only got", "paid for", "didn't get", "drink", "fries"]):
                detected_cats.append(ComplaintCategory.MISSING_ITEM)
            if any(k in msg_lower for k in ["cold", "soggy", "rotten", "smell", "taste", "quality", "disgusting", "inedible", "stale"]):
                detected_cats.append(ComplaintCategory.POOR_QUALITY)
            
            if not detected_cats:
                detected_cats = [ComplaintCategory.POOR_QUALITY]
            
            primary = detected_cats[0]
            secondary = detected_cats[1:]
            confidence = 0.88 if len(detected_cats) > 1 else 0.92
            
            raw_response = json.dumps({
                "primary_category": primary.value,
                "secondary_categories": [c.value for c in secondary],
                "confidence": confidence,
                "reasoning": f"Identified issues: {', '.join([c.value for c in detected_cats])}"
            }, indent=2)
            
            return MultiLabelClassification(
                complaint_id=complaint.id,
                primary_category=primary,
                secondary_categories=secondary,
                confidence=confidence,
                raw_response=raw_response
            )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=256,
            system=self.get_system_prompt(),
            messages=[{
                "role": "user",
                "content": f"Classify all issues: {complaint.message}"
            }]
        )
        
        response_text = response.content[0].text
        try:
            result = json.loads(response_text)
            primary = ComplaintCategory(result["primary_category"])
            secondary = [
                ComplaintCategory(cat) 
                for cat in result.get("secondary_categories", [])
            ]
            confidence = result.get("confidence", 0.5)
        except (json.JSONDecodeError, ValueError):
            primary = ComplaintCategory.POOR_QUALITY
            secondary = []
            confidence = 0.3
        
        return MultiLabelClassification(
            complaint_id=complaint.id,
            primary_category=primary,
            secondary_categories=secondary,
            confidence=confidence,
            raw_response=response_text
        )


# ============================================================================
# Feature 2: Confidence-Based Filtering
# ============================================================================

class ConfidenceFilter:
    """
    Routes low-confidence predictions to human review.
    Improves quality while reducing unnecessary human intervention.
    """
    
    def __init__(self, 
                 high_confidence_threshold: float = 0.85,
                 low_confidence_threshold: float = 0.60):
        """
        Args:
            high_confidence_threshold: Predictions above this are auto-approved
            low_confidence_threshold: Below this go to human review
        """
        self.high_threshold = high_confidence_threshold
        self.low_threshold = low_confidence_threshold
    
    def filter(self, prediction: Classification) -> Dict:
        """
        Categorize prediction by confidence level.
        
        Returns:
            {
                "action": "auto_approve" | "review" | "reject",
                "confidence_level": "high" | "medium" | "low",
                "prediction": Classification,
                "requires_human_review": bool
            }
        """
        
        if prediction.confidence >= self.high_threshold:
            action = "auto_approve"
            confidence_level = "high"
            requires_review = False
        elif prediction.confidence >= self.low_threshold:
            action = "review"
            confidence_level = "medium"
            requires_review = True
        else:
            action = "review"
            confidence_level = "low"
            requires_review = True
        
        return {
            "action": action,
            "confidence_level": confidence_level,
            "prediction": prediction,
            "requires_human_review": requires_review
        }


# ============================================================================
# Feature 3: Active Learning
# ============================================================================

class ActiveLearner:
    """
    Identifies which unlabeled examples would be most valuable to label.
    Reduces labeling effort for improving model.
    """
    
    @staticmethod
    def identify_hard_examples(predictions: List[Classification],
                              n_examples: int = 10) -> List[Tuple[str, float]]:
        """
        Find low-confidence predictions (hardest for model).
        These are most valuable to label for improving training data.
        
        Args:
            predictions: List of Classification objects
            n_examples: How many hard examples to return
        
        Returns:
            List of (complaint_id, confidence) tuples, sorted by lowest confidence
        """
        # Sort by confidence (ascending)
        hard_examples = sorted(
            [(p.complaint_id, p.confidence) for p in predictions],
            key=lambda x: x[1]
        )
        
        return hard_examples[:n_examples]
    
    @staticmethod
    def identify_uncertain_examples(predictions: List[Classification],
                                   threshold: float = 0.55) -> List[str]:
        """
        Find predictions near decision boundaries (0.50-0.60 confidence).
        These indicate boundary cases and are useful training examples.
        """
        uncertain = [
            p.complaint_id 
            for p in predictions 
            if 0.45 <= p.confidence <= 0.65
        ]
        return uncertain
    
    @staticmethod
    def identify_disagreement_examples(predictions1: List[Classification],
                                      predictions2: List[Classification]) -> List[str]:
        """
        Find examples where two models disagree.
        Useful for identifying systematic issues.
        """
        disagreements = []
        pred_dict2 = {p.complaint_id: p for p in predictions2}
        
        for pred1 in predictions1:
            if pred1.complaint_id in pred_dict2:
                pred2 = pred_dict2[pred1.complaint_id]
                if pred1.predicted_category != pred2.predicted_category:
                    disagreements.append(pred1.complaint_id)
        
        return disagreements


# ============================================================================
# Feature 4: Production Monitoring
# ============================================================================

@dataclass
class ClassificationMetrics:
    """Metrics for monitoring classifier in production"""
    timestamp: str
    total_classified: int
    auto_approved: int  # high confidence
    human_review_needed: int  # low confidence
    average_confidence: float
    category_distribution: Dict[str, int]
    avg_processing_time_ms: float
    error_rate: float  # Failed classifications


class ProductionMonitor:
    """
    Tracks classifier performance and health metrics in production.
    Alerts on anomalies.
    """
    
    def __init__(self):
        self.metrics_history = []
        self.alert_thresholds = {
            "min_confidence": 0.70,
            "max_review_rate": 0.30,
            "error_rate": 0.05
        }
    
    def track_batch(self,
                   predictions: List[Classification],
                   processing_time_ms: float,
                   errors_count: int = 0) -> ClassificationMetrics:
        """
        Record metrics for a batch of classifications.
        
        Args:
            predictions: List of Classification results
            processing_time_ms: Total processing time
            errors_count: Number of failed classifications
        """
        
        confidence_filter = ConfidenceFilter()
        auto_approved = 0
        human_review = 0
        
        for pred in predictions:
            result = confidence_filter.filter(pred)
            if result["action"] == "auto_approve":
                auto_approved += 1
            else:
                human_review += 1
        
        # Category distribution
        category_dist = defaultdict(int)
        for pred in predictions:
            category_dist[pred.predicted_category.value] += 1
        
        avg_confidence = sum(p.confidence for p in predictions) / len(predictions)
        error_rate = errors_count / len(predictions) if predictions else 0
        
        metrics = ClassificationMetrics(
            timestamp=datetime.now().isoformat(),
            total_classified=len(predictions),
            auto_approved=auto_approved,
            human_review_needed=human_review,
            average_confidence=avg_confidence,
            category_distribution=dict(category_dist),
            avg_processing_time_ms=processing_time_ms / len(predictions) if predictions else 0,
            error_rate=error_rate
        )
        
        self.metrics_history.append(metrics)
        return metrics
    
    def check_alerts(self, metrics: ClassificationMetrics) -> List[str]:
        """
        Check if metrics exceed alert thresholds.
        
        Returns:
            List of alert messages
        """
        alerts = []
        
        if metrics.average_confidence < self.alert_thresholds["min_confidence"]:
            alerts.append(
                f"⚠️  Low avg confidence: {metrics.average_confidence:.2f} "
                f"(threshold: {self.alert_thresholds['min_confidence']})"
            )
        
        review_rate = metrics.human_review_needed / metrics.total_classified
        if review_rate > self.alert_thresholds["max_review_rate"]:
            alerts.append(
                f"⚠️  High review rate: {review_rate:.1%} "
                f"(threshold: {self.alert_thresholds['max_review_rate']:.1%})"
            )
        
        if metrics.error_rate > self.alert_thresholds["error_rate"]:
            alerts.append(
                f"⚠️  High error rate: {metrics.error_rate:.1%} "
                f"(threshold: {self.alert_thresholds['error_rate']:.1%})"
            )
        
        return alerts
    
    def get_summary(self) -> Dict:
        """Get summary statistics across all recorded metrics"""
        if not self.metrics_history:
            return {}
        
        total_classified = sum(m.total_classified for m in self.metrics_history)
        total_auto_approved = sum(m.auto_approved for m in self.metrics_history)
        avg_confidence = sum(m.average_confidence for m in self.metrics_history) / len(self.metrics_history)
        
        return {
            "batches_processed": len(self.metrics_history),
            "total_classified": total_classified,
            "total_auto_approved": total_auto_approved,
            "approval_rate": total_auto_approved / total_classified if total_classified > 0 else 0,
            "average_confidence": avg_confidence,
            "latest_timestamp": self.metrics_history[-1].timestamp if self.metrics_history else None
        }


# ============================================================================
# Feature 5: A/B Testing Framework
# ============================================================================

class ABTestFramework:
    """
    Framework for running A/B tests comparing different strategies.
    """
    
    @dataclass
    class TestResult:
        test_id: str
        strategy_a: str
        strategy_b: str
        accuracy_a: float
        accuracy_b: float
        confidence_a: float
        confidence_b: float
        cost_a: float  # tokens
        cost_b: float  # tokens
        winner: str  # "A", "B", or "tie"
        statistical_significance: bool
    
    def __init__(self):
        self.test_results = []
    
    def run_ab_test(self,
                   classifier_a,
                   classifier_b,
                   test_complaints: List[Complaint],
                   ground_truth: List[Complaint],
                   test_id: str = "test_1") -> TestResult:
        """
        Run A/B test comparing two classifiers.
        
        Args:
            classifier_a: First classifier (baseline)
            classifier_b: Second classifier (variant)
            test_complaints: Complaints to classify
            ground_truth: True labels for evaluation
            test_id: Identifier for this test
        """
        
        # Run classifier A
        predictions_a = []
        for complaint in test_complaints:
            pred = classifier_a.classify(complaint)
            predictions_a.append(pred)
        
        # Run classifier B
        predictions_b = []
        for complaint in test_complaints:
            pred = classifier_b.classify(complaint)
            predictions_b.append(pred)
        
        # Evaluate both
        correct_a = sum(
            1 for pred, truth in zip(predictions_a, ground_truth)
            if pred.predicted_category == truth.true_category
        )
        accuracy_a = correct_a / len(predictions_a)
        
        correct_b = sum(
            1 for pred, truth in zip(predictions_b, ground_truth)
            if pred.predicted_category == truth.true_category
        )
        accuracy_b = correct_b / len(predictions_b)
        
        # Average confidence
        conf_a = sum(p.confidence for p in predictions_a) / len(predictions_a)
        conf_b = sum(p.confidence for p in predictions_b) / len(predictions_b)
        
        # Estimate costs (tokens)
        cost_a = len(test_complaints) * 900  # Estimate
        cost_b = len(test_complaints) * 900
        
        # Determine winner
        if accuracy_a > accuracy_b + 0.05:  # 5% margin
            winner = "A"
            sig = True
        elif accuracy_b > accuracy_a + 0.05:
            winner = "B"
            sig = True
        else:
            winner = "tie"
            sig = False
        
        result = self.TestResult(
            test_id=test_id,
            strategy_a=classifier_a.use_case,
            strategy_b=classifier_b.use_case,
            accuracy_a=accuracy_a,
            accuracy_b=accuracy_b,
            confidence_a=conf_a,
            confidence_b=conf_b,
            cost_a=cost_a,
            cost_b=cost_b,
            winner=winner,
            statistical_significance=sig
        )
        
        self.test_results.append(result)
        return result
    
    def print_test_result(self, result: TestResult):
        """Print formatted A/B test results"""
        print(f"\n{'='*70}")
        print(f"A/B Test: {result.test_id}")
        print(f"{'='*70}")
        print(f"\nStrategy A ({result.strategy_a}):")
        print(f"  Accuracy:  {result.accuracy_a:.1%}")
        print(f"  Confidence: {result.confidence_a:.2f}")
        print(f"  Token Cost: {result.cost_a:,}")
        
        print(f"\nStrategy B ({result.strategy_b}):")
        print(f"  Accuracy:  {result.accuracy_b:.1%}")
        print(f"  Confidence: {result.confidence_b:.2f}")
        print(f"  Token Cost: {result.cost_b:,}")
        
        print(f"\n🏆 Winner: Strategy {result.winner}")
        print(f"Significant: {'Yes ✓' if result.statistical_significance else 'No'}")
        print(f"{'='*70}\n")


# ============================================================================
# Integration Example
# ============================================================================

def demo_advanced_features():
    """Demonstrate all advanced features"""
    from complaint_classifier import ZeroShotClassifier, FewShotClassifier, ADDITIONAL_TEST_EXAMPLES
    
    print("🚀 Advanced Features Demo")
    print("=" * 70)
    
    # 1. Multi-Label Classification
    print("\n1️⃣  Multi-Label Classification")
    multi_classifier = MultiLabelClassifier(num_examples=6)
    complaint = ADDITIONAL_TEST_EXAMPLES[0]
    multi_result = multi_classifier.classify(complaint)
    print(f"Complaint: {complaint.message[:60]}...")
    print(f"Primary: {multi_result.primary_category.value}")
    print(f"Secondary: {[c.value for c in multi_result.secondary_categories]}")
    
    # 2. Confidence Filtering
    print("\n2️⃣  Confidence-Based Filtering")
    few_shot = FewShotClassifier(num_examples=6)
    predictions = [few_shot.classify(c) for c in ADDITIONAL_TEST_EXAMPLES[:3]]
    filter = ConfidenceFilter(high_confidence_threshold=0.80)
    
    for pred in predictions:
        filtered = filter.filter(pred)
        print(f"ID: {pred.complaint_id:10s} | Confidence: {pred.confidence:.2f} | "
              f"Action: {filtered['action']}")
    
    # 3. Active Learning
    print("\n3️⃣  Active Learning - Hard Examples")
    hard_examples = ActiveLearner.identify_hard_examples(predictions, n_examples=2)
    print("Examples most valuable to label for improvement:")
    for complaint_id, confidence in hard_examples:
        print(f"  {complaint_id}: confidence={confidence:.2f}")
    
    # 4. Production Monitoring
    print("\n4️⃣  Production Monitoring")
    monitor = ProductionMonitor()
    metrics = monitor.track_batch(predictions, processing_time_ms=1500)
    print(f"Total classified: {metrics.total_classified}")
    print(f"Auto-approved: {metrics.auto_approved}")
    print(f"Require review: {metrics.human_review_needed}")
    print(f"Avg confidence: {metrics.average_confidence:.2f}")
    
    alerts = monitor.check_alerts(metrics)
    for alert in alerts:
        print(f"  {alert}")
    
    # 5. A/B Testing
    print("\n5️⃣  A/B Testing Framework")
    ab_test = ABTestFramework()
    zero_shot = ZeroShotClassifier()
    few_shot = FewShotClassifier(num_examples=6)
    
    # Use only first 2 examples to save API calls in demo
    test_set = ADDITIONAL_TEST_EXAMPLES[:2]
    result = ab_test.run_ab_test(
        zero_shot,
        few_shot,
        test_set,
        test_set,
        test_id="demo_test"
    )
    ab_test.print_test_result(result)
    
    print("✅ Advanced Features Demo Complete!")


if __name__ == "__main__":
    demo_advanced_features()
