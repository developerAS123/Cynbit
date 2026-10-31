import pytest

@pytest.mark.asyncio
async def test_submit_career_application(client):
    """Verifies that complete job candidate blueprints are securely stored."""
    payload = {
        "jobId": "backend-developer",
        "fullName": "Kavya Patel",
        "email": "kavya.patel@test.com",
        "phone": "+919876543210",
        "whatsapp": "+919876543210",
        "dob": "2002-04-15",
        "gender": "Female",
        "education": "B.Tech in Computer Science",
        "university": "National Institute of Technology",
        "graduationYear": "2025",
        "noticePeriod": "Immediate",
        "skills": "Python, FastAPI, PostgreSQL, Docker, Redis",
        "currentCity": "Bangalore",
        "permanentAddress": "123 Tech Park Road, Whitefield, Bangalore",
        "portfolioUrl": "https://drive.google.com/sample_resume",
        "linkedinUrl": "https://linkedin.com/in/kavyapatel",
        "professionalProfileUrl": "https://github.com/kavyapatel",
        "message": "Passionate about building scalable distributed backends.",
        "agreedToTerms": True
    }
    response = await client.post("/api/v1/applications", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["application_id"] is not None

@pytest.mark.asyncio
async def test_duplicate_application_zero_enumeration(client):
    """
    Verifies that submitting a duplicate application returns an identical generic
    confirmation, rather than exposing applicant tracking URLs or duplicate warnings.
    """
    payload = {
        "jobId": "backend-developer",
        "fullName": "Aarav Gupta",
        "email": "aarav.gupta@test.com",
        "phone": "+919876500000",
        "whatsapp": "+919876500000",
        "dob": "2001-08-20",
        "gender": "Male",
        "education": "B.E. in Information Technology",
        "university": "XYZ University",
        "graduationYear": "2024",
        "noticePeriod": "30 days",
        "skills": "Go, FastAPI, Kubernetes",
        "currentCity": "Pune",
        "permanentAddress": "Flat 402, Shivajinagar, Pune",
        "portfolioUrl": "https://aaravgupta.dev",
        "linkedinUrl": "https://linkedin.com/in/aaravgupta",
        "message": "Interested in joining Cynbit core backend engineering.",
        "agreedToTerms": True
    }
    
    # First submission
    resp1 = await client.post("/api/v1/applications", json=payload)
    assert resp1.status_code == 201
    
    # Duplicate submission
    resp2 = await client.post("/api/v1/applications", json=payload)
    assert resp2.status_code == 201
    
    # Assert message parity (prevents duplicate applicant reconnaissance)
    assert resp1.json()["message"] == resp2.json()["message"]

