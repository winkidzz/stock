#!/usr/bin/env python3
"""
Test script for local LLM integration
"""

import os
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

print("🧪 Testing Local LLM Integration")
print("=" * 40)

def test_config():
    """Test configuration loading"""
    print("\n1. Testing Configuration...")
    
    try:
        from src.config import settings
        print(f"   ✓ Ollama Base URL: {settings.ollama_base_url}")
        print(f"   ✓ Primary Model: {settings.llm_model}")
        print(f"   ✓ Fast Model: {settings.llm_model_fast}")
        print(f"   ✓ Temperature: {settings.llm_temperature}")
        return True
    except Exception as e:
        print(f"   ✗ Configuration error: {e}")
        return False

def test_ollama_connection():
    """Test Ollama connection"""
    print("\n2. Testing Ollama Connection...")
    
    try:
        import requests
        from src.config import settings
        
        response = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print(f"   ✓ Ollama is running")
            print(f"   ✓ Available models: {len(models.get('models', []))}")
            return True
        else:
            print(f"   ✗ Ollama returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Ollama connection error: {e}")
        print("   💡 Make sure Ollama is running with: ollama serve")
        return False

def test_llm_basic():
    """Test basic LLM functionality"""
    print("\n3. Testing Basic LLM Functionality...")
    
    try:
        from langchain_ollama import OllamaLLM
        from src.config import settings
        
        llm = OllamaLLM(
            model=settings.llm_model_fast,
            base_url=settings.ollama_base_url,
            temperature=0.1
        )
        
        response = llm.invoke("Hello! Please respond with just 'Hello World'")
        print(f"   ✓ LLM Response: {response[:100]}...")
        return True
    except Exception as e:
        print(f"   ✗ LLM test error: {e}")
        return False

async def test_sentiment_analysis():
    """Test sentiment analysis"""
    print("\n4. Testing Sentiment Analysis...")
    
    try:
        from src.services.news_service import NewsService
        
        news_service = NewsService()
        
        # Test positive sentiment
        positive_text = "Apple Inc. reports record quarterly earnings, beating analyst expectations"
        positive_result = await news_service.analyze_sentiment(positive_text)
        print(f"   ✓ Positive sentiment: {positive_result.score:.2f} ({positive_result.label})")
        
        # Test negative sentiment
        negative_text = "Company faces major lawsuit, stock price plummets"
        negative_result = await news_service.analyze_sentiment(negative_text)
        print(f"   ✓ Negative sentiment: {negative_result.score:.2f} ({negative_result.label})")
        
        return True
    except Exception as e:
        print(f"   ✗ Sentiment analysis error: {e}")
        return False

async def test_embeddings():
    """Test embedding generation"""
    print("\n5. Testing Embeddings...")
    
    try:
        from src.services.news_service import NewsService
        
        news_service = NewsService()
        
        text = "Apple Inc. is a technology company"
        embedding = await news_service.get_embedding(text)
        
        if embedding:
            print(f"   ✓ Embedding generated: {len(embedding)} dimensions")
            print(f"   ✓ Sample values: {embedding[:5]}...")
            return True
        else:
            print("   ✗ No embedding generated")
            return False
    except Exception as e:
        print(f"   ✗ Embedding error: {e}")
        return False

async def test_data_collection_agent():
    """Test data collection agent"""
    print("\n6. Testing Data Collection Agent...")
    
    try:
        from src.agents.data_collection_agent import DataCollectionAgent
        
        agent = DataCollectionAgent()
        
        # Test summary generation
        test_state = {
            'symbol': 'TEST',
            'status': 'completed',
            'collected_data': {
                'stock_data': {'historical_data_points': 100},
                'news_data': {'news_items_collected': 5},
                'validation': {'overall_valid': True}
            }
        }
        
        summary = agent._generate_summary(test_state)
        print(f"   ✓ Summary generated: {len(summary)} characters")
        print(f"   ✓ Sample: {summary[:100]}...")
        return True
    except Exception as e:
        print(f"   ✗ Data collection agent error: {e}")
        return False

async def main():
    """Run all tests"""
    print("Starting local LLM integration tests...\n")
    
    tests = [
        ("Configuration", test_config),
        ("Ollama Connection", test_ollama_connection),
        ("Basic LLM", test_llm_basic),
        ("Sentiment Analysis", test_sentiment_analysis),
        ("Embeddings", test_embeddings),
        ("Data Collection Agent", test_data_collection_agent),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ✗ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Test Results Summary:")
    print("=" * 40)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\nPassed: {passed}/{total} tests")
    
    if passed == total:
        print("\n🎉 All tests passed! Local LLM integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration and setup.")
        
        print("\n💡 Troubleshooting:")
        print("   - Make sure Ollama is running: ollama serve")
        print("   - Install required models: ollama pull llama3:8b")
        print("   - Check .env configuration")
        print("   - Install dependencies: pip install -r requirements.txt")

if __name__ == "__main__":
    asyncio.run(main()) 