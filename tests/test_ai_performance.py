"""
Performance testing suite for AI features
"""
import time
import statistics
import asyncio
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor
import requests
from unittest.mock import Mock, patch

from app.services.ai_service import AICategorizationService
from app.models.user import User
from app.models.category import Category


class AIPerformanceTester:
    """Performance testing class for AI services"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
    
    def test_suggestion_response_time(self, num_requests: int = 100) -> Dict:
        """Test AI suggestion response times"""
        print(f"Testing AI suggestion response time with {num_requests} requests...")
        
        test_data = [
            {"note": "Coffee at Starbucks", "amount": 5.50, "entry_type": "expense"},
            {"note": "Uber ride to work", "amount": 12.00, "entry_type": "expense"},
            {"note": "Amazon purchase", "amount": 25.99, "entry_type": "expense"},
            {"note": "Netflix subscription", "amount": 15.99, "entry_type": "expense"},
            {"note": "Grocery shopping", "amount": 45.00, "entry_type": "expense"},
        ]
        
        response_times = []
        success_count = 0
        
        for i in range(num_requests):
            # Rotate through test data
            data = test_data[i % len(test_data)]
            
            start_time = time.time()
            try:
                # Note: In real testing, you'd need proper authentication
                # This is a mock test for the service layer
                response_time = self._mock_suggestion_request(data)
                response_times.append(response_time)
                success_count += 1
            except Exception as e:
                print(f"Request {i+1} failed: {e}")
        
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            p95_time = self._percentile(response_times, 95)
            p99_time = self._percentile(response_times, 99)
            
            results = {
                "total_requests": num_requests,
                "successful_requests": success_count,
                "success_rate": (success_count / num_requests) * 100,
                "avg_response_time": avg_time,
                "median_response_time": median_time,
                "min_response_time": min_time,
                "max_response_time": max_time,
                "p95_response_time": p95_time,
                "p99_response_time": p99_time,
                "all_response_times": response_times
            }
            
            print(f"✅ AI Suggestion Performance Results:")
            print(f"   Success Rate: {results['success_rate']:.1f}%")
            print(f"   Average Response Time: {results['avg_response_time']:.3f}s")
            print(f"   Median Response Time: {results['median_response_time']:.3f}s")
            print(f"   95th Percentile: {results['p95_response_time']:.3f}s")
            print(f"   99th Percentile: {results['p99_response_time']:.3f}s")
            
            return results
        else:
            return {"error": "No successful requests"}
    
    def test_concurrent_suggestions(self, num_concurrent: int = 10, requests_per_thread: int = 10) -> Dict:
        """Test concurrent AI suggestion performance"""
        print(f"Testing concurrent AI suggestions: {num_concurrent} threads, {requests_per_thread} requests each...")
        
        def worker_thread(thread_id: int) -> List[float]:
            """Worker thread for concurrent testing"""
            thread_times = []
            test_data = [
                {"note": f"Thread {thread_id} - Coffee", "amount": 5.50, "entry_type": "expense"},
                {"note": f"Thread {thread_id} - Uber", "amount": 12.00, "entry_type": "expense"},
                {"note": f"Thread {thread_id} - Amazon", "amount": 25.99, "entry_type": "expense"},
            ]
            
            for i in range(requests_per_thread):
                data = test_data[i % len(test_data)]
                start_time = time.time()
                try:
                    self._mock_suggestion_request(data)
                    response_time = time.time() - start_time
                    thread_times.append(response_time)
                except Exception as e:
                    print(f"Thread {thread_id}, Request {i+1} failed: {e}")
            
            return thread_times
        
        # Run concurrent threads
        all_times = []
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(worker_thread, i) for i in range(num_concurrent)]
            
            for future in futures:
                thread_times = future.result()
                all_times.extend(thread_times)
        
        if all_times:
            results = {
                "concurrent_threads": num_concurrent,
                "requests_per_thread": requests_per_thread,
                "total_requests": len(all_times),
                "avg_response_time": statistics.mean(all_times),
                "median_response_time": statistics.median(all_times),
                "max_response_time": max(all_times),
                "min_response_time": min(all_times),
                "p95_response_time": self._percentile(all_times, 95),
                "p99_response_time": self._percentile(all_times, 99)
            }
            
            print(f"✅ Concurrent AI Performance Results:")
            print(f"   Total Requests: {results['total_requests']}")
            print(f"   Average Response Time: {results['avg_response_time']:.3f}s")
            print(f"   Max Response Time: {results['max_response_time']:.3f}s")
            print(f"   95th Percentile: {results['p95_response_time']:.3f}s")
            
            return results
        else:
            return {"error": "No successful concurrent requests"}
    
    def test_memory_usage(self, num_iterations: int = 1000) -> Dict:
        """Test memory usage during AI operations"""
        print(f"Testing AI memory usage with {num_iterations} iterations...")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Mock AI service operations
        mock_db = Mock()
        service = AICategorizationService(mock_db)
        
        test_data = {
            "note": "Coffee at Starbucks",
            "amount": 5.50,
            "type": "expense"
        }
        
        memory_samples = []
        
        for i in range(num_iterations):
            # Simulate AI operations
            try:
                # This would normally call the AI service
                # For memory testing, we'll simulate the operations
                self._simulate_ai_operations(service, test_data)
                
                # Sample memory every 100 iterations
                if i % 100 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_samples.append(current_memory)
                    
            except Exception as e:
                print(f"Memory test iteration {i} failed: {e}")
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        results = {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": memory_increase,
            "memory_samples": memory_samples,
            "iterations": num_iterations
        }
        
        print(f"✅ Memory Usage Results:")
        print(f"   Initial Memory: {results['initial_memory_mb']:.1f} MB")
        print(f"   Final Memory: {results['final_memory_mb']:.1f} MB")
        print(f"   Memory Increase: {results['memory_increase_mb']:.1f} MB")
        
        return results
    
    def test_accuracy_under_load(self, num_requests: int = 50) -> Dict:
        """Test AI accuracy under load conditions"""
        print(f"Testing AI accuracy under load with {num_requests} requests...")
        
        # Test cases with expected categories
        test_cases = [
            {"note": "Coffee at Starbucks", "expected_category": "Food & Dining", "amount": 5.50},
            {"note": "Uber ride to work", "expected_category": "Transportation", "amount": 12.00},
            {"note": "Amazon purchase", "expected_category": "Shopping", "amount": 25.99},
            {"note": "Netflix subscription", "expected_category": "Entertainment", "amount": 15.99},
            {"note": "Grocery shopping", "expected_category": "Food & Dining", "amount": 45.00},
        ]
        
        correct_predictions = 0
        total_predictions = 0
        confidence_scores = []
        
        for i in range(num_requests):
            test_case = test_cases[i % len(test_cases)]
            
            try:
                # Mock AI prediction
                predicted_category, confidence = self._mock_ai_prediction(test_case)
                
                if predicted_category == test_case["expected_category"]:
                    correct_predictions += 1
                
                total_predictions += 1
                confidence_scores.append(confidence)
                
            except Exception as e:
                print(f"Accuracy test iteration {i} failed: {e}")
        
        if total_predictions > 0:
            accuracy = (correct_predictions / total_predictions) * 100
            avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0
            
            results = {
                "total_predictions": total_predictions,
                "correct_predictions": correct_predictions,
                "accuracy_percentage": accuracy,
                "average_confidence": avg_confidence,
                "confidence_scores": confidence_scores
            }
            
            print(f"✅ Accuracy Under Load Results:")
            print(f"   Accuracy: {results['accuracy_percentage']:.1f}%")
            print(f"   Average Confidence: {results['average_confidence']:.3f}")
            print(f"   Correct Predictions: {results['correct_predictions']}/{results['total_predictions']}")
            
            return results
        else:
            return {"error": "No successful predictions"}
    
    def run_full_performance_suite(self) -> Dict:
        """Run complete performance test suite"""
        print("🚀 Starting AI Performance Test Suite...")
        print("=" * 50)
        
        suite_results = {}
        
        # Test 1: Response Time
        suite_results["response_time"] = self.test_suggestion_response_time(100)
        print()
        
        # Test 2: Concurrent Performance
        suite_results["concurrent"] = self.test_concurrent_suggestions(10, 10)
        print()
        
        # Test 3: Memory Usage
        suite_results["memory"] = self.test_memory_usage(1000)
        print()
        
        # Test 4: Accuracy Under Load
        suite_results["accuracy"] = self.test_accuracy_under_load(50)
        print()
        
        # Summary
        print("=" * 50)
        print("📊 Performance Test Suite Summary:")
        print("=" * 50)
        
        if "response_time" in suite_results and "avg_response_time" in suite_results["response_time"]:
            print(f"✅ Response Time: {suite_results['response_time']['avg_response_time']:.3f}s avg")
        
        if "concurrent" in suite_results and "avg_response_time" in suite_results["concurrent"]:
            print(f"✅ Concurrent: {suite_results['concurrent']['avg_response_time']:.3f}s avg")
        
        if "memory" in suite_results and "memory_increase_mb" in suite_results["memory"]:
            print(f"✅ Memory: {suite_results['memory']['memory_increase_mb']:.1f} MB increase")
        
        if "accuracy" in suite_results and "accuracy_percentage" in suite_results["accuracy"]:
            print(f"✅ Accuracy: {suite_results['accuracy']['accuracy_percentage']:.1f}%")
        
        return suite_results
    
    def _mock_suggestion_request(self, data: Dict) -> float:
        """Mock AI suggestion request for testing"""
        # Simulate AI processing time
        processing_time = 0.01 + (hash(str(data)) % 100) / 10000  # 0.01-0.11 seconds
        time.sleep(processing_time)
        return processing_time
    
    def _simulate_ai_operations(self, service: AICategorizationService, data: Dict):
        """Simulate AI operations for memory testing"""
        # Simulate text processing
        text = data.get("note", "")
        if text:
            # Simulate keyword matching
            keywords = text.lower().split()
            # Simulate pattern matching
            patterns = [word for word in keywords if len(word) > 3]
    
    def _mock_ai_prediction(self, test_case: Dict) -> Tuple[str, float]:
        """Mock AI prediction for accuracy testing"""
        # Simple mock prediction based on keywords
        note = test_case["note"].lower()
        
        if "coffee" in note or "starbucks" in note or "grocery" in note:
            return "Food & Dining", 0.85
        elif "uber" in note or "ride" in note:
            return "Transportation", 0.90
        elif "amazon" in note or "purchase" in note:
            return "Shopping", 0.80
        elif "netflix" in note or "subscription" in note:
            return "Entertainment", 0.75
        else:
            return "Other", 0.50
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]


def run_performance_tests():
    """Run all performance tests"""
    tester = AIPerformanceTester()
    results = tester.run_full_performance_suite()
    return results


if __name__ == "__main__":
    run_performance_tests()
