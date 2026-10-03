# Recruitment Platform API Reference

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

The API currently uses a shared secret key configured via the `SECRET_KEY` environment variable. Include it in the `Authorization` header:

```
Authorization: Bearer <SECRET_KEY>
```

## Response Format

All endpoints return JSON responses wrapped in a standard envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "metadata": { ... }
}
```

### Error Response

```json
{
  "success": false,
  "error": "Error message",
  "details": [
    {
      "field": "text",
      "message": "Field is required",
      "code": "required"
    }
  ]
}
```

---

## Health Endpoints

### GET /health

Check the health status of the API.

**Response 200:**
```json
{
  "status": "healthy",
  "service": "recruitment-platform"
}
```

### GET /ready

Check if the API is ready to accept traffic.

**Response 200:**
```json
{
  "status": "ready"
}
```

---

## Resume Parser

### POST /resume-parser/parse

Parse a resume into structured data.

**Request Body:**
```json
{
  "text": "John Doe\njohn.doe@email.com\n(555) 123-4567\n\nEducation:\nBachelor of Science in Computer Science\nStanford University, 2018\n\nExperience:\nSenior Software Engineer at Google\nJan 2020 - Present\n\nSkills: Python, Java, AWS, Kubernetes"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "contact": {
      "email": "john.doe@email.com",
      "phone": "(555) 123-4567"
    },
    "education": [
      {
        "degree": "Bachelor of Science in Computer Science",
        "institution": "",
        "year": ""
      }
    ],
    "experience": [
      {
        "title": "",
        "company": "",
        "dates": "Jan 2020 - Present",
        "description": "..."
      }
    ],
    "skills": ["Python", "Java", "AWS", "Kubernetes"]
  }
}
```

### POST /resume-parser/extract-contact

Extract contact information from resume text.

**Request Body:**
```json
{
  "text": "Email: test@example.com\nPhone: (555) 987-6543"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "email": "test@example.com",
    "phone": "(555) 987-6543"
  }
}
```

### POST /resume-parser/extract-skills

Extract skills from resume text.

**Request Body:**
```json
{
  "text": "Experienced in Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": ["python", "javascript", "react", "node", "aws", "docker", "kubernetes"]
}
```

---

## Candidate Matcher

### POST /candidate-matcher/match

Match candidates to a job description with bias-aware ranking.

**Request Body:**
```json
{
  "candidates": [
    {
      "id": "cand-001",
      "name": "Jane Smith",
      "skills": ["Python", "AWS", "Docker"],
      "experience_years": 5,
      "match_score": 0.85
    }
  ],
  "job_requirements": {
    "title": "Senior Software Engineer",
    "required_skills": ["Python", "AWS", "Kubernetes"],
    "min_experience_years": 3
  }
}
```

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": "cand-001",
      "name": "Jane Smith",
      "match_score": 0.85
    }
  ]
}
```

### POST /candidate-matcher/explain

Explain a candidate match decision.

**Request Body:**
```json
{
  "candidate": { "id": "cand-001", "skills": ["Python", "AWS"] },
  "job": { "title": "Senior Software Engineer", "required_skills": ["Python", "AWS", "Kubernetes"] },
  "match_result": { "score": 0.85 }
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "summary": "",
    "strengths": [],
    "gaps": [],
    "recommendations": []
  }
}
```

### POST /candidate-matcher/gap-analysis

Analyze skills gap between candidate and job requirements.

**Request Body:**
```json
{
  "candidate_skills": ["Python", "AWS"],
  "required_skills": ["Python", "AWS", "Kubernetes"]
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "missing_skills": ["Kubernetes"],
    "matching_skills": ["Python", "AWS"],
    "transferable_skills": [],
    "gap_score": 0.333
  }
}
```

---

## Interview Scheduler

### POST /interview-scheduler/optimize-slots

Find optimal interview time slots based on participant availability.

