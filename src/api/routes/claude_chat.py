"""
Claude AI API routes
"""

from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/status")
async def claude_status():
    """Get Claude service status"""
    return {
        "status": "ready",
        "daily_queries_used": 0,
        "daily_limit": 10
    }

@router.get("/conversations")
async def get_conversations():
    """Get active conversation threads"""
    return {
        "conversations": [],
        "total_count": 0
    }

@router.post("/test-json")
async def test_claude_json():
    """Test Claude's JSON response parsing"""
    try:
        # Initialize Claude service
        from src.services.claude_service import ClaudeService
        claude_service = ClaudeService()
        
        result = await claude_service.test_json_response()
        
        if result["success"]:
            return {
                "status": "success",
                "message": "✅ Claude JSON integration working correctly!",
                "test_result": result,
                "recommendation": "Claude will return structured data for reliable processing"
            }
        else:
            return {
                "status": "error", 
                "message": "❌ Claude JSON integration has issues",
                "test_result": result,
                "recommendation": "Check Claude API configuration and model settings"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}") 