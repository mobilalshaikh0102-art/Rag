"""
Practical Examples for Using the Complaint Classifier
These examples show common real-world scenarios.
"""

import os
import sys
import json
from dotenv import load_dotenv

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()
from complaint_classifier import (
    ZeroShotClassifier,
    FewShotClassifier,
    Complaint,
    ComplaintCategory,
    ClassifierEvaluator
)
from advanced_features import (
    MultiLabelClassifier,
    ConfidenceFilter,
    ActiveLearner,
    ProductionMonitor,
    ABTestFramework
)


# ============================================================================
# Example 1: Simple Single Classification
# ============================================================================

def example_1_simple_classification():
    """
    Classify a single complaint using few-shot prompting.
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Simple Single Classification")
    print("="*70)
    
    # Create classifier
    classifier = FewShotClassifier(num_examples=6)
    
    # Define a complaint
    complaint = Complaint(
        id="complaint_001",
        message="I ordered at 7 PM and it's now 9:15 PM. Still no delivery! "
                "The app keeps saying 5 more minutes but nothing arrives. "
                "This is ridiculous."
    )
    
    # Classify
    result = classifier.classify(complaint)
    
    # Display result
    print(f"\nComplaint ID: {result.complaint_id}")
    print(f"Message: {complaint.message}")
    print(f"\n✅ Classification Result:")
    print(f"   Category: {result.predicted_category.value}")
    print(f"   Confidence: {result.confidence:.0%}")
    print(f"   Reasoning: {result.reasoning}")


# ============================================================================
# Example 2: Batch Classification
# ============================================================================

def example_2_batch_classification():
    """
    Classify multiple complaints efficiently.
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Batch Classification (10 complaints)")
    print("="*70)
    
    # Create classifier
    classifier = FewShotClassifier(num_examples=6)
    
    # Define batch of complaints
    complaints_data = [
        ("c001", "Waited 3 hours for food, absolutely unacceptable service."),
        ("c002", "Ordered pizza but got pasta instead, wrong order entirely."),
        ("c003", "Got my burger but fries are missing from the bag."),
        ("c004", "Food is cold, stale, and tastes like it's been sitting all day."),
        ("c005", "Been 2 hours and my order hasn't even left the restaurant."),
        ("c006", "I asked for no onions but the burger is full of them. Wrong order!"),
        ("c007", "Ordered 3 items but only got 2. One item missing completely."),
        ("c008", "Rice is mushy, curry is cold, overall very poor quality."),
        ("c009", "90 minutes for delivery on a simple order. Too slow!"),
        ("c010", "Sushi smells off and rice is warm. This is unsafe to eat."),
    ]
    
    complaints = [
        Complaint(id=cid, message=msg) 
        for cid, msg in complaints_data
    ]
    
    # Classify each complaint
    results = []
    print("\nClassifying...\n")
    
    for complaint in complaints:
        result = classifier.classify(complaint)
        results.append(result)
        print(f"✓ {result.complaint_id}: {result.predicted_category.value:20s} "
              f"(confidence: {result.confidence:.0%})")
    
    # Summary
    category_counts = {}
    for result in results:
        cat = result.predicted_category.value
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    print(f"\n📊 Summary:")
    for category, count in sorted(category_counts.items()):
        print(f"   {category:20s}: {count} complaints")


# ============================================================================
# Example 3: Zero-Shot vs Few-Shot Comparison
# ============================================================================

