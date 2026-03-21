"""Demo script showing caching functionality."""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cache import get_response_cache
from case_manager import CaseManager


def demo_ttl_cache():
    """Demonstrate TTL cache functionality."""
    print("=" * 60)
    print("TTL Cache Demo")
    print("=" * 60)
    
    cache = get_response_cache()
    
    # Set some fallback responses
    print("\n1. Setting fallback responses...")
    cache.set_fallback("prosecution", "opening", "The prosecution rests.")
    cache.set_fallback("defence", "opening", "The defence rests.")
    cache.set_fallback("judge", "summing_up", "The jury will now deliberate.")
    
    # Retrieve fallback responses
    print("\n2. Retrieving fallback responses...")
    prosecution_fallback = cache.get_fallback("prosecution", "opening")
    print(f"   Prosecution fallback: {prosecution_fallback}")
    
    defence_fallback = cache.get_fallback("defence", "opening")
    print(f"   Defence fallback: {defence_fallback}")
    
    # Show cache stats
    print("\n3. Cache statistics:")
    stats = cache.get_all_stats()
    for cache_type, cache_stats in stats.items():
        print(f"   {cache_type}:")
        print(f"      Hits: {cache_stats['hits']}")
        print(f"      Misses: {cache_stats['misses']}")
        print(f"      Size: {cache_stats['size']}")
        print(f"      Hit Rate: {cache_stats['hit_rate']}")


def demo_case_caching():
    """Demonstrate case content caching."""
    print("\n" + "=" * 60)
    print("Case Content Caching Demo")
    print("=" * 60)
    
    manager = CaseManager()
    
    # First load (from file)
    print("\n1. Loading case for the first time (from file)...")
    start = time.time()
    try:
        case1 = manager.load_case("blackthorn-hall-001")
        elapsed1 = (time.time() - start) * 1000
        print(f"   Loaded: {case1.title}")
        print(f"   Time: {elapsed1:.2f}ms")
    except FileNotFoundError:
        print("   Case file not found (expected in test environment)")
        return
    
    # Second load (from cache)
    print("\n2. Loading same case again (from cache)...")
    start = time.time()
    case2 = manager.load_case("blackthorn-hall-001")
    elapsed2 = (time.time() - start) * 1000
    print(f"   Loaded: {case2.title}")
    print(f"   Time: {elapsed2:.2f}ms")
    
    # Show performance improvement
    print(f"\n3. Performance improvement:")
    print(f"   First load: {elapsed1:.2f}ms")
    print(f"   Cached load: {elapsed2:.2f}ms")
    print(f"   Speedup: {elapsed1/elapsed2:.1f}x faster")
    
    # Show cache stats
    cache = get_response_cache()
    stats = cache.case_cache.get_stats()
    print(f"\n4. Case cache statistics:")
    print(f"   Hits: {stats['hits']}")
    print(f"   Misses: {stats['misses']}")
    print(f"   Size: {stats['size']}")
    print(f"   Hit Rate: {stats['hit_rate']}")


def demo_cache_expiration():
    """Demonstrate TTL expiration."""
    print("\n" + "=" * 60)
    print("Cache Expiration Demo")
    print("=" * 60)
    
    cache = get_response_cache()
    
    # Set a response with short TTL
    print("\n1. Setting response with 2-second TTL...")
    cache.agent_cache.set("test_key", "test_value", ttl=2)
    
    # Retrieve immediately
    print("2. Retrieving immediately...")
    value = cache.agent_cache.get("test_key")
    print(f"   Value: {value}")
    
    # Wait for expiration
    print("3. Waiting 2.5 seconds for expiration...")
    time.sleep(2.5)
    
    # Try to retrieve after expiration
    print("4. Retrieving after expiration...")
    value = cache.agent_cache.get("test_key")
    print(f"   Value: {value} (should be None)")


def demo_cache_cleanup():
    """Demonstrate cache cleanup."""
    print("\n" + "=" * 60)
    print("Cache Cleanup Demo")
    print("=" * 60)
    
    cache = get_response_cache()
    
    # Set multiple entries with different TTLs
    print("\n1. Setting multiple entries with different TTLs...")
    cache.agent_cache.set("short_ttl_1", "value1", ttl=1)
    cache.agent_cache.set("short_ttl_2", "value2", ttl=1)
    cache.agent_cache.set("long_ttl", "value3", ttl=60)
    
    print(f"   Cache size: {cache.agent_cache.get_stats()['size']}")
    
    # Wait for some to expire
    print("\n2. Waiting 1.5 seconds...")
    time.sleep(1.5)
    
    # Cleanup expired entries
    print("3. Cleaning up expired entries...")
    cache.agent_cache.cleanup_expired()
    
    stats = cache.agent_cache.get_stats()
    print(f"   Cache size after cleanup: {stats['size']}")
    print(f"   Remaining entry: {cache.agent_cache.get('long_ttl')}")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("VERITAS Caching System Demo")
    print("=" * 60)
    
    # Run demos
    demo_ttl_cache()
    demo_case_caching()
    demo_cache_expiration()
    demo_cache_cleanup()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