**Request Body:**
```json
{
  "participants": [
    {
      "id": "user-1",
      "name": "Interviewer A",
      "availability": [
        { "start": "2024-01-15T09:00:00Z", "end": "2024-01-15T17:00:00Z" }
      ]
    }
  ],
  "duration_minutes": 60,
  "preferred_days": ["Monday", "Tuesday", "Wednesday"]
}
```

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "start": "2024-01-15T10:00:00Z",
      "end": "2024-01-15T11:00:00Z",
      "score": 0.95
    }
  ]
}
```

### POST /interview-scheduler/detect-conflicts

Detect scheduling conflicts for a proposed interview.

**Request Body:**
```json
{
  "proposed_slot": {
    "start": "2024-01-15T14:00:00Z",
    "end": "2024-01-15T15:00:00Z"
  },
  "existing_events": [
    {
      "title": "Team Standup",
      "start": "2024-01-15T14:30:00Z",
      "end": "2024-01-15T15:00:00Z"
    }
  ]
}
```

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "type": "overlap",
      "event": "Team Standup",
      "severity": "high"
    }
  ]
}
```

### POST /interview-scheduler/send-reminder

Send interview reminders to participants.

**Request Body:**
```json
{
  "interview": {
    "id": "int-001",
    "candidate": "Jane Smith",
    "time": "2024-01-15T14:00:00Z"
  },
  "reminder_type": "email"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "sent": true,
    "channels": ["email"],
    "timestamp": "2024-01-14T14:00:00Z"
  }
}
```

---

## Skills Assessor

### POST /skills-assessor/assess

Assess candidate skills and generate proficiency scores.

**Request Body:**
```json
{
  "skill_assessments": {
    "Python": 0.9,
    "AWS": 0.75,
    "Kubernetes": 0.6
  },
  "target_level": "senior"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "Python": 0.9,
    "AWS": 0.75,
    "Kubernetes": 0.6
  }
}
```

### POST /skills-assessor/learning-path

Recommend a personalized learning path.

**Request Body:**
```json
{
  "skill_gaps": ["Kubernetes", "Terraform"],
  "career_goals": "DevOps Engineer"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "skill": "Kubernetes",
      "resources": [],
      "estimated_weeks": 4
    }
  ]
}
```

### POST /skills-assessor/validate-skills

Validate claimed skills against evidence.

**Request Body:**
```json
{
  "claimed_skills": ["Python", "AWS"],
  "evidence": {
    "assessments": { "Python": 0.9 },
    "work_history": ["Used AWS in production for 3 years"]
  }
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "validated": ["Python"],
    "unverified": ["AWS"],
    "discrepancies": []
  }
}
```

---

## Bias Detector

### POST /bias-detector/analyze-language

Detect biased language in text.

**Request Body:**
```json
{
  "text": "We need a young and energetic candidate who can work long hours"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "phrase": "young",
      "type": "age_bias",
      "suggestion": "early-career or specify experience level"
    },
    {
      "phrase": "work long hours",
      "type": "work_life_bias",
      "suggestion": "flexible schedule or competitive hours"
    }
  ]
}
```

### POST /bias-detector/fairness-score

Compute fairness metrics for hiring decisions.

**Request Body:**
```json
{
  "decisions": [
    { "candidate_id": "c1", "hired": true, "gender": "F" },
    { "candidate_id": "c2", "hired": false, "gender": "M" }
  ],
  "protected_attributes": ["gender", "race"]
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "statistical_parity": 0.85,
    "equal_opportunity": 0.90,
    "calibration": 0.88
  }
}
```

### POST /bias-detector/demographic-analysis

Analyze demographic patterns in hiring data.

**Request Body:**
```json
{
  "hiring_data": { "total_applications": 1000, "hires": 50 },
  "demographics": { "gender": { "M": 600, "F": 400 } }
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "disparities": [],
    "representation": { "gender": { "M": 0.6, "F": 0.4 } },
    "risk_areas": []
  }
}
```

### POST /bias-detector/recommendations

Get bias mitigation recommendations.

**Request Body:**
```json
{
  "bias_analysis": {
    "language_biases": ["gendered_terms"],
    "demographic_disparities": ["gender_gap"]
  }
}
```

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "category": "language",
      "action": "Replace gendered terms with neutral alternatives",
      "priority": "high"
    }
  ]
}
```

---

## Talent Pool

### POST /talent-pool/source

Source candidates from talent pool for a position.

**Request Body:**
```json
{
  "job_requirements": {
    "title": "Senior Software Engineer",
    "required_skills": ["Python", "AWS"]
  },
  "pool_criteria": {
    "min_experience_years": 3,
    "location": "Remote"
  }
}
```

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "candidate_id": "cand-001",
      "name": "Jane Smith",
      "match_score": 0.85
    }
  ]
}
```

