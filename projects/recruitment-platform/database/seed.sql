-- ============================================================================
-- Recruitment Platform Seed Data
-- ============================================================================
-- This file populates the database with sample data for development and testing.
-- Run after schema.sql: psql -d recruitment_platform -f seed.sql
-- ============================================================================

-- Enable extensions (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- SKILLS
-- ============================================================================

INSERT INTO skills (id, name, slug, category, subcategory, description, aliases) VALUES
    (gen_random_uuid(), 'Python', 'python', 'Programming', 'Backend', 'Python programming language', '["python3", "py"]'),
    (gen_random_uuid(), 'JavaScript', 'javascript', 'Programming', 'Frontend', 'JavaScript programming language', '["js", "es6", "es2020"]'),
    (gen_random_uuid(), 'TypeScript', 'typescript', 'Programming', 'Frontend', 'Typed superset of JavaScript', '["ts"]'),
    (gen_random_uuid(), 'React', 'react', 'Framework', 'Frontend', 'React.js library', '["reactjs", "react.js"]'),
    (gen_random_uuid(), 'Node.js', 'nodejs', 'Runtime', 'Backend', 'Node.js runtime', '["node", "node.js"]'),
    (gen_random_uuid(), 'PostgreSQL', 'postgresql', 'Database', 'SQL', 'PostgreSQL database', '["postgres"]'),
    (gen_random_uuid(), 'Docker', 'docker', 'DevOps', 'Containerization', 'Docker container platform', '["docker-compose"]'),
    (gen_random_uuid(), 'Kubernetes', 'kubernetes', 'DevOps', 'Orchestration', 'Kubernetes orchestration', '["k8s"]'),
    (gen_random_uuid(), 'AWS', 'aws', 'Cloud', 'Infrastructure', 'Amazon Web Services', '["amazon-web-services"]'),
    (gen_random_uuid(), 'Machine Learning', 'machine-learning', 'Data Science', 'ML', 'Machine Learning', '["ml", "deep-learning"]'),
    (gen_random_uuid(), 'SQL', 'sql', 'Database', 'Query Language', 'Structured Query Language', '["structured-query-language"]'),
    (gen_random_uuid(), 'GraphQL', 'graphql', 'API', 'Query Language', 'GraphQL API language', '["graph-ql"]'),
    (gen_random_uuid(), 'REST API', 'rest-api', 'API', 'Architecture', 'RESTful API design', '["rest", "restful"]'),
    (gen_random_uuid(), 'Git', 'git', 'Tool', 'Version Control', 'Git version control', '["github", "gitlab"]'),
    (gen_random_uuid(), 'CI/CD', 'cicd', 'DevOps', 'Automation', 'Continuous Integration/Deployment', '["continuous-integration", "continuous-deployment"]'),
    (gen_random_uuid(), 'Agile', 'agile', 'Methodology', 'Project Management', 'Agile methodology', '["scrum", "kanban"]'),
    (gen_random_uuid(), 'System Design', 'system-design', 'Architecture', 'Design', 'System design principles', '["distributed-systems"]'),
    (gen_random_uuid(), 'Data Structures', 'data-structures', 'Computer Science', 'Fundamentals', 'Data structures and algorithms', '["algorithms", "ds"]'),
    (gen_random_uuid(), 'Communication', 'communication', 'Soft Skills', 'Interpersonal', 'Effective communication', '["verbal-communication", "written-communication"]'),
    (gen_random_uuid(), 'Leadership', 'leadership', 'Soft Skills', 'Management', 'Leadership skills', '["team-leadership", "management"]'),
    (gen_random_uuid(), 'Project Management', 'project-management', 'Management', 'Planning', 'Project management', '["pm"]');

-- ============================================================================
-- EMPLOYERS
-- ============================================================================

INSERT INTO employers (id, name, slug, description, website, industry, company_size, founded_year, logo_url, headquarters, social_links, settings, is_active, is_verified) VALUES
    (gen_random_uuid(), 'TechCorp Inc.', 'techcorp', 'Leading technology company building innovative solutions for the future.', 'https://techcorp.example.com', 'Technology', '500-1000', 2010, 'https://cdn.example.com/logos/techcorp.png',
     '{"city": "San Francisco", "state": "CA", "country": "USA", "address": "123 Tech Street"}',
     '{"linkedin": "https://linkedin.com/company/techcorp", "twitter": "@techcorp"}',
     '{"careers_page": true, "auto_respond": true}', TRUE, TRUE),
    (gen_random_uuid(), 'DataFlow Systems', 'dataflow-systems', 'Data analytics and machine learning platform for enterprises.', 'https://dataflow.example.com', 'Data Analytics', '50-200', 2018, 'https://cdn.example.com/logos/dataflow.png',
     '{"city": "New York", "state": "NY", "country": "USA", "address": "456 Data Avenue"}',
     '{"linkedin": "https://linkedin.com/company/dataflow", "twitter": "@dataflow"}',
     '{"careers_page": true, "auto_respond": false}', TRUE, TRUE),
    (gen_random_uuid(), 'CloudNine Solutions', 'cloudnine-solutions', 'Cloud infrastructure and DevOps consulting company.', 'https://cloudnine.example.com', 'Cloud Computing', '200-500', 2015, 'https://cdn.example.com/logos/cloudnine.png',
     '{"city": "Austin", "state": "WA", "country": "USA", "address": "789 Cloud Blvd"}',
     '{"linkedin": "https://linkedin.com/company/cloudnine", "twitter": "@cloudnine"}',
     '{"careers_page": true, "auto_respond": true}', TRUE, TRUE),
    (gen_random_uuid(), 'StartupXYZ', 'startupxyz', 'Early-stage startup revolutionizing the fintech industry.', 'https://startupxyz.example.com', 'Fintech', '10-50', 2022, 'https://cdn.example.com/logos/startupxyz.png',
     '{"city": "Austin", "state": "TX", "country": "USA", "address": "321 Innovation Way"}',
     '{"linkedin": "https://linkedin.com/company/startupxyz", "twitter": "@startupxyz"}',
     '{"careers_page": true, "auto_respond": false}', TRUE, FALSE);

-- ============================================================================
-- RECRUITERS
-- ============================================================================

INSERT INTO recruiters (id, employer_id, email, first_name, last_name, title, department, phone, avatar_url, bio, specialties, is_active, is_admin, last_login_at)
SELECT
    gen_random_uuid(),
    e.id,
    'recruiter@' || e.slug || '.example.com',
    'John',
    'Doe',
    'Senior Technical Recruiter',
    'Talent Acquisition',
    '+1-555-0100',
    'https://cdn.example.com/avatars/john-doe.png',
    'Experienced recruiter specializing in tech talent.',
    '["engineering", "product", "data"]',
    TRUE,
    TRUE,
    NOW() - INTERVAL '2 hours'
FROM employers e WHERE e.slug = 'techcorp';

INSERT INTO recruiters (id, employer_id, email, first_name, last_name, title, department, phone, avatar_url, bio, specialties, is_active, is_admin, last_login_at)
SELECT
    gen_random_uuid(),
    e.id,
    'jane@' || e.slug || '.example.com',
    'Jane',
    'Smith',
    'Recruiting Manager',
    'People Operations',
    '+1-555-0101',
    'https://cdn.example.com/avatars/jane-smith.png',
    'Building world-class teams through strategic hiring.',
    '["engineering", "design", "leadership"]',
    TRUE,
    TRUE,
    NOW() - INTERVAL '1 day'
FROM employers e WHERE e.slug = 'dataflow-systems';

INSERT INTO recruiters (id, employer_id, email, first_name, last_name, title, department, phone, avatar_url, bio, specialties, is_active, is_admin, last_login_at)
SELECT
    gen_random_uuid(),
    e.id,
    'mike@' || e.slug || '.example.com',
    'Mike',
    'Johnson',
    'Technical Recruiter',
    'Talent Acquisition',
    '+1-555-0102',
    'https://cdn.example.com/avatars/mike-johnson.png',
    'Passionate about connecting great talent with great opportunities.',
    '["devops", "cloud", "backend"]',
    TRUE,
    FALSE,
    NOW() - INTERVAL '3 hours'
FROM employers e WHERE e.slug = 'cloudnine-solutions';

-- ============================================================================
-- CANDIDATES
-- ============================================================================

INSERT INTO candidates (id, email, first_name, last_name, phone, date_of_birth, gender, nationality, current_title, current_company, current_location, address, social_profiles, resume_url, resume_text, cover_letter, portfolio_url, linkedin_url, github_url, website_url, preferred_location, preferred_salary, notice_period_days, years_experience, summary, languages, certifications, preferences, source, referral_code, is_active, is_anonymous, email_verified, phone_verified, profile_completeness, last_active_at) VALUES
    (gen_random_uuid(), 'alice.johnson@email.com', 'Alice', 'Johnson', '+1-555-1001', '1992-03-15', 'Female', 'USA', 'Senior Software Engineer', 'TechCorp Inc.', 'San Francisco, CA',
     '{"street": "123 Main St", "city": "San Francisco", "state": "CA", "zip": "94105", "country": "USA"}',
     '{"linkedin": "https://linkedin.com/in/alicejohnson", "github": "https://github.com/alicej"}',
     'https://cdn.example.com/resumes/alice-johnson.pdf',
     'Experienced full-stack developer with 8+ years building scalable web applications. Expert in Python, JavaScript, and cloud technologies.',
     'I am excited to apply for this position...',
     'https://alicejohnson.dev',
     'https://linkedin.com/in/alicejohnson',
     'https://github.com/alicej',
     'https://alicejohnson.dev',
     'San Francisco, CA',
     '{"min": 150000, "max": 200000, "currency": "USD"}',
     30, 8.5,
     'Full-stack developer passionate about building scalable applications and mentoring junior developers.',
     '[{"language": "English", "proficiency": "native"}, {"language": "Spanish", "proficiency": "intermediate"}]',
     '["AWS Certified Solutions Architect", "Certified Kubernetes Administrator"]',
     '{"remote_preference": "hybrid", "notice_period": "2 weeks"}',
     'linkedin', 'REF123', TRUE, FALSE, TRUE, TRUE, 95, NOW() - INTERVAL '1 hour'),

    (gen_random_uuid(), 'bob.smith@email.com', 'Bob', 'Smith', '+1-555-1002', '1990-07-22', 'Male', 'USA', 'DevOps Engineer', 'DataFlow Systems', 'New York, NY',
     '{"street": "456 Oak Ave", "city": "New York", "state": "NY", "zip": "10001", "country": "USA"}',
     '{"linkedin": "https://linkedin.com/in/bobsmith", "github": "https://github.com/bobs"}',
     'https://cdn.example.com/resumes/bob-smith.pdf',
     'DevOps engineer with 6 years of experience in cloud infrastructure, CI/CD, and containerization.',
     'I believe my experience aligns well with your requirements...',
     'https://bobsmith.io',
     'https://linkedin.com/in/bobsmith',
     'https://github.com/bobs',
     'https://bobsmith.io',
     'New York, NY',
     '{"min": 130000, "max": 170000, "currency": "USD"}',
     14, 6.0,
     'DevOps engineer specializing in AWS, Kubernetes, and infrastructure as code.',
     '[{"language": "English", "proficiency": "native"}]',
     '["AWS Certified DevOps Engineer", "HashiCorp Certified: Terraform Associate"]',
     '{"remote_preference": "remote", "notice_period": "1 week"}',
     'indeed', NULL, TRUE, FALSE, TRUE, TRUE, 88, NOW() - INTERVAL '30 minutes'),

    (gen_random_uuid(), 'carol.williams@email.com', 'Carol', 'Williams', '+1-555-1003', '1995-11-08', 'Female', 'Canada', 'Frontend Developer', 'StartupXYZ', 'Austin, TX',
     '{"street": "789 Pine Rd", "city": "Austin", "state": "TX", "zip": "73301", "country": "USA"}',
     '{"linkedin": "https://linkedin.com/in/carolwilliams", "github": "https://github.com/carolw"}',
     'https://cdn.example.com/resumes/carol-williams.pdf',
     'Creative frontend developer with 4 years of experience in React, TypeScript, and modern web technologies.',
     'I am thrilled about the opportunity to join your team...',
     'https://carolwilliams.com',
     'https://linkedin.com/in/carolwilliams',
     'https://github.com/carolw',
     'https://carolwilliams.com',
     'Austin, TX',
     '{"min": 110000, "max": 150000, "currency": "USD"}',
     7, 4.0,
     'Frontend developer focused on creating beautiful, accessible, and performant user interfaces.',
     '[{"language": "English", "proficiency": "native"}, {"language": "French", "proficiency": "advanced"}]',
     '["Google UX Design Certificate"]',
     '{"remote_preference": "remote", "notice_period": "2 weeks"}',
     'company_website', NULL, TRUE, FALSE, TRUE, FALSE, 75, NOW() - INTERVAL '2 hours'),

    (gen_random_uuid(), 'david.brown@email.com', 'David', 'Brown', '+1-555-1004', '1988-01-30', 'Male', 'UK', 'Machine Learning Engineer', 'DataFlow Systems', 'London, UK',
     '{"street": "321 Elm St", "city": "London", "postcode": "SW1A 1AA", "country": "UK"}',
     '{"linkedin": "https://linkedin.com/in/davidbrown", "github": "https://github.com/davidb"}',
     'https://cdn.example.com/resumes/david-brown.pdf',
     'ML engineer with 10+ years of experience in machine learning, deep learning, and data science.',
     'My extensive experience in ML makes me a strong candidate...',
     'https://davidbrown.ai',
     'https://linkedin.com/in/davidbrown',
     'https://github.com/davidb',
     'https://davidbrown.ai',
     'London, UK',
     '{"min": 160000, "max": 220000, "currency": "GBP"}',
     30, 10.0,
     'Machine learning engineer with expertise in NLP, computer vision, and recommendation systems.',
     '[{"language": "English", "proficiency": "native"}, {"language": "German", "proficiency": "intermediate"}]',
     '["TensorFlow Developer Certificate", "AWS Certified Machine Learning"]',
     '{"remote_preference": "hybrid", "notice_period": "1 month"}',
     'linkedin', 'REF456', TRUE, FALSE, TRUE, TRUE, 92, NOW() - INTERVAL '15 minutes'),

    (gen_random_uuid(), 'eva.martinez@email.com', 'Eva', 'Martinez', '+1-555-1005', '1993-09-12', 'Female', 'Spain', 'Product Manager', 'CloudNine Solutions', 'Seattle, WA',
     '{"street": "654 Maple Dr", "city": "Seattle", "state": "WA", "zip": "98101", "country": "USA"}',
     '{"linkedin": "https://linkedin.com/in/evamartinez"}',
     'https://cdn.example.com/resumes/eva-martinez.pdf',
     'Product manager with 7 years of experience in B2B SaaS and cloud products.',
     'I am excited about the opportunity to drive product vision...',
     NULL,
     'https://linkedin.com/in/evamartinez',
     NULL,
     NULL,
     'Seattle, WA',
     '{"min": 140000, "max": 180000, "currency": "USD"}',
     21, 7.0,
     'Product manager with a track record of launching successful B2B SaaS products.',
     '[{"language": "English", "proficiency": "native"}, {"language": "Spanish", "proficiency": "native"}]',
     '["Certified Scrum Product Owner", "PMP"]',
     '{"remote_preference": "hybrid", "notice_period": "3 weeks"}',
     'referral', 'REF789', TRUE, FALSE, TRUE, TRUE, 90, NOW() - INTERVAL '45 minutes');

-- ============================================================================
-- JOBS
-- ============================================================================

INSERT INTO jobs (id, employer_id, posted_by, title, slug, description, responsibilities, requirements, nice_to_have, employment_type, experience_level, department, location_type, location, salary_range, benefits, skills_required, skills_preferred, application_url, application_email, openings, is_remote, is_featured, is_active, is_urgent, views_count, applications_count, published_at, expires_at, closed_at)
SELECT
    gen_random_uuid(),
    e.id,
    r.id,
    'Senior Backend Engineer',
    'senior-backend-engineer-techcorp',
    'We are looking for a Senior Backend Engineer to join our growing team. You will design, build, and maintain scalable backend services that power our platform used by millions of users worldwide.',
    '["Design and implement RESTful APIs", "Optimize database queries and performance", "Mentor junior engineers", "Participate in code reviews", "Collaborate with cross-functional teams"]',
    '["5+ years of backend development experience", "Strong proficiency in Python and PostgreSQL", "Experience with microservices architecture", "Knowledge of Docker and Kubernetes", "Understanding of CI/CD pipelines"]',
    '["Experience with GraphQL", "Familiarity with Redis", "Knowledge of message queues (RabbitMQ, Kafka)"]',
    'full_time', 'senior', 'Engineering', 'hybrid',
    '{"city": "San Francisco", "state": "CA", "country": "USA"}',
    '{"min": 150000, "max": 200000, "currency": "USD"}',
    '["Health insurance", "401(k) matching", "Unlimited PTO", "Remote work options", "Learning budget"]',
    '["Python", "PostgreSQL", "Docker", "Kubernetes"]',
    '["GraphQL", "Redis", "AWS"]',
    'https://techcorp.example.com/careers/senior-backend-engineer',
    'careers@techcorp.example.com',
    2, TRUE, TRUE, TRUE, FALSE, 150, 12,
    NOW() - INTERVAL '5 days', NOW() + INTERVAL '25 days', NULL
FROM employers e, recruiters r WHERE e.slug = 'techcorp' AND r.email LIKE 'recruiter@techcorp%';

INSERT INTO jobs (id, employer_id, posted_by, title, slug, description, responsibilities, requirements, nice_to_have, employment_type, experience_level, department, location_type, location, salary_range, benefits, skills_required, skills_preferred, application_url, application_email, openings, is_remote, is_featured, is_active, is_urgent, views_count, applications_count, published_at, expires_at, closed_at)
SELECT
    gen_random_uuid(),
    e.id,
    r.id,
    'Machine Learning Engineer',
    'ml-engineer-dataflow',
    'Join our ML team to build and deploy machine learning models at scale. You will work on cutting-edge NLP and recommendation systems that serve millions of users.',
    '["Design and implement ML models", "Deploy models to production", "Optimize model performance", "Collaborate with data scientists", "Build data pipelines"]',
    '["3+ years of ML engineering experience", "Strong Python and TensorFlow/PyTorch skills", "Experience with MLOps and model deployment", "Knowledge of SQL and data modeling", "Understanding of distributed computing"]',
    '["Experience with Kubernetes", "Familiarity with Spark", "Published research papers"]',
    'full_time', 'mid', 'Data Science', 'remote',
    '{"city": "New York", "state": "NY", "country": "USA"}',
    '{"min": 140000, "max": 190000, "currency": "USD"}',
    ["Equity package", "Health insurance", "Remote-first culture", "Conference budget", "Flexible hours"]',
    '["Python", "Machine Learning", "SQL", "Docker"]',
    '["Kubernetes", "Spark", "AWS"]',
    'https://dataflow.example.com/careers/ml-engineer',
    'careers@dataflow.example.com',
    1, TRUE, TRUE, TRUE, TRUE, 230, 18,
    NOW() - INTERVAL '3 days', NOW() + INTERVAL '27 days', NULL
FROM employers e, recruiters r WHERE e.slug = 'dataflow-systems' AND r.email LIKE 'jane@dataflow%';

INSERT INTO jobs (id, employer_id, posted_by, title, slug, description, responsibilities, requirements, nice_to_have, employment_type, experience_level, department, location_type, location, salary_range, benefits, skills_required, skills_preferred, application_url, application_email, openings, is_remote, is_featured, is_active, is_urgent, views_count, applications_count, published_at, expires_at, closed_at)
SELECT
    gen_random_uuid(),
    e.id,
    r.id,
    'DevOps Engineer',
    'devops-engineer-cloudnine',
    'We are seeking a DevOps Engineer to help us build and maintain our cloud infrastructure. You will work with AWS, Kubernetes, and various automation tools to ensure our systems are reliable and scalable.',
    '["Manage cloud infrastructure on AWS", "Implement CI/CD pipelines", "Monitor system performance", "Automate deployment processes", "Ensure security best practices"]',
    '["3+ years of DevOps experience", "Strong AWS knowledge", "Experience with Kubernetes and Docker", "Scripting skills (Bash, Python)", "Knowledge of infrastructure as code (Terraform)"]',
    '["Experience with monitoring tools (Prometheus, Grafana)", "Certifications in AWS or Kubernetes"]',
    'full_time', 'mid', 'Infrastructure', 'hybrid',
    '{"city": "Seattle", "state": "WA", "country": "USA"}',
    '{"min": 130000, "max": 170000, "currency": "USD"}',
    '["Stock options", "Health insurance", "Gym membership", "Learning budget", "Flexible schedule"]',
    '["AWS", "Kubernetes", "Docker", "CI/CD"]',
    '["Terraform", "Python", "Monitoring"]',
    'https://cloudnine.example.com/careers/devops-engineer',
    'careers@cloudnine.example.com',
    3, TRUE, FALSE, TRUE, FALSE, 89, 7,
    NOW() - INTERVAL '7 days', NOW() + INTERVAL '23 days', NULL
FROM employers e, recruiters r WHERE e.slug = 'cloudnine-solutions' AND r.email LIKE 'mike@cloudnine%';

INSERT INTO jobs (id, employer_id, posted_by, title, slug, description, responsibilities, requirements, nice_to_have, employment_type, experience_level, department, location_type, location, salary_range, benefits, skills_required, skills_preferred, application_url, application_email, openings, is_remote, is_featured, is_active, is_urgent, views_count, applications_count, published_at, expires_at, closed_at)
SELECT
    gen_random_uuid(),
    e.id,
    r.id,
    'Frontend Developer (React)',
    'frontend-developer-startupxyz',
    'Join our fast-growing team to build beautiful and responsive user interfaces. You will work closely with designers and backend engineers to deliver exceptional user experiences.',
    '["Build responsive web applications with React", "Implement pixel-perfect designs", "Optimize frontend performance", "Write clean, maintainable code", "Participate in code reviews"]',
    '["2+ years of frontend development experience", "Strong React and TypeScript skills", "Experience with modern CSS (Flexbox, Grid)", "Understanding of REST APIs", "Knowledge of testing frameworks (Jest, Cypress)"]',
    '["Experience with Next.js", "Familiarity with GraphQL", "Design system experience"]',
    'full_time', 'junior', 'Engineering', 'remote',
    '{"city": "Austin", "state": "TX", "country": "USA"}',
    '{"min": 100000, "max": 140000, "currency": "USD"}',
    '["Equity package", "Health insurance", "Remote work", "Learning budget", "Flexible hours"]',
    '["React", "TypeScript", "JavaScript", "REST API"]',
    '["Next.js", "GraphQL", "Tailwind CSS"]',
    'https://startupxyz.example.com/careers/frontend-developer',
    'careers@startupxyz.example.com',
    1, TRUE, FALSE, TRUE, FALSE, 67, 5,
    NOW() - INTERVAL '2 days', NOW() + INTERVAL '28 days', NULL
FROM employers e, recruiters r WHERE e.slug = 'startupxyz' AND r.email LIKE 'recruiter@startupxyz%';

-- ============================================================================
-- APPLICATIONS
-- ============================================================================

INSERT INTO applications (id, candidate_id, job_id, recruiter_id, status, status_history, cover_letter, custom_answers, source, referral_code, rating, internal_notes, rejection_reason, rejection_category, offer_details, applied_at, reviewed_at, decided_at)
SELECT
    gen_random_uuid(),
    c.id,
    j.id,
    r.id,
    'interview',
    '[{"status": "submitted", "timestamp": "2026-10-01T10:00:00Z"}, {"status": "screening", "timestamp": "2026-10-02T14:00:00Z"}, {"status": "interview", "timestamp": "2026-10-03T09:00:00Z"}]',
    'I am very excited about this opportunity...',
    '{"question_1": "I have 8 years of experience building scalable systems.", "question_2": "My greatest achievement is leading the migration to microservices."}',
    'linkedin', 'REF123', 4, 'Strong technical background, good culture fit.', NULL, NULL, NULL,
    NOW() - INTERVAL '2 days', NOW() - INTERVAL '1 day', NULL
FROM candidates c, jobs j, recruiters r, employers e
WHERE c.email = 'alice.johnson@email.com' AND j.slug = 'senior-backend-engineer-techcorp' AND e.id = j.employer_id AND r.employer_id = e.id LIMIT 1;

INSERT INTO applications (id, candidate_id, job_id, recruiter_id, status, status_history, cover_letter, custom_answers, source, referral_code, rating, internal_notes, rejection_reason, rejection_category, offer_details, applied_at, reviewed_at, decided_at)
SELECT
    gen_random_uuid(),
    c.id,
    j.id,
    r.id,
    'assessment',
    '[{"status": "submitted", "timestamp": "2026-10-01T11:00:00Z"}, {"status": "screening", "timestamp": "2026-10-02T15:00:00Z"}, {"status": "assessment", "timestamp": "2026-10-03T10:00:00Z"}]',
    'My DevOps experience makes me a great fit...',
    '{"question_1": "I have extensive experience with AWS and Kubernetes.", "question_2": "I automated 90% of deployment processes at my current role."}',
    'indeed', NULL, 5, 'Excellent technical skills, highly recommended.', NULL, NULL, NULL,
    NOW() - INTERVAL '1 day', NOW() - INTERVAL '12 hours', NULL
FROM candidates c, jobs j, recruiters r, employers e
WHERE c.email = 'bob.smith@email.com' AND j.slug = 'devops-engineer-cloudnine' AND e.id = j.employer_id AND r.employer_id = e.id LIMIT 1;

INSERT INTO applications (id, candidate_id, job_id, recruiter_id, status, status_history, cover_letter, custom_answers, source, referral_code, rating, internal_notes, rejection_reason, rejection_category, offer_details, applied_at, reviewed_at, decided_at)
SELECT
    gen_random_uuid(),
    c.id,
    j.id,
    r.id,
    'submitted',
    '[{"status": "submitted", "timestamp": "2026-10-03T08:00:00Z"}]',
    'I am passionate about building great user experiences...',
    '{"question_1": "I have 4 years of React experience.", "question_2": "I led the redesign of our main product."}',
    'company_website', NULL, NULL, NULL, NULL, NULL, NULL,
    NOW() - INTERVAL '6 hours', NULL, NULL
FROM candidates c, jobs j, recruiters r, employers e
WHERE c.email = 'carol.williams@email.com' AND j.slug = 'frontend-developer-startupxyz' AND e.id = j.employer_id AND r.employer_id = e.id LIMIT 1;

INSERT INTO applications (id, candidate_id, job_id, recruiter_id, status, status_history, cover_letter, custom_answers, source, referral_code, rating, internal_notes, rejection_reason, rejection_category, offer_details, applied_at, reviewed_at, decided_at)
SELECT
    gen_random_uuid(),
    c.id,
    j.id,
    r.id,
    'offer',
    '[{"status": "submitted", "timestamp": "2026-09-28T09:00:00Z"}, {"status": "screening", "timestamp": "2026-09-29T10:00:00Z"}, {"status": "interview", "timestamp": "2026-09-30T14:00:00Z"}, {"status": "assessment", "timestamp": "2026-10-01T11:00:00Z"}, {"status": "offer", "timestamp": "2026-10-02T16:00:00Z"}]',
    'I am thrilled about the opportunity to join your ML team...',
    '{"question_1": "I have published 3 papers on NLP.", "question_2": "I built a recommendation system serving 10M users."}',
    'linkedin', 'REF456', 5, 'Exceptional candidate, top 1% of applicants.', NULL, NULL,
    '{"salary": 185000, "equity": "0.1%", "start_date": "2026-11-01", "benefits": ["health", "dental", "vision", "401k"]}',
    NOW() - INTERVAL '5 days', NOW() - INTERVAL '3 days', NOW() - INTERVAL '1 day'
FROM candidates c, jobs j, recruiters r, employers e
WHERE c.email = 'david.brown@email.com' AND j.slug = 'ml-engineer-dataflow' AND e.id = j.employer_id AND r.employer_id = e.id LIMIT 1;

-- ============================================================================
-- INTERVIEWS
-- ============================================================================

INSERT INTO interviews (id, application_id, interviewer_id, interview_type, status, scheduled_at, duration_minutes, timezone, location, meeting_url, meeting_id, feedback, overall_rating, recommendation, notes, candidate_notes, no_show_reason, rescheduled_from, reminder_sent_at)
SELECT
    gen_random_uuid(),
    a.id,
    r.id,
    'technical',
    'scheduled',
    NOW() + INTERVAL '2 days',
    60,
    'America/Los_Angeles',
    'San Francisco Office',
    'https://meet.example.com/tech-interview-123',
    'tech-interview-123',
    '{}',
    NULL,
    NULL,
    'Technical interview focusing on system design and coding.',
    'Please prepare for a system design discussion.',
    NULL,
    NULL,
    NOW() - INTERVAL '1 day'
FROM applications a, recruiters r, candidates c, jobs j
WHERE a.candidate_id = c.id AND a.job_id = j.id AND c.email = 'alice.johnson@email.com' AND j.slug = 'senior-backend-engineer-techcorp' AND r.employer_id = j.employer_id LIMIT 1;

INSERT INTO interviews (id, application_id, interviewer_id, interview_type, status, scheduled_at, duration_minutes, timezone, location, meeting_url, meeting_id, feedback, overall_rating, recommendation, notes, candidate_notes, no_show_reason, rescheduled_from, reminder_sent_at)
SELECT
    gen_random_uuid(),
    a.id,
    r.id,
    'video',
    'completed',
    NOW() - INTERVAL '1 day',
    45,
    'America/New_York',
    NULL,
    'https://meet.example.com/ml-interview-456',
    'ml-interview-456',
    '{"technical_score": 4, "communication_score": 5, "culture_fit": 4, "notes": "Strong ML fundamentals, good problem-solving skills."}',
    4,
    'hire',
    'Candidate demonstrated strong ML knowledge and good communication skills.',
    NULL,
    NULL,
    NULL,
    NOW() - INTERVAL '2 days'
FROM applications a, recruiters r, candidates c, jobs j
WHERE a.candidate_id = c.id AND a.job_id = j.id AND c.email = 'david.brown@email.com' AND j.slug = 'ml-engineer-dataflow' AND r.employer_id = j.employer_id LIMIT 1;

-- ============================================================================
-- ASSESSMENTS
-- ============================================================================

INSERT INTO assessments (id, application_id, assessment_type, status, title, description, instructions, duration_minutes, max_score, passing_score, questions, candidate_answers, score, score_details, evaluator_id, evaluation_notes, started_at, submitted_at, evaluated_at, due_at)
SELECT
    gen_random_uuid(),
    a.id,
    'coding',
    'submitted',
    'Backend Coding Challenge',
    'Complete a series of coding challenges to demonstrate your backend development skills.',
    'You have 90 minutes to complete all challenges. You may use any programming language.',
    90, 100.00, 70.00,
    '[{"id": 1, "title": "API Design", "description": "Design a RESTful API for a job board", "points": 30}, {"id": 2, "title": "Database Schema", "description": "Design a database schema for the API", "points": 30}, {"id": 3, "title": "Implementation", "description": "Implement the API endpoints", "points": 40}]',
    '{"1": "Designed RESTful API with proper HTTP verbs and status codes.", "2": "Created normalized schema with proper indexes.", "3": "Implemented all endpoints with error handling."}',
    85.00,
    '{"1": 25, "2": 28, "3": 32}',
    r.id,
    'Good understanding of API design and database principles.',
    NOW() - INTERVAL '2 days', NOW() - INTERVAL '1 day', NOW() - INTERVAL '12 hours',
    NOW() + INTERVAL '3 days'
FROM applications a, recruiters r, candidates c, jobs j
WHERE a.candidate_id = c.id AND a.job_id = j.id AND c.email = 'alice.johnson@email.com' AND j.slug = 'senior-backend-engineer-techcorp' AND r.employer_id = j.employer_id LIMIT 1;

INSERT INTO assessments (id, application_id, assessment_type, status, title, description, instructions, duration_minutes, max_score, passing_score, questions, candidate_answers, score, score_details, evaluator_id, evaluation_notes, started_at, submitted_at, evaluated_at, due_at)
SELECT
    gen_random_uuid(),
    a.id,
    'technical_quiz',
    'evaluated',
    'DevOps Knowledge Assessment',
    'Test your knowledge of DevOps tools and practices.',
    'Answer all questions to the best of your ability.',
    30, 100.00, 60.00,
    '[{"id": 1, "question": "What is the purpose of Kubernetes?", "options": ["Container orchestration", "Version control", "Database", "Web server"], "correct": 0}, {"id": 2, "question": "What does CI/CD stand for?", "options": ["Continuous Integration/Continuous Deployment", "Code Integration/Code Deployment", "Continuous Improvement/Continuous Development", "None"], "correct": 0}, {"id": 3, "question": "Which AWS service is used for container registry?", "options": ["ECR", "S3", "EC2", "Lambda"], "correct": 0}]',
    '{"1": 0, "2": 0, "3": 0}',
    100.00,
    '{"1": 33.33, "2": 33.33, "3": 33.34}',
    r.id,
    'Perfect score! Excellent understanding of DevOps concepts.',
    NOW() - INTERVAL '3 days', NOW() - INTERVAL '2 days', NOW() - INTERVAL '1 day',
    NOW() - INTERVAL '1 day'
FROM applications a, recruiters r, candidates c, jobs j
WHERE a.candidate_id = c.id AND a.job_id = j.id AND c.email = 'bob.smith@email.com' AND j.slug = 'devops-engineer-cloudnine' AND r.employer_id = j.employer_id LIMIT 1;

-- ============================================================================
-- CANDIDATE SKILLS
-- ============================================================================

INSERT INTO candidate_skills (id, candidate_id, skill_id, proficiency_level, years_experience, is_primary, verified_by, verified_at)
SELECT gen_random_uuid(), c.id, s.id, 5, 8.0, TRUE, NULL, NULL
FROM candidates c, skills s WHERE c.email = 'alice.johnson@email.com' AND s.slug = 'python';

INSERT INTO candidate_skills (id, candidate_id, skill_id, proficiency_level, years_experience, is_primary, verified_by, verified_at)
SELECT gen_random_uuid(), c.id, s.id, 4, 6.0, FALSE, NULL, NULL
FROM candidates c, skills s WHERE c.email = 'alice.johnson@email.com' AND s.slug = 'javascript';

INSERT INTO candidate_skills (id, candidate_id, skill_id, proficiency_level, years_experience, is_primary, verified_by, verified_at)
SELECT gen_random_uuid(), c.id, s.id, 4, 5.0, TRUE, NULL, NULL
FROM candidates c, skills s WHERE c.email = 'alice.johnson@email.com' AND s.slug = 'postgresql';

INSERT INTO candidate_skills (id, candidate_id, skill_id, proficiency_level, years_experience, is_primary, verified_by, verified_at)
SELECT gen_random_uuid(), c.id, s.id, 4, 6.0, TRUE, NULL, NULL
FROM candidates c, skills s WHERE c.email = 'bob.smith@email.com' AND s.slug = 'aws';

INSERT INTO candidate_skills (id, candidate_id, skill_id, proficiency_level, years_experience, is_primary, verified_by, verified_at)
SELECT gen_random_uuid(), c.id, s.id, 5, 4.0, TRUE, NULL, NULL
FROM candidates c, skills s WHERE c.email = 'bob.smith@email.com' AND s.slug = 'kubernetes';

INSERT INTO candidate_skills (id, candidate_id, skill_id, proficiency_level, years_experience, is_primary, verified_by, verified_at)
SELECT gen_random_uuid(), c.id, s.id, 4, 4.0, TRUE, NULL, NULL
FROM candidates c, skills s WHERE c.email = 'carol.williams@email.com' AND s.slug = 'react';

INSERT INTO candidate_skills (id, candidate_id, skill_id, proficiency_level, years_experience, is_primary, verified_by, verified_at)
SELECT gen_random_uuid(), c.id, s.id, 4, 3.0, TRUE, NULL, NULL
FROM candidates c, skills s WHERE c.email = 'carol.williams@email.com' AND s.slug = 'typescript';

INSERT INTO candidate_skills (id, candidate_id, skill_id, proficiency_level, years_experience, is_primary, verified_by, verified_at)
SELECT gen_random_uuid(), c.id, s.id, 5, 10.0, TRUE, NULL, NULL
FROM candidates c, skills s WHERE c.email = 'david.brown@email.com' AND s.slug = 'machine-learning';

INSERT INTO candidate_skills (id, candidate_id, skill_id, proficiency_level, years_experience, is_primary, verified_by, verified_at)
SELECT gen_random_uuid(), c.id, s.id, 5, 8.0, TRUE, NULL, NULL
FROM candidates c, skills s WHERE c.email = 'david.brown@email.com' AND s.slug = 'python';

-- ============================================================================
-- EXPERIENCES
-- ============================================================================

INSERT INTO experiences (id, candidate_id, company_name, company_logo_url, title, employment_type, department, location, is_remote, start_date, end_date, is_current, description, achievements, skills_used)
SELECT gen_random_uuid(), c.id, 'TechCorp Inc.', 'https://cdn.example.com/logos/techcorp.png', 'Senior Software Engineer', 'full_time', 'Engineering', 'San Francisco, CA', FALSE, '2020-03-01', NULL, TRUE,
    'Leading development of core platform services and mentoring junior developers.',
    '["Led migration to microservices architecture", "Improved system performance by 40%", "Mentored 5 junior developers"]',
    '["Python", "PostgreSQL", "Docker", "Kubernetes"]'
FROM candidates c WHERE c.email = 'alice.johnson@email.com';

INSERT INTO experiences (id, candidate_id, company_name, company_logo_url, title, employment_type, department, location, is_remote, start_date, end_date, is_current, description, achievements, skills_used)
SELECT gen_random_uuid(), c.id, 'DataFlow Systems', 'https://cdn.example.com/logos/dataflow.png', 'DevOps Engineer', 'full_time', 'Infrastructure', 'New York, NY', TRUE, '2021-06-01', NULL, TRUE,
    'Managing cloud infrastructure and CI/CD pipelines for data platform.',
    '["Reduced deployment time by 60%", "Implemented infrastructure as code", "Achieved 99.9% uptime"]',
    '["AWS", "Kubernetes", "Docker", "Terraform"]'
FROM candidates c WHERE c.email = 'bob.smith@email.com';

INSERT INTO experiences (id, candidate_id, company_name, company_logo_url, title, employment_type, department, location, is_remote, start_date, end_date, is_current, description, achievements, skills_used)
SELECT gen_random_uuid(), c.id, 'StartupXYZ', 'https://cdn.example.com/logos/startupxyz.png', 'Frontend Developer', 'full_time', 'Engineering', 'Austin, TX', TRUE, '2022-01-01', NULL, TRUE,
    'Building responsive web applications and design system.',
    '["Led redesign of main product", "Improved page load speed by 50%", "Built component library"]',
    '["React", "TypeScript", "JavaScript", "CSS"]'
FROM candidates c WHERE c.email = 'carol.williams@email.com';

INSERT INTO experiences (id, candidate_id, company_name, company_logo_url, title, employment_type, department, location, is_remote, start_date, end_date, is_current, description, achievements, skills_used)
SELECT gen_random_uuid(), c.id, 'DataFlow Systems', 'https://cdn.example.com/logos/dataflow.png', 'Machine Learning Engineer', 'full_time', 'Data Science', 'London, UK', FALSE, '2019-09-01', NULL, TRUE,
    'Developing and deploying ML models for recommendation systems.',
    '["Built recommendation system serving 10M users", "Published 3 research papers", "Improved model accuracy by 25%"]',
    '["Python", "Machine Learning", "TensorFlow", "SQL"]'
FROM candidates c WHERE c.email = 'david.brown@email.com';

-- ============================================================================
-- EDUCATION
-- ============================================================================

INSERT INTO education (id, candidate_id, institution_name, institution_logo_url, degree, field_of_study, education_level, start_date, end_date, is_current, gpa, max_gpa, honors, activities, coursework, description)
SELECT gen_random_uuid(), c.id, 'Stanford University', 'https://cdn.example.com/logos/stanford.png', 'Master of Science', 'Computer Science', 'master', '2014-09-01', '2016-06-01', FALSE, 3.8, 4.0, 'Magna Cum Laude',
    '["Teaching Assistant for CS101", "President of Women in Tech"]',
    '["Machine Learning", "Distributed Systems", "Database Systems", "Algorithms"]',
    'Focused on distributed systems and machine learning.'
FROM candidates c WHERE c.email = 'alice.johnson@email.com';

INSERT INTO education (id, candidate_id, institution_name, institution_logo_url, degree, field_of_study, education_level, start_date, end_date, is_current, gpa, max_gpa, honors, activities, coursework, description)
SELECT gen_random_uuid(), c.id, 'MIT', 'https://cdn.example.com/logos/mit.png', 'Bachelor of Science', 'Computer Science', 'bachelor', '2016-09-01', '2020-06-01', FALSE, 3.9, 4.0, 'Summa Cum Laude',
    ['"HackMIT Organizer", "Robotics Club"]',
    '["Data Structures", "Algorithms", "Operating Systems", "Computer Networks"]',
    'Strong focus on systems programming and algorithms.'
FROM candidates c WHERE c.email = 'bob.smith@email.com';

INSERT INTO education (id, candidate_id, institution_name, institution_logo_url, degree, field_of_study, education_level, start_date, end_date, is_current, gpa, max_gpa, honors, activities, coursework, description)
SELECT gen_random_uuid(), c.id, 'University of Texas at Austin', 'https://cdn.example.com/logos/ut-austin.png', 'Bachelor of Science', 'Computer Science', 'bachelor', '2018-09-01', '2022-05-01', FALSE, 3.7, 4.0, 'Dean''s List',
    '["Web Development Club", "UX Design Society"]',
    '["Web Development", "Human-Computer Interaction", "Database Systems"]',
    'Focus on web technologies and user experience design.'
FROM candidates c WHERE c.email = 'carol.williams@email.com';

INSERT INTO education (id, candidate_id, institution_name, institution_logo_url, degree, field_of_study, education_level, start_date, end_date, is_current, gpa, max_gpa, honors, activities, coursework, description)
SELECT gen_random_uuid(), c.id, 'University of Oxford', 'https://cdn.example.com/logos/oxford.png', 'Doctor of Philosophy', 'Machine Learning', 'doctorate', '2015-10-01', '2019-09-01', FALSE, NULL, NULL, NULL,
    ['"Published 3 papers on NLP", "Best Paper Award at NeurIPS"]',
    '["Deep Learning", "Natural Language Processing", "Computer Vision", "Reinforcement Learning"]',
    'Research focused on transformer architectures and NLP applications.'
FROM candidates c WHERE c.email = 'david.brown@email.com';

-- ============================================================================
-- TALENT POOLS
-- ============================================================================

INSERT INTO talent_pools (id, employer_id, created_by, name, description, pool_type, criteria, member_count, is_active)
SELECT gen_random_uuid(), e.id, r.id, 'Senior Backend Engineers', 'Pool of experienced backend engineers for current and future openings.', 'active',
    '{"skills": ["Python", "PostgreSQL"], "experience_years": 5, "location": "San Francisco"}', 1, TRUE
FROM employers e, recruiters r WHERE e.slug = 'techcorp' AND r.email LIKE 'recruiter@techcorp%' LIMIT 1;

INSERT INTO talent_pools (id, employer_id, created_by, name, description, pool_type, criteria, member_count, is_active)
SELECT gen_random_uuid(), e.id, r.id, 'ML/AI Talent', 'Top machine learning and AI talent for data science roles.', 'passive',
    '{"skills": ["Machine Learning", "Python"], "education": "masters_or_phd"}', 1, TRUE
FROM employers e, recruiters r WHERE e.slug = 'dataflow-systems' AND r.email LIKE 'jane@dataflow%' LIMIT 1;

INSERT INTO talent_pools (id, employer_id, created_by, name, description, pool_type, criteria, member_count, is_active)
SELECT gen_random_uuid(), e.id, r.id, 'DevOps Cloud Experts', 'Experienced DevOps engineers with cloud and Kubernetes expertise.', 'active',
    '{"skills": ["AWS", "Kubernetes", "Docker"], "certifications": ["AWS"]}', 1, TRUE
FROM employers e, recruiters r WHERE e.slug = 'cloudnine-solutions' AND r.email LIKE 'mike@cloudnine%' LIMIT 1;

-- ============================================================================
-- TALENT POOL MEMBERS
-- ============================================================================

INSERT INTO talent_pool_members (id, talent_pool_id, candidate_id, added_by, notes)
SELECT gen_random_uuid(), tp.id, c.id, r.id, 'Strong technical background, recommended by team.'
FROM talent_pools tp, candidates c, recruiters r, employers e
WHERE tp.name = 'Senior Backend Engineers' AND c.email = 'alice.johnson@email.com' AND e.id = tp.employer_id AND r.employer_id = e.id LIMIT 1;

INSERT INTO talent_pool_members (id, talent_pool_id, candidate_id, added_by, notes)
SELECT gen_random_uuid(), tp.id, c.id, r.id, 'Exceptional ML credentials, published researcher.'
FROM talent_pools tp, candidates c, recruiters r, employers e
WHERE tp.name = 'ML/AI Talent' AND c.email = 'david.brown@email.com' AND e.id = tp.employer_id AND r.employer_id = e.id LIMIT 1;

INSERT INTO talent_pool_members (id, talent_pool_id, candidate_id, added_by, notes)
SELECT gen_random_uuid(), tp.id, c.id, r.id, 'Perfect fit for cloud infrastructure role.'
FROM talent_pools tp, candidates c, recruiters r, employers e
WHERE tp.name = 'DevOps Cloud Experts' AND c.email = 'bob.smith@email.com' AND e.id = tp.employer_id AND r.employer_id = e.id LIMIT 1;

-- ============================================================================
-- ANALYTICS EVENTS (sample events for current month)
-- ============================================================================

INSERT INTO analytics_events (id, event_type, event_name, session_id, user_id, candidate_id, employer_id, job_id, application_id, interview_id, assessment_id, recruiter_id, ip_address, user_agent, referrer, url, page_title, metadata, properties, created_at)
SELECT
    gen_random_uuid(),
    'job_view',
    'Job Viewed',
    'sess_' || md5(random()::text),
    NULL,
    c.id,
    e.id,
    j.id,
    NULL, NULL, NULL, NULL,
    '192.168.1.100'::inet,
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'https://google.com',
    'https://example.com/jobs/' || j.slug,
    j.title,
    '{"source": "organic", "device": "desktop"}',
    '{"time_on_page": 45}',
    NOW() - (random() * INTERVAL '30 days')
FROM candidates c, jobs j, employers e
WHERE c.email = 'alice.johnson@email.com' AND j.slug = 'senior-backend-engineer-techcorp' AND e.id = j.employer_id;

INSERT INTO analytics_events (id, event_type, event_name, session_id, user_id, candidate_id, employer_id, job_id, application_id, interview_id, assessment_id, recruiter_id, ip_address, user_agent, referrer, url, page_title, metadata, properties, created_at)
SELECT
    gen_random_uuid(),
    'job_apply_start',
    'Application Started',
    'sess_' || md5(random()::text),
    NULL,
    c.id,
    e.id,
    j.id,
    NULL, NULL, NULL, NULL,
    '192.168.1.101'::inet,
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'https://linkedin.com',
    'https://example.com/jobs/' || j.slug || '/apply',
    'Apply - ' || j.title,
    '{"source": "linkedin", "device": "desktop"}',
    '{"form_started": true}',
    NOW() - (random() * INTERVAL '20 days')
FROM candidates c, jobs j, employers e
WHERE c.email = 'bob.smith@email.com' AND j.slug = 'devops-engineer-cloudnine' AND e.id = j.employer_id;

INSERT INTO analytics_events (id, event_type, event_name, session_id, user_id, candidate_id, employer_id, job_id, application_id, interview_id, assessment_id, recruiter_id, ip_address, user_agent, referrer, url, page_title, metadata, properties, created_at)
SELECT
    gen_random_uuid(),
    'search_query',
    'Job Search',
    'sess_' || md5(random()::text),
    NULL,
    NULL,
    NULL,
    NULL, NULL, NULL, NULL, NULL,
    '10.0.0.50'::inet,
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
    NULL,
    'https://example.com/jobs?q=python&location=remote',
    'Job Search Results',
    '{"query": "python", "location": "remote", "results_count": 42}',
    '{"filters": ["remote", "full_time"]}',
    NOW() - (random() * INTERVAL '15 days');

-- ============================================================================
-- AUDIT LOG (sample entries)
-- ============================================================================

INSERT INTO audit_log (id, table_name, record_id, action, old_values, new_values, changed_fields, performed_by, performed_by_type, ip_address, user_agent, session_id, reason)
SELECT gen_random_uuid(), 'jobs', j.id, 'INSERT', NULL,
    jsonb_build_object('title', j.title, 'status', 'published'),
    NULL, NULL, 'system', '192.168.1.1'::inet, 'Mozilla/5.0', NULL, 'Job published'
FROM jobs j WHERE j.slug = 'senior-backend-engineer-techcorp';

INSERT INTO audit_log (id, table_name, record_id, action, old_values, new_values, changed_fields, performed_by, performed_by_type, ip_address, user_agent, session_id, reason)
SELECT gen_random_uuid(), 'applications', a.id, 'UPDATE',
    jsonb_build_object('status', 'screening'),
    jsonb_build_object('status', 'interview'),
    '["status"]'::jsonb,
    r.id, 'recruiter', '192.168.1.2'::inet, 'Mozilla/5.0', 'sess_abc123', 'Status updated to interview'
FROM applications a, recruiters r, candidates c, jobs j
WHERE a.candidate_id = c.id AND a.job_id = j.id AND c.email = 'alice.johnson@email.com' AND j.slug = 'senior-backend-engineer-techcorp' AND r.employer_id = j.employer_id LIMIT 1;

-- ============================================================================
-- UPDATE SEARCH VECTORS (trigger should handle this, but ensure they're set)
-- ============================================================================

UPDATE employers SET search_vector =
    setweight(to_tsvector('english', COALESCE(name, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(description, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(industry, '')), 'C');

UPDATE recruiters SET search_vector =
    setweight(to_tsvector('english', COALESCE(first_name, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(last_name, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(title, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(department, '')), 'C');

UPDATE candidates SET search_vector =
    setweight(to_tsvector('english', COALESCE(first_name, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(last_name, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(current_title, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(current_company, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(summary, '')), 'C') ||
    setweight(to_tsvector('english', COALESCE(resume_text, '')), 'D');

UPDATE jobs SET search_vector =
    setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(description, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(requirements, '')), 'C') ||
    setweight(to_tsvector('english', COALESCE(responsibilities, '')), 'C');

-- ============================================================================
-- SEED DATA COMPLETE
-- ============================================================================
