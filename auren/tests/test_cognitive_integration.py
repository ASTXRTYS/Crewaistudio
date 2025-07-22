"""
Integration tests for CognitiveTwinService with AUREN.
Tests the complete flow from natural language to database persistence.
"""

import pytest
import asyncio
import os
from datetime import datetime
from src.core.database import db
from src.services.cognitive_twin_service import CognitiveTwinService
from src.core.config import validate_environment

@pytest.fixture(scope="session")
async def setup_database():
    """Set up test database and service."""
    # Skip if no database configured
    try:
        validate_environment()
    except ValueError:
        pytest.skip("Database not configured for testing")
    
    await db.initialize()
    service = CognitiveTwinService(db.pool)
    yield service
    await db.close()

@pytest.mark.asyncio
async def test_track_weight(setup_database):
    """Test weight tracking through service."""
    service = setup_database
    
    # Test weight tracking
    result = await service.track_weight("test_user_123", 218.5, "lbs")
    assert result.success
    assert "218.5 lbs" in result.message
    
    # Test insights
    insights = await service.get_weight_insights("test_user_123")
    assert insights.success
    assert "weight" in insights.message.lower()

@pytest.mark.asyncio
async def test_track_energy(setup_database):
    """Test energy tracking."""
    service = setup_database
    
    result = await service.track_energy("test_user_123", 8, "morning")
    assert result["success"]
    assert "8/10" in result["message"]

@pytest.mark.asyncio
async def test_track_sleep(setup_database):
    """Test sleep tracking."""
    service = setup_database
    
    result = await service.track_sleep("test_user_123", 7.5, 8)
    assert result["success"]
    assert "7.5 hours" in result["message"]

@pytest.mark.asyncio
async def test_track_milestone(setup_database):
    """Test milestone tracking."""
    service = setup_database
    
    result = await service.track_milestone(
        "test_user_123",
        "weight_loss",
        "First 5 lbs Lost",
        "Lost 5 lbs in 2 weeks through consistent morning workouts",
        {"weight_change": -5, "weeks": 2}
    )
    assert result["success"]
    assert "First 5 lbs Lost" in result["message"]

@pytest.mark.asyncio
async def test_extract_weight_from_text():
    """Test natural language weight extraction."""
    service = CognitiveTwinService(None)  # No DB needed for extraction
    
    # Test various patterns
    test_cases = [
        ("I weighed 218.5 lbs this morning", {"weight": 218.5, "unit": "lbs"}),
        ("Down to 215 pounds", {"weight": 215.0, "unit": "lbs"}),
        ("At 98 kg now", {"weight": 98.0, "unit": "kg"}),
        ("I weigh 220", {"weight": 220.0, "unit": "lbs"}),
    ]
    
    for text, expected in test_cases:
        result = service.extract_weight_from_text(text)
        assert result == expected

@pytest.mark.asyncio
async def test_extract_energy_from_text():
    """Test natural language energy extraction."""
    service = CognitiveTwinService(None)
    
    test_cases = [
        ("Energy is 8 out of 10", 8),
        ("Feeling a solid 7/10", 7),
        ("Energy level at 9", 9),
        ("Feeling great today", 8),
        ("Pretty tired", 3),
    ]
    
    for text, expected in test_cases:
        result = service.extract_energy_from_text(text)
        assert result == expected

@pytest.mark.asyncio
async def test_extract_sleep_from_text():
    """Test natural language sleep extraction."""
    service = CognitiveTwinService(None)
    
    test_cases = [
        ("Got 7.5 hours of sleep", {"hours": 7.5, "quality": 5}),
        ("Slept for 8 hours", {"hours": 8.0, "quality": 5}),
        ("8 hours sleep last night", {"hours": 8.0, "quality": 5}),
    ]
    
    for text, expected in test_cases:
        result = service.extract_sleep_from_text(text)
        assert result == expected

@pytest.mark.asyncio
async def test_error_handling(setup_database):
    """Test graceful error handling."""
    service = setup_database
    
    # Test with invalid database (simulate failure)
    bad_service = CognitiveTwinService(None)
    result = await bad_service.track_weight("test_user_123", 200, "lbs")
    assert not result.success
    assert "trouble remembering" in result.message

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
