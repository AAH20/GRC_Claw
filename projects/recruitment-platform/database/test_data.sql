-- Insert test employers
INSERT INTO employers (id, name, slug, industry, company_size, founded_year, is_active, is_verified)
VALUES
    ('11111111-1111-1111-1111-111111111111', 'TechCorp', 'techcorp', 'Technology', '501-1000', 2010, true, true),
    ('22222222-2222-2222-2222-222222222222', 'DataSoft', 'datasoft', 'Technology', '201-500', 2015, true, true),
    ('33333333-3333-3333-3333-333333333333', 'HealthPlus', 'healthplus', 'Healthcare', '1001-5000', 2005, true, false),
    ('44444444-4444-4444-4444-444444444444', 'FinanceHub', 'financehub', 'Finance', '51-200', 2018, true, true),
    ('55555555-5555-5555-5555-555555555555', 'EduLearn', 'edulearn', 'Education', '11-50', 2020, true, false);

-- Insert test recruiters
INSERT INTO recruiters (id, employer_id, email, first_name, last_name, title, department, is_active, is_admin)
VALUES
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '11111111-1111-1111-1111-111111111111', 'john@techcorp.com', 'John', 'Smith', 'Senior Recruiter', 'Engineering', true, true),
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '11111111-1111-1111-1111-111111111111', 'jane@techcorp.com', 'Jane', 'Doe', 'Recruiter', 'Engineering', true, false),
    ('cccccccc-cccc-cccc-cccc-cccccccccccc', '22222222-2222-2222-2222-222222222222', 'bob@datasoft.com', 'Bob', 'Johnson', 'Talent Acquisition', 'People', true, true),
    ('dddddddd-dddd-dddd-dddd-dddddddddddd', '33333333-3333-3333-3333-333333333333', 'alice@healthplus.com', 'Alice', 'Williams', 'Recruiter', 'Medical', true, false),
    ('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', '44444444-4444-4444-4444-444444444444', 'charlie@financehub.com', 'Charlie', 'Brown', 'Hiring Manager', 'Finance', true, true);

-- Insert test candidates
INSERT INTO candidates (id, email, first_name, last_name, phone, date_of_birth, gender, nationality, current_title, current_company, current_location, years_experience, source, is_active, email_verified, profile_completeness)
VALUES
    ('11111111-1111-1111-1111-111111111112', 'candidate1@test.com', 'Alice', 'Johnson', '555-0101', '1990-05-15', 'Female', 'US', 'Software Engineer', 'TechCorp', 'San Francisco', 5.5, 'referral', true, true, 85),
    ('22222222-2222-2222-2222-222222222223', 'candidate2@test.com', 'Bob', 'Smith', '555-0102', '1988-03-20', 'Male', 'US', 'Data Scientist', 'DataSoft', 'New York', 7.0, 'linkedin', true, true, 90),
    ('33333333-3333-3333-3333-333333333334', 'candidate3@test.com', 'Carol', 'Williams', '555-0103', '1992-11-10', 'Female', 'UK', 'Product Manager', 'HealthPlus', 'London', 4.0, 'indeed', true, true, 75),
    ('44444444-4444-4444-4444-444444444445', 'candidate4@test.com', 'David', 'Brown', '555-0104', '1985-07-25', 'Male', 'US', 'DevOps Engineer', 'FinanceHub', 'Chicago', 9.5, 'referral', true, true, 95),
    ('55555555-5555-5555-5555-555555555556', 'candidate5@test.com', 'Eve', 'Davis', '555-0105', '1995-01-30', 'Female', 'CA', 'UX Designer', 'EduLearn', 'Toronto', 3.0, 'glassdoor', true, false, 60);