### POST /talent-pool/analyze-pool

Analyze talent pool health and composition.

**Request Body:**
```json
{
  "pool_data": { "total_members": 500 },
  "hiring_needs": { "open_positions": 10, "required_skills": ["Python", "AWS"] }
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "total_candidates": 500,
    "skill_coverage": { "Python": 0.8, "AWS": 0.6 },
    "diversity": {},
    "readiness": 0.75
  }
}
```

### POST /talent-pool/recommend

Recommend talent for a position.

**Request Body:**
```json
{
  "job": { "title": "Senior Software Engineer", "required_skills": ["Python", "AWS"] },
  "pool_members": [
    { "id": "c1", "skills": ["Python", "AWS", "Docker"] }
  ]
}
```

**Response 200:**
```json
{
  "success": true,
  "data": [
    { "candidate_id": "c1", "match_score": 0.95 }
  ]
}
```

### POST /talent-pool/track-engagement

Track candidate engagement in the talent pool.

**Request Body:**
```json
{
  "candidate_id": "cand-001",
  "interactions": [
    { "type": "email_open", "timestamp": "2024-01-10T09:00:00Z" },
    { "type": "profile_view", "timestamp": "2024-01-12T14:00:00Z" }
  ]
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "engagement_level": "active",
    "last_contact": "2024-01-12T14:00:00Z",
    "score": 0.75
  }
}
```

---

## Analytics

### POST /analytics/cost-analysis

Analyze recruitment costs and ROI.

**Request Body:**
```json
{
  "hiring_data": { "total_hires": 50, "total_applications": 1000 },
  "cost_data": { "total_spend": 500000, "channel_costs": { "linkedin": 200000 } }
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "cost_per_hire": 10000,
    "total_spend": 500000,
    "roi": 2.5,
    "breakdown": { "linkedin": 200000 }
  }
}
```

### POST /analytics/funnel-analysis

Analyze recruitment funnel conversion rates.

**Request Body:**
```json
{
  "funnel_data": {
    "stages": ["applied", "screened", "interviewed", "offered", "hired"],
    "counts": [1000, 500, 200, 50, 30]
  }
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "stages": ["applied", "screened", "interviewed", "offered", "hired"],
    "conversion_rates": { "applied_to_screened": 0.5, "screened_to_interviewed": 0.4 },
    "bottlenecks": ["screened_to_interviewed"],
    "drop_off_points": ["interviewed_to_offered"]
  }
}
```

### POST /analytics/diversity-metrics

Get diversity metrics across the recruitment pipeline.

**Request Body:**
```json
{
  "pipeline_data": { "stages": ["applied", "hired"], "counts": [1000, 50] },
  "demographics": { "gender": { "M": 600, "F": 400 } }
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "overall_diversity": { "gender": { "M": 0.6, "F": 0.4 } },
    "stage_metrics": {},
    "trends": []
  }
}
```

### POST /analytics/predict

Generate hiring predictions.

**Request Body:**
```json
{
  "historical_data": { "avg_time_to_hire": 30, "avg_quality_score": 0.8 },
  "current_pipeline": { "open_positions": 10, "active_candidates": 50 }
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "time_to_hire_days": 28,
    "quality_forecast": 0.82,
    "success_probability": 0.75
  }
}
```

### POST /analytics/source-effectiveness

Analyze recruitment source effectiveness.

**Request Body:**
```json
{
  "source_data": { "linkedin": 200, "indeed": 150, "referrals": 50 },
  "outcomes": { "linkedin": { "hires": 20 }, "indeed": { "hires": 10 } }
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "sources": { "linkedin": 0.1, "indeed": 0.067, "referrals": 0.2 },
    "top_performers": ["referrals"],
    "recommendations": []
  }
}
```

---

## Onboarding

### POST /onboarding/check-compliance

Verify onboarding compliance requirements.