def example_3_zero_shot_vs_few_shot():
    """
    Compare zero-shot and few-shot on the same complaints.
    Shows how few-shot improves accuracy.
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Zero-Shot vs Few-Shot Comparison")
    print("="*70)
    
    # Test complaints with known categories
    test_cases = [
        (
            "c1",
            "Order promised at 8 PM, now it's 10 PM and still nothing!",
            ComplaintCategory.LATE_DELIVERY
        ),
        (
            "c2",
            "I specifically ordered vegetarian but got meat. Wrong item!",
            ComplaintCategory.WRONG_ITEM
        ),
        (
            "c3",
            "Ordered 5 items, received only 3. Missing 2 completely.",
            ComplaintCategory.MISSING_ITEM
        ),
        (
            "c4",
            "Food arrived cold and stale. Completely inedible quality.",
            ComplaintCategory.POOR_QUALITY
        ),
    ]
    
    # Create classifiers
    zero_shot = ZeroShotClassifier()
    few_shot = FewShotClassifier(num_examples=6)
    
    # Classify with both
    print("\nClassifications:\n")
    print(f"{'ID':5} {'Message':35} {'Actual':15} {'Zero-Shot':15} {'Few-Shot':15}")
    print("-" * 85)
    
    zero_shot_correct = 0
    few_shot_correct = 0
    
    for complaint_id, message, true_category in test_cases:
        complaint = Complaint(id=complaint_id, message=message)
        
        z_result = zero_shot.classify(complaint)
        f_result = few_shot.classify(complaint)
        
        z_correct = z_result.predicted_category == true_category
        f_correct = f_result.predicted_category == true_category
        
        zero_shot_correct += int(z_correct)
        few_shot_correct += int(f_correct)
        
        print(f"{complaint_id:5} {message[:35]:35} {true_category.value[:15]:15} "
              f"{z_result.predicted_category.value[:15]:15} "
              f"{f_result.predicted_category.value[:15]:15}")
    
    # Summary
    print("\n📊 Results:")
    print(f"   Zero-Shot: {zero_shot_correct}/4 correct ({zero_shot_correct/4:.0%})")
    print(f"   Few-Shot:  {few_shot_correct}/4 correct ({few_shot_correct/4:.0%})")
    print(f"   Improvement: {(few_shot_correct - zero_shot_correct)/4:+.0%}")


# ============================================================================
# Example 4: Multi-Label Classification
# ============================================================================

def example_4_multi_label_classification():
    """
    Handle complaints with multiple issues.
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Multi-Label Classification")
    print("="*70)
    
    # Create multi-label classifier
    classifier = MultiLabelClassifier(num_examples=6)
    
    # Complaint with multiple issues
    complaint = Complaint(
        id="complex_complaint",
        message="Waited 2.5 hours for my order to arrive (unacceptable!), "
                "and when it finally came, it was missing 3 items AND "
                "the food was cold and tasted horrible. This was my birthday dinner! "
                "I'm extremely disappointed with your service."
    )
    
    # Classify
    result = classifier.classify(complaint)
    
    # Display
    print(f"\nComplaint: {complaint.message}\n")
    print(f"✅ Multi-Label Results:")
    print(f"   PRIMARY issue: {result.primary_category.value}")
    print(f"   SECONDARY issues:")
    for i, category in enumerate(result.secondary_categories, 1):
        print(f"      {i}. {category.value}")
    print(f"   Overall confidence: {result.confidence:.0%}")


# ============================================================================
# Example 5: Confidence-Based Filtering & Human Review
# ============================================================================