-- Insert test jobs
INSERT INTO jobs (id, employer_id, posted_by, title, slug, description, employment_type, experience_level, department, location_type, location, salary_range, openings, is_remote, is_featured, is_active, is_urgent, views_count, applications_count, published_at, expires_at)
VALUES
    ('11111111-1111-1111-1111-111111111113', '11111111-1111-1111-1111-111111111111', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Senior Software Engineer', 'senior-software-engineer-techcorp', 'Build scalable systems', 'full_time', 'senior', 'Engineering', 'onsite', '{"city": "San Francisco", "state": "CA"}', '{"min": 150000, "max": 200000}', 2, false, true, true, false, 150, 12, '2026-09-01', '2026-12-01'),
    ('22222222-2222-2222-2222-222222222224', '11111111-1111-1111-1111-111111111111', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Frontend Developer', 'frontend-developer-techcorp', 'Build user interfaces', 'full_time', 'mid', 'Engineering', 'remote', '{"city": "Remote"}', '{"min": 120000, "max": 160000}', 3, true, false, true, false, 200, 25, '2026-09-15', '2026-11-15'),
    ('33333333-3333-3333-3333-333333333335', '22222222-2222-2222-2222-222222222222', 'cccccccc-cccc-cccc-cccc-cccccccccccc', 'Data Scientist', 'data-scientist-datasoft', 'Analyze data', 'full_time', 'senior', 'Data Science', 'hybrid', '{"city": "New York", "state": "NY"}', '{"min": 140000, "max": 180000}', 1, false, true, true, true, 300, 8, '2026-08-20', '2026-10-20'),
    ('44444444-4444-4444-4444-444444444446', '33333333-3333-3333-3333-333333333333', 'dddddddd-dddd-dddd-dddd-dddddddddddd', 'Registered Nurse', 'registered-nurse-healthplus', 'Provide patient care', 'full_time', 'mid', 'Medical', 'onsite', '{"city": "Boston", "state": "MA"}', '{"min": 70000, "max": 95000}', 5, false, false, true, false, 80, 15, '2026-09-10', '2026-11-10'),
    ('55555555-5555-5555-5555-555555555557', '44444444-4444-4444-4444-444444444444', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'Financial Analyst', 'financial-analyst-financehub', 'Analyze financial data', 'full_time', 'junior', 'Finance', 'onsite', '{"city": "Chicago", "state": "IL"}', '{"min": 60000, "max": 85000}', 2, false, false, true, false, 45, 6, '2026-09-20', '2026-10-20');

-- Insert test applications
INSERT INTO applications (id, candidate_id, job_id, recruiter_id, status, rating, source, applied_at, reviewed_at)
VALUES
    ('11111111-1111-1111-1111-111111111114', '11111111-1111-1111-1111-111111111112', '11111111-1111-1111-1111-111111111113', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'interview', 4, 'referral', '2026-09-05', '2026-09-08'),
    ('22222222-2222-2222-2222-222222222225', '22222222-2222-2222-2222-222222222223', '33333333-3333-3333-3333-333333333335', 'cccccccc-cccc-cccc-cccc-cccccccccccc', 'offer', 5, 'linkedin', '2026-08-25', '2026-09-01'),
    ('33333333-3333-3333-3333-333333333336', '33333333-3333-3333-3333-333333333334', '44444444-4444-4444-4444-444444444446', 'dddddddd-dddd-dddd-dddd-dddddddddddd', 'screening', NULL, 'indeed', '2026-09-12', '2026-09-15'),
    ('44444444-4444-4444-4444-444444444447', '44444444-4444-4444-4444-444444444445', '11111111-1111-1111-1111-111111111113', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'hired', 5, 'referral', '2026-08-15', '2026-08-20'),
    ('55555555-5555-5555-5555-555555555558', '55555555-5555-5555-5555-555555555556', '22222222-2222-2222-2222-222222222224', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'submitted', NULL, 'glassdoor', '2026-09-18', NULL);

-- Insert test interviews
INSERT INTO interviews (id, application_id, interviewer_id, interview_type, status, scheduled_at, duration_minutes, overall_rating, recommendation)
VALUES
    ('11111111-1111-1111-1111-111111111115', '11111111-1111-1111-1111-111111111114', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'technical', 'completed', '2026-09-10 10:00:00+00', 60, 4, 'strong_hire'),
    ('22222222-2222-2222-2222-222222222226', '22222222-2222-2222-2222-222222222225', 'cccccccc-cccc-cccc-cccc-cccccccccccc', 'behavioral', 'completed', '2026-09-05 14:00:00+00', 45, 5, 'hire'),
    ('33333333-3333-3333-3333-333333333337', '33333333-3333-3333-3333-333333333336', 'dddddddd-dddd-dddd-dddd-dddddddddddd', 'phone_screen', 'scheduled', '2026-10-05 09:00:00+00', 30, NULL, NULL),
    ('44444444-4444-4444-4444-444444444448', '44444444-4444-4444-4444-444444444447', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'panel', 'completed', '2026-08-25 11:00:00+00', 90, 5, 'strong_hire'),
    ('55555555-5555-5555-5555-555555555559', '55555555-5555-5555-5555-555555555558', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'video', 'confirmed', '2026-10-08 15:00:00+00', 60, NULL, NULL);

-- Insert test assessments
INSERT INTO assessments (id, application_id, assessment_type, status, title, duration_minutes, max_score, passing_score, score, due_at)
VALUES
    ('11111111-1111-1111-1111-111111111116', '11111111-1111-1111-1111-111111111114', 'coding', 'evaluated', 'Coding Challenge', 120, 100.00, 70.00, 85.00, '2026-09-12 23:59:59+00'),
    ('22222222-2222-2222-2222-222222222227', '22222222-2222-2222-2222-222222222225', 'technical_quiz', 'submitted', 'Technical Quiz', 60, 50.00, 35.00, NULL, '2026-09-08 23:59:59+00'),
    ('33333333-3333-3333-3333-333333333338', '44444444-4444-4444-4444-444444444447', 'take_home', 'evaluated', 'Take Home Project', 480, 100.00, 80.00, 92.00, '2026-08-22 23:59:59+00');

-- Insert test skills
INSERT INTO skills (id, name, slug, category, is_active)
VALUES
    ('11111111-1111-1111-1111-111111111117', 'Python', 'python', 'programming', true),
    ('22222222-2222-2222-2222-222222222228', 'JavaScript', 'javascript', 'programming', true),
    ('33333333-3333-3333-3333-333333333339', 'React', 'react', 'framework', true),
    ('44444444-4444-4444-4444-444444444449', 'PostgreSQL', 'postgresql', 'database', true),
    ('55555555-5555-5555-5555-555555555560', 'AWS', 'aws', 'cloud', true);

-- Insert test experiences
INSERT INTO experiences (id, candidate_id, company_name, title, employment_type, start_date, end_date, is_current, location)
VALUES
    ('11111111-1111-1111-1111-111111111118', '11111111-1111-1111-1111-111111111112', 'TechCorp', 'Software Engineer', 'full_time', '2021-01-15', NULL, true, 'San Francisco'),
    ('22222222-2222-2222-2222-222222222229', '22222222-2222-2222-2222-222222222223', 'DataSoft', 'Data Scientist', 'full_time', '2019-06-01', NULL, true, 'New York'),
    ('33333333-3333-3333-3333-333333333340', '33333333-3333-3333-3333-333333333334', 'HealthPlus', 'Product Manager', 'full_time', '2022-03-01', NULL, true, 'London');

-- Insert test education
INSERT INTO education (id, candidate_id, institution_name, degree, field_of_study, education_level, start_date, end_date, gpa, max_gpa)
VALUES
    ('11111111-1111-1111-1111-111111111119', '11111111-1111-1111-1111-111111111112', 'MIT', 'Master of Science', 'Computer Science', 'master', '2015-09-01', '2017-06-30', 3.80, 4.00),
    ('22222222-2222-2222-2222-222222222230', '22222222-2222-2222-2222-222222222223', 'Stanford', 'Bachelor of Science', 'Statistics', 'bachelor', '2014-09-01', '2018-06-30', 3.60, 4.00),
    ('33333333-3333-3333-3333-333333333341', '33333333-3333-3333-3333-333333333334', 'Oxford', 'Bachelor of Arts', 'Economics', 'bachelor', '2016-09-01', '2020-06-30', 3.50, 4.00);

-- Insert test talent pools
INSERT INTO talent_pools (id, employer_id, created_by, name, pool_type, member_count, is_active)
VALUES
    ('11111111-1111-1111-1111-111111111120', '11111111-1111-1111-1111-111111111111', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Senior Engineers', 'active', 2, true),
    ('22222222-2222-2222-2222-222222222231', '22222222-2222-2222-2222-222222222222', 'cccccccc-cccc-cccc-cccc-cccccccccccc', 'Data Science Talent', 'passive', 1, true);

-- Insert test talent pool members
INSERT INTO talent_pool_members (id, talent_pool_id, candidate_id, added_by)
VALUES
    ('11111111-1111-1111-1111-111111111121', '11111111-1111-1111-1111-111111111120', '11111111-1111-1111-1111-111111111112', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'),
    ('22222222-2222-2222-2222-222222222232', '11111111-1111-1111-1111-111111111120', '44444444-4444-4444-4444-444444444445', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'),
    ('33333333-3333-3333-3333-333333333342', '22222222-2222-2222-2222-222222222231', '22222222-2222-2222-2222-222222222223', 'cccccccc-cccc-cccc-cccc-cccccccccccc');

-- Insert test candidate skills
INSERT INTO candidate_skills (id, candidate_id, skill_id, proficiency_level, years_experience, is_primary)
VALUES
    ('11111111-1111-1111-1111-111111111122', '11111111-1111-1111-1111-111111111112', '11111111-1111-1111-1111-111111111117', 5, 5.0, true),
    ('22222222-2222-2222-2222-222222222233', '11111111-1111-1111-1111-111111111112', '22222222-2222-2222-2222-222222222228', 4, 4.0, false),
    ('33333333-3333-3333-3333-333333333343', '22222222-2222-2222-2222-222222222223', '44444444-4444-4444-4444-444444444449', 5, 6.0, true);

-- Insert test analytics events
INSERT INTO analytics_events (id, event_type, event_name, session_id, user_id, candidate_id, employer_id, job_id, created_at)
VALUES
    ('11111111-1111-1111-1111-111111111123', 'page_view', 'home_page', 'sess-001', NULL, NULL, NULL, NULL, '2026-09-01 10:00:00+00'),
    ('22222222-2222-2222-2222-222222222234', 'job_view', 'job_detail', 'sess-002', NULL, '11111111-1111-1111-1111-111111111112', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111113', '2026-09-02 11:00:00+00'),
    ('33333333-3333-3333-3333-333333333344', 'job_apply_start', 'apply_started', 'sess-003', NULL, '11111111-1111-1111-1111-111111111112', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111113', '2026-09-03 09:00:00+00'),
    ('44444444-4444-4444-4444-444444444450', 'job_apply_complete', 'apply_completed', 'sess-003', NULL, '11111111-1111-1111-1111-111111111112', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111113', '2026-09-03 09:30:00+00'),
    ('55555555-5555-5555-5555-555555555561', 'search_query', 'job_search', 'sess-004', NULL, NULL, NULL, NULL, '2026-09-04 14:00:00+00');

-- Refresh materialized views
SELECT refresh_all_materialized_views();

-- Verify data loaded
SELECT 'employers' AS table_name, COUNT(*) AS row_count FROM employers
UNION ALL SELECT 'recruiters', COUNT(*) FROM recruiters
UNION ALL SELECT 'candidates', COUNT(*) FROM candidates
UNION ALL SELECT 'jobs', COUNT(*) FROM jobs
UNION ALL SELECT 'applications', COUNT(*) FROM applications
UNION ALL SELECT 'interviews', COUNT(*) FROM interviews
UNION ALL SELECT 'assessments', COUNT(*) FROM assessments
UNION ALL SELECT 'skills', COUNT(*) FROM skills
UNION ALL SELECT 'experiences', COUNT(*) FROM experiences
UNION ALL SELECT 'education', COUNT(*) FROM education
UNION ALL SELECT 'talent_pools', COUNT(*) FROM talent_pools
UNION ALL SELECT 'talent_pool_members', COUNT(*) FROM talent_pool_members
UNION ALL SELECT 'candidate_skills', COUNT(*) FROM candidate_skills
UNION ALL SELECT 'analytics_events', COUNT(*) FROM analytics_events
UNION ALL SELECT 'audit_log', COUNT(*) FROM audit_log;