**Request Body:**
```json
{
  "employee_data": {
    "name": "Jane Smith",
    "start_date": "2024-02-01",
    "role": "Software Engineer"
  },
  "jurisdiction": "US"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "compliant": true,
    "violations": [],
    "pending_items": [],
    "risk_level": "low"
  }
}
```

### POST /onboarding/generate-documents

Generate onboarding documents.

**Request Body:**
```json
{
  "employee": {
    "name": "Jane Smith",
    "role": "Software Engineer",
    "department": "Engineering"
  },
  "template_config": {
    "include_offer_letter": true,
    "include_policy_ack": true
  }
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "documents": [
      { "type": "offer_letter", "status": "generated" },
      { "type": "policy_acknowledgment", "status": "generated" }
    ],
    "generated_count": 2,
    "pending_signatures": ["offer_letter"]
  }
}
```

### POST /onboarding/track-progress

Track onboarding progress for a new hire.

**Request Body:**
```json
{
  "employee_id": "emp-001",
  "onboarding_plan": {
    "tasks": [
      { "id": "t1", "name": "Complete I-9", "completed": true },
      { "id": "t2", "name": "Setup workstation", "completed": false }
    ]
  }
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "completion_percentage": 0.5,
    "completed_tasks": ["Complete I-9"],
    "pending_tasks": ["Setup workstation"],
    "blockers": []
  }
}
```

### POST /onboarding/schedule-tasks

Schedule onboarding tasks and milestones.

**Request Body:**
```json
{
  "employee": { "name": "Jane Smith", "role": "Software Engineer" },
  "start_date": "2024-02-01"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "task": "Complete I-9",
      "due_date": "2024-02-01",
      "dependencies": []
    },
    {
      "task": "Setup workstation",
      "due_date": "2024-02-02",
      "dependencies": ["Complete I-9"]
    }
  ]
}
```

### POST /onboarding/welcome-message

Generate a personalized welcome message.

**Request Body:**
```json
{
  "employee": { "name": "Jane Smith", "role": "Software Engineer" },
  "team_info": { "name": "Platform Team", "manager": "John Doe" }
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "subject": "Welcome to the team, Jane!",
    "body": "Dear Jane, welcome to the Platform Team...",
    "email_html": "<html>...</html>"
  }
}
```

---

## Job Description Optimizer

### POST /job-description/check-ats

Check job description compatibility with ATS systems.

**Request Body:**
```json
{
  "job_description": "We are looking for a Senior Software Engineer with 5+ years of experience in Python and AWS. Responsibilities include designing scalable systems and mentoring junior developers."
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "compatible": true,
    "score": 0.92,
    "issues": [],
    "recommendations": []
  }
}
```

### POST /job-description/remove-bias

Remove biased language from job description.

**Request Body:**
```json
{
  "job_description": "We need a young, energetic salesman who can work long hours and rock the boat"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "original": "We need a young, energetic salesman...",
    "cleaned": "We are seeking an energetic sales professional...",
    "changes": [
      { "from": "young", "to": "early-career" },
      { "from": "salesman", "to": "sales professional" }
    ],
    "bias_score": 0.15
  }
}
```

### POST /job-description/optimize-keywords

Optimize keywords for search visibility.

**Request Body:**
```json
{
  "job_description": "Looking for a software engineer to build web applications",
  "target_role": "Senior Software Engineer"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "optimized": "Seeking a Senior Software Engineer to build scalable web applications...",
    "added_keywords": ["Senior", "scalable", "distributed systems"],
    "removed_keywords": [],
    "score": 0.88
  }
}
```

### POST /job-description/optimize-seo

Optimize job description for search engines.

**Request Body:**
```json
{
  "job_description": "Software Engineer position at a leading tech company",
  "platform": "linkedin"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "title_suggestions": ["Senior Software Engineer - Tech Company"],
    "meta_description": "Join our engineering team...",
    "structured_data": {},
    "score": 0.85
  }
}
```

### POST /job-description/analyze-tone

Analyze the tone of a job description.

**Request Body:**
```json
{
  "job_description": "Join our amazing team! We're looking for a rockstar developer.",
  "brand_voice": "professional"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "tone": "casual",
    "formality": 0.3,
    "enthusiasm": 0.9,
    "inclusivity": 0.7,
    "recommendations": ["Consider more formal language for senior roles"]
  }
}
```