def example_5_confidence_filtering():
    """
    Route predictions to human review based on confidence.
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Confidence-Based Filtering")
    print("="*70)
    
    # Classify several complaints
    classifier = FewShotClassifier(num_examples=6)
    
    test_messages = [
        "Order arrived 2 hours late",  # Clear → high confidence
        "Food not good quality",  # Ambiguous → low confidence
        "Item missing from order",  # Clear → high confidence
        "Something wrong with delivery",  # Very ambiguous → very low confidence
    ]
    
    complaints = [
        Complaint(id=f"c{i}", message=msg)
        for i, msg in enumerate(test_messages, 1)
    ]
    
    predictions = [classifier.classify(c) for c in complaints]
    
    # Filter by confidence
    filter = ConfidenceFilter(
        high_confidence_threshold=0.85,
        low_confidence_threshold=0.60
    )
    
    print("\nFiltering Results:\n")
    print(f"{'ID':5} {'Confidence':12} {'Action':15} {'Category':20}")
    print("-" * 52)
    
    for pred in predictions:
        filtered = filter.filter(pred)
        print(f"{pred.complaint_id:5} {pred.confidence:12.0%} "
              f"{filtered['action']:15} {pred.predicted_category.value:20}")
    
    # Summary
    auto_approved = sum(1 for p in predictions if filter.filter(p)['action'] == 'auto_approve')
    needs_review = sum(1 for p in predictions if filter.filter(p)['requires_human_review'])
    
    print(f"\n📊 Summary:")
    print(f"   Auto-approved: {auto_approved} (high confidence)")
    print(f"   Need review: {needs_review} (low confidence)")


# ============================================================================
# Example 6: Active Learning - Identify Hard Examples
# ============================================================================

def example_6_active_learning():
    """
    Identify which complaints would be most valuable to manually label.
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: Active Learning - Find Hard Examples")
    print("="*70)
    
    # Classify a batch
    classifier = FewShotClassifier(num_examples=6)
    
    test_messages = [
        "I'm not satisfied with my order",  # Vague
        "Order arrived 30 minutes late",  # Clear
        "Incorrect food sent",  # Clear
        "Complaint about food",  # Very vague
        "Missing items in my delivery",  # Clear
        "There was an issue",  # Vague
    ]
    
    complaints = [
        Complaint(id=f"c{i}", message=msg)
        for i, msg in enumerate(test_messages, 1)
    ]
    
    predictions = [classifier.classify(c) for c in complaints]
    
    # Find hard examples
    hard_examples = ActiveLearner.identify_hard_examples(predictions, n_examples=3)
    
    print("\nHard Examples (lowest confidence - most valuable to label):\n")
    print(f"{'Rank':5} {'ID':10} {'Confidence':12} {'Message Preview':50}")
    print("-" * 77)
    
    for rank, (complaint_id, confidence) in enumerate(hard_examples, 1):
        # Find original message
        msg = next(c.message for c in complaints if c.id == complaint_id)
        msg_preview = msg[:47] + "..." if len(msg) > 50 else msg
        print(f"{rank:5} {complaint_id:10} {confidence:12.0%} {msg_preview:50}")
    
    print("\n💡 Recommendation: Prioritize labeling these examples to improve the model.")


# ============================================================================
# Example 7: Production Monitoring
# ============================================================================

def example_7_production_monitoring():
    """
    Monitor classifier performance in production.
    """
    print("\n" + "="*70)
    print("EXAMPLE 7: Production Monitoring")
    print("="*70)
    
    # Simulate production batches
    monitor = ProductionMonitor()
    classifier = FewShotClassifier(num_examples=6)
    
    test_messages = [
        "Arrived late",
        "Wrong item",
        "Missing items",
        "Poor quality",
        "Very late delivery",
        "Wrong food completely",
        "Item missing",
        "Cold and stale",
    ]
    
    complaints = [
        Complaint(id=f"c{i}", message=msg)
        for i, msg in enumerate(test_messages, 1)
    ]
    
    predictions = [classifier.classify(c) for c in complaints]
    
    # Track batch
    metrics = monitor.track_batch(
        predictions,
        processing_time_ms=2500,  # 2.5 seconds for 8 items
        errors_count=0
    )
    
    # Display metrics
    print(f"\n📊 Batch Metrics:")
    print(f"   Total classified: {metrics.total_classified}")
    print(f"   Auto-approved: {metrics.auto_approved}")
    print(f"   Require review: {metrics.human_review_needed}")
    print(f"   Avg confidence: {metrics.average_confidence:.2f}")
    print(f"   Processing time: {metrics.avg_processing_time_ms:.0f}ms per item")
    
    print(f"\n📋 Category Distribution:")
    for category, count in metrics.category_distribution.items():
        print(f"   {category:20s}: {count}")
    
    # Check alerts
    alerts = monitor.check_alerts(metrics)
    if alerts:
        print(f"\n⚠️  Alerts:")
        for alert in alerts:
            print(f"   {alert}")
    else:
        print(f"\n✅ All metrics within normal range")


