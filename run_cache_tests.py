"""
Test Runner for Cache Performance Tests

Quick script to run cache tests without pytest command line.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.cache import get_cache


def run_basic_tests():
    """Run basic cache validation tests"""
    print("=" * 60)
    print("CACHE SYSTEM VALIDATION")
    print("=" * 60)

    cache = get_cache()

    results = {'passed': 0, 'failed': 0, 'total': 0}

    def test(name, condition):
        """Helper to run a test"""
        results['total'] += 1
        if condition:
            results['passed'] += 1
            print(f"[PASS] {name}")
            return True
        else:
            results['failed'] += 1
            print(f"[FAIL] {name}")
            return False

    # Test 1: Cache initialization
    test("Cache service initialization", cache is not None)
    test("Cache enabled status", isinstance(cache.enabled, bool))

    # Test 2: Basic operations
    cache.set('test:basic', {'value': 123}, ttl=60)
    result = cache.get('test:basic')
    test("Basic set/get operation", result == {'value': 123} if cache.enabled else result is None)

    # Test 3: Complex data
    complex_data = {
        'forecast': [{'date': '2025-01-01', 'amount': 100}],
        'summary': {'total': 100, 'average': 100},
        'metadata': {'created': '2025-12-26'}
    }
    cache.set('test:complex', complex_data, ttl=60)
    result = cache.get('test:complex')
    test("Complex data serialization", result == complex_data if cache.enabled else result is None)

    # Test 4: Pattern deletion
    cache.set('user:999:forecast', {'data': 'f1'})
    cache.set('user:999:report', {'data': 'r1'})
    cache.set('user:888:forecast', {'data': 'f2'})
    deleted = cache.delete_pattern('user:999:*')
    test("Pattern deletion", deleted == 2 if cache.enabled else deleted == 0)
    test("Pattern deletion accuracy", cache.get('user:999:forecast') is None and cache.get('user:888:forecast') is not None if cache.enabled else True)

    # Test 5: User cache invalidation
    cache.set('forecast:777:total:90', {'test': 'data'})
    cache.set('report:777:monthly:6', {'test': 'data'})
    deleted = cache.invalidate_user_cache(777)
    test("User cache invalidation", deleted >= 2 if cache.enabled else deleted == 0)
    test("Invalidation accuracy", cache.get('forecast:777:total:90') is None if cache.enabled else True)

    # Test 6: Cache statistics
    stats = cache.get_stats()
    test("Cache statistics available", 'enabled' in stats)
    test("Stats show correct status", stats['enabled'] == cache.enabled)

    # Test 7: TTL functionality
    cache.set('test:ttl:short', {'expires': 'soon'}, ttl=1)
    test("TTL set operation", cache.get('test:ttl:short') is not None if cache.enabled else True)

    # Test 8: Delete operation
    cache.set('test:delete', {'value': 'to_delete'})
    cache.delete('test:delete')
    test("Delete operation", cache.get('test:delete') is None)

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {results['total']}")
    print(f"Passed: {results['passed']} ({results['passed']/results['total']*100:.1f}%)")
    print(f"Failed: {results['failed']}")

    if cache.enabled:
        print("\n" + "=" * 60)
        print("CACHE STATISTICS")
        print("=" * 60)
        stats = cache.get_stats()
        print(f"Redis enabled: {stats['enabled']}")
        print(f"Total keys: {stats.get('total_keys', 'N/A')}")
        print(f"Memory used: {stats.get('memory_used', 'N/A')}")
        print(f"Cache hits: {stats.get('hits', 'N/A')}")
        print(f"Cache misses: {stats.get('misses', 'N/A')}")
        print(f"Hit rate: {stats.get('hit_rate', 'N/A')}")
    else:
        print("\n[WARNING] Redis not available - cache is disabled")
        print("Tests passed using graceful degradation mode")

    print("=" * 60)

    return results['failed'] == 0


def run_performance_test():
    """Run quick performance benchmark"""
    import time
    import statistics

    print("\n" + "=" * 60)
    print("PERFORMANCE BENCHMARK")
    print("=" * 60)

    cache = get_cache()

    if not cache.enabled:
        print("[WARNING] Skipping performance test - Redis not available")
        return

    # Warm-up
    for i in range(10):
        cache.set(f'warmup:{i}', {'value': i}, ttl=60)

    # Benchmark SET operations
    test_data = {'forecast': list(range(100))}
    iterations = 50

    set_times = []
    for i in range(iterations):
        start = time.perf_counter()
        cache.set(f'perf:test:{i}', test_data, ttl=60)
        elapsed = (time.perf_counter() - start) * 1000
        set_times.append(elapsed)

    # Benchmark GET operations
    get_times = []
    for i in range(iterations):
        start = time.perf_counter()
        cache.get(f'perf:test:{i}')
        elapsed = (time.perf_counter() - start) * 1000
        get_times.append(elapsed)

    # Results
    print(f"\nSET Operations ({iterations} iterations):")
    print(f"  Average: {statistics.mean(set_times):.3f}ms")
    print(f"  Median: {statistics.median(set_times):.3f}ms")
    print(f"  Min: {min(set_times):.3f}ms")
    print(f"  Max: {max(set_times):.3f}ms")

    print(f"\nGET Operations ({iterations} iterations):")
    print(f"  Average: {statistics.mean(get_times):.3f}ms")
    print(f"  Median: {statistics.median(get_times):.3f}ms")
    print(f"  Min: {min(get_times):.3f}ms")
    print(f"  Max: {max(get_times):.3f}ms")

    # Performance assessment
    avg_get = statistics.mean(get_times)
    avg_set = statistics.mean(set_times)

    print("\nPerformance Assessment:")
    print(f"  GET: {'[EXCELLENT]' if avg_get < 2 else '[GOOD]' if avg_get < 5 else '[SLOW]'} ({avg_get:.3f}ms avg)")
    print(f"  SET: {'[EXCELLENT]' if avg_set < 5 else '[GOOD]' if avg_set < 10 else '[SLOW]'} ({avg_set:.3f}ms avg)")

    # Clean up
    cache.delete_pattern('perf:test:*')
    cache.delete_pattern('warmup:*')

    print("=" * 60)


if __name__ == '__main__':
    print("\n>>> Cache System Test Suite\n")

    # Run validation tests
    validation_passed = run_basic_tests()

    # Run performance test
    run_performance_test()

    # Exit with appropriate code
    if validation_passed:
        print("\n[SUCCESS] All tests passed successfully!\n")
        sys.exit(0)
    else:
        print("\n[FAILURE] Some tests failed. Check output above.\n")
        sys.exit(1)