---

## Employer Branding

### POST /employer-branding/brand-strategy

Develop an employer branding strategy.

**Request Body:**
```json
{
  "company_data": {
    "name": "TechCorp",
    "industry": "Technology",
    "size": 500
  },
  "target_audience": {
    "demographics": "Software Engineers",
    "experience_level": "mid-to-senior"
  }
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "positioning": "Innovative technology company...",
    "value_proposition": "Build the future of...",
    "channels": ["linkedin", "glassdoor", "careers_page"],
    "messaging": {}
  }
}
```

### POST /employer-branding/generate-content

Generate employer branding content.

**Request Body:**
```json
{
  "content_type": "social_media_post",
  "brand_guidelines": {
    "tone": "professional",
    "voice": "innovative"
  }
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "content": "Excited to announce...",
    "format": "text",
    "platform": "linkedin",
    "hashtags": ["#hiring", "#techjobs"]
  }
}
```

### POST /employer-branding/manage-reputation

Manage employer reputation across platforms.

**Request Body:**
```json
{
  "platform_data": {
    "glassdoor": { "rating": 4.2, "reviews": 150 },
    "indeed": { "rating": 4.0, "reviews": 200 }
  },
  "reputation_metrics": { "overall": 4.1, "trend": "improving" }
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "overall_score": 4.1,
    "platform_scores": { "glassdoor": 4.2, "indeed": 4.0 },
    "trends": ["improving"],
    "action_items": ["Respond to recent negative reviews"]
  }
}
```

### POST /employer-branding/analyze-reviews

Analyze employee and candidate reviews.

**Request Body:**
```json
{
  "reviews": [
    { "rating": 5, "text": "Great place to work!" },
    { "rating": 2, "text": "Poor management" }
  ],
  "platform": "glassdoor"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "themes": ["management", "culture", "compensation"],
    "sentiment": { "positive": 0.6, "negative": 0.3, "neutral": 0.1 },
    "actionable_insights": ["Address management concerns"],
    "response_suggestions": []
  }
}
```

### POST /employer-branding/analyze-sentiment

Analyze sentiment in employer-related content.

**Request Body:**
```json
{
  "texts": [
    "Great company with amazing culture",
    "Terrible work-life balance",
    "Decent place to grow your career"
  ]
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "overall_sentiment": "mixed",
    "positive_ratio": 0.33,
    "negative_ratio": 0.33,
    "trends": []
  }
}
```

---

## Rate Limiting

The API enforces rate limiting via NGINX ingress:

- **Limit:** 100 requests per minute per client
- **Header:** `X-RateLimit-Remaining` shows remaining requests

## Pagination

List endpoints support pagination via query parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `page` | 1 | Page number (1-indexed) |
| `per_page` | 20 | Items per page (max 100) |

## Versioning

The API uses URL path versioning. The current version is `v1`.

```
/api/v1/resume-parser/parse
```

## SDK Examples

### Python

```python
import httpx

async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1") as client:
    # Parse a resume
    response = await client.post("/resume-parser/parse", json={
        "text": "John Doe\njohn@example.com\nPython, AWS"
    })
    data = response.json()
    print(data["data"]["contact"])

    # Match candidates
    response = await client.post("/candidate-matcher/match", json={
        "candidates": [{"id": "1", "skills": ["Python"]}],
        "job_requirements": {"required_skills": ["Python"]}
    })
    matches = response.json()["data"]
```

### cURL

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Parse resume
curl -X POST http://localhost:8000/api/v1/resume-parser/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "John Doe\nPython, AWS"}'

# Match candidates
curl -X POST http://localhost:8000/api/v1/candidate-matcher/match \
  -H "Content-Type: application/json" \
  -d '{
    "candidates": [{"id": "1", "skills": ["Python"]}],
    "job_requirements": {"required_skills": ["Python"]}
  }'
```

### JavaScript

```javascript
const baseUrl = 'http://localhost:8000/api/v1';

// Parse resume
const response = await fetch(`${baseUrl}/resume-parser/parse`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: 'John Doe\nPython, AWS' })
});
const { data } = await response.json();
console.log(data.contact);
```