# ============================================================================
# Example 8: A/B Testing
# ============================================================================

def example_8_ab_testing():
    """
    Compare two strategies with A/B test.
    """
    print("\n" + "="*70)
    print("EXAMPLE 8: A/B Testing (Zero-Shot vs Few-Shot)")
    print("="*70)
    
    # Create test data with known labels
    test_data = [
        ("Waiting 2 hours", ComplaintCategory.LATE_DELIVERY),
        ("Got wrong pizza", ComplaintCategory.WRONG_ITEM),
        ("Fries missing", ComplaintCategory.MISSING_ITEM),
        ("Food cold and stale", ComplaintCategory.POOR_QUALITY),
    ]
    
    test_complaints = [
        Complaint(id=f"c{i}", message=msg)
        for i, (msg, _) in enumerate(test_data, 1)
    ]
    
    ground_truth = [
        Complaint(id=f"c{i}", message=msg, true_category=cat)
        for i, (msg, cat) in enumerate(test_data, 1)
    ]
    
    # Create classifiers
    zero_shot = ZeroShotClassifier()
    few_shot = FewShotClassifier(num_examples=6)
    
    # Run A/B test
    ab_test = ABTestFramework()
    result = ab_test.run_ab_test(
        zero_shot,
        few_shot,
        test_complaints,
        ground_truth,
        test_id="test_001"
    )
    
    # Display results
    ab_test.print_test_result(result)


# ============================================================================
# Example 9: Save/Load Predictions
# ============================================================================

def example_9_save_predictions():
    """
    Save predictions to JSON for later analysis.
    """
    print("\n" + "="*70)
    print("EXAMPLE 9: Save Predictions to JSON")
    print("="*70)
    
    # Classify some complaints
    classifier = FewShotClassifier(num_examples=6)
    
    complaints = [
        Complaint("c1", "Order 3 hours late"),
        Complaint("c2", "Wrong item received"),
        Complaint("c3", "Missing items"),
    ]
    
    predictions = [classifier.classify(c) for c in complaints]
    
    # Save to JSON
    output_data = []
    for pred in predictions:
        output_data.append({
            "complaint_id": pred.complaint_id,
            "predicted_category": pred.predicted_category.value,
            "confidence": pred.confidence,
            "reasoning": pred.reasoning
        })
    
    with open("predictions.json", "w") as f:
        json.dump(output_data, f, indent=2)
    
    print("\n✅ Predictions saved to predictions.json")
    print("\nSample of saved data:")
    print(json.dumps(output_data[0], indent=2))


# ============================================================================
# Main
# ============================================================================

def main():
    """Run all examples"""
    
    print("\n" + "="*70)
    print("COMPLAINT CLASSIFIER - PRACTICAL EXAMPLES")
    print("="*70)
    
    examples = [
        ("1", "Simple Classification", example_1_simple_classification),
        ("2", "Batch Classification", example_2_batch_classification),
        ("3", "Zero-Shot vs Few-Shot", example_3_zero_shot_vs_few_shot),
        ("4", "Multi-Label Classification", example_4_multi_label_classification),
        ("5", "Confidence Filtering", example_5_confidence_filtering),
        ("6", "Active Learning", example_6_active_learning),
        ("7", "Production Monitoring", example_7_production_monitoring),
        ("8", "A/B Testing", example_8_ab_testing),
        ("9", "Save Predictions", example_9_save_predictions),
    ]
    
    print("\nAvailable examples:")
    for num, title, _ in examples:
        print(f"  {num}. {title}")
    
    print("\n" + "="*70)
    print("Running all examples...")
    print("="*70)
    
    # Run each example
    for num, title, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n❌ Error in Example {num}: {str(e)}")
    
    print("\n" + "="*70)
    print("✅ All examples completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
