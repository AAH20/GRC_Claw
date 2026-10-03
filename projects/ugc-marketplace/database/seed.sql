-- =============================================================================
-- UGC Marketplace Seed Data
-- =============================================================================

-- =============================================================================
-- CREATORS
-- =============================================================================
INSERT INTO creators (id, username, email, display_name, bio, avatar_url, website_url, social_links, verification_status, reputation_score, total_earnings, total_sales, is_active)
VALUES
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'artista', 'artista@example.com', 'Maria Artistica', 'Digital artist specializing in 3D assets and illustrations.', 'https://cdn.example.com/avatars/artista.jpg', 'https://mariaart.example.com', '{"twitter": "@artista", "instagram": "@maria.artista"}', 'verified', 92.50, 15420.00, 87, true),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'pixelmaster', 'pixelmaster@example.com', 'John Pixel', 'Game asset creator with 10 years of experience.', 'https://cdn.example.com/avatars/pixelmaster.jpg', 'https://pixelmaster.dev', '{"twitter": "@pixelmaster", "github": "pixelmaster"}', 'verified', 88.75, 28900.50, 156, true),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'soundwave', 'soundwave@example.com', 'Alex Sound', 'Audio engineer and sound designer for games and film.', 'https://cdn.example.com/avatars/soundwave.jpg', NULL, '{"twitter": "@soundwave_audio"}', 'verified', 85.00, 12300.00, 64, true),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'motionguru', 'motionguru@example.com', 'Sarah Motion', 'Motion graphics and animation specialist.', 'https://cdn.example.com/avatars/motionguru.jpg', 'https://sarahmotion.com', '{"vimeo": "motionguru", "behance": "sarahmotion"}', 'pending', 78.25, 5600.00, 32, true),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a55', 'newbie_creator', 'newbie@example.com', 'New Creator', 'Just starting out in content creation.', NULL, NULL, '{}', 'unverified', 45.00, 0.00, 0, true),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a66', 'suspended_user', 'suspended@example.com', 'Bad Actor', 'Account suspended for violations.', NULL, NULL, '{}', 'suspended', 10.00, 0.00, 0, false);

-- =============================================================================
-- CONTENT
-- =============================================================================
INSERT INTO content (id, creator_id, title, description, content_type, media_urls, tags, metadata, status, is_nsfw, view_count, like_count)
VALUES
    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Fantasy Character Pack', 'A collection of 10 high-quality fantasy character models with textures and rigging.', '3d_model', '["https://cdn.example.com/content/fantasy_char_1.fbx", "https://cdn.example.com/content/fantasy_char_2.fbx"]', '{"fantasy", "character", "3d", "game-ready"}', '{"polycount": "50k-100k", "formats": ["fbx", "obj"], "rigged": true}', 'published', false, 15420, 892),
    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Sci-Fi Environment Kit', 'Modular sci-fi environment assets for game development.', '3d_model', '["https://cdn.example.com/content/scifi_env_1.fbx"]', '{"sci-fi", "environment", "modular", "game"}', '{"polycount": "200k+", "formats": ["fbx", "blend"]}', 'published', false, 8930, 567),
    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'Pixel Art Tileset - Forest', 'Complete pixel art tileset for 2D platformer games.', '2d_art', '["https://cdn.example.com/content/forest_tileset.png"]', '{"pixel-art", "tileset", "2d", "platformer"}', '{"resolution": "16x16", "tiles": 256}', 'published', false, 22100, 1340),
    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'UI Icon Pack - Gaming', '500+ gaming UI icons in multiple styles.', '2d_art', '["https://cdn.example.com/content/ui_icons.zip"]', '{"ui", "icons", "gaming", "interface"}', '{"count": 500, "styles": ["flat", "outlined", "filled"]}', 'published', false, 18750, 923),
    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a55', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'Ambient Soundscapes Vol. 1', 'Professional ambient soundscapes for games and meditation apps.', 'audio', '["https://cdn.example.com/content/ambient_1.wav", "https://cdn.example.com/content/ambient_2.wav"]', '{"ambient", "soundscape", "meditation", "game-audio"}', '{"duration": "30min", "format": "wav", "sample_rate": "48kHz"}', 'published', false, 5600, 234),
    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a66', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'Cinematic Music Pack', 'Epic orchestral music tracks for trailers and games.', 'audio', '["https://cdn.example.com/content/cinematic_1.mp3"]', '{"cinematic", "orchestral", "trailer", "epic"}', '{"tracks": 10, "duration": "45min", "format": "mp3", "bitrate": "320kbps"}', 'published', false, 12300, 678),
    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a77', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'Logo Animation Template', 'After Effects template for modern logo animations.', 'video', '["https://cdn.example.com/content/logo_anim.aep"]', '{"animation", "logo", "after-effects", "template"}', '{"duration": "5s", "resolution": "4K", "plugins_required": false}', 'published', false, 9800, 445),
    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a88', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'Explainer Video Template', 'Professional explainer video template with characters.', 'video', '["https://cdn.example.com/content/explainer.aep"]', '{"explainer", "video", "template", "animation"}', '{"duration": "60s", "resolution": "1080p"}', 'draft', false, 0, 0);

-- =============================================================================
-- LISTINGS
-- =============================================================================
INSERT INTO listings (id, content_id, creator_id, title, description, price, currency, license_type, usage_rights, is_active, sales_count)
VALUES
    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Fantasy Character Pack - Commercial', 'Full commercial license for the Fantasy Character Pack.', 49.99, 'USD', 'commercial', '{"commercial_use": true, "modification": true, "redistribution": false, "attribution": false}', true, 45),
    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Fantasy Character Pack - Personal', 'Personal use license for the Fantasy Character Pack.', 19.99, 'USD', 'personal', '{"commercial_use": false, "modification": true, "redistribution": false, "attribution": false}', true, 42),
    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Sci-Fi Environment Kit - Commercial', 'Full commercial license for the Sci-Fi Environment Kit.', 79.99, 'USD', 'commercial', '{"commercial_use": true, "modification": true, "redistribution": false, "attribution": false}', true, 28),
    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'Pixel Art Tileset - Commercial', 'Commercial license for the Forest Tileset.', 24.99, 'USD', 'commercial', '{"commercial_use": true, "modification": true, "redistribution": false, "attribution": true}', true, 89),
    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a55', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'UI Icon Pack - Extended', 'Extended license for the Gaming UI Icon Pack.', 39.99, 'USD', 'extended', '{"commercial_use": true, "modification": true, "redistribution": true, "attribution": false, "unlimited_projects": true}', true, 67),
    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a66', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a55', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'Ambient Soundscapes - Commercial', 'Commercial license for Ambient Soundscapes Vol. 1.', 29.99, 'USD', 'commercial', '{"commercial_use": true, "modification": false, "redistribution": false, "attribution": false}', true, 23),
    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a77', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a66', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'Cinematic Music Pack - Commercial', 'Commercial license for the Cinematic Music Pack.', 59.99, 'USD', 'commercial', '{"commercial_use": true, "modification": false, "redistribution": false, "attribution": false}', true, 34),
    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a88', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a77', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'Logo Animation Template - Single', 'Single project license for the Logo Animation Template.', 14.99, 'USD', 'single', '{"commercial_use": true, "modification": true, "redistribution": false, "attribution": false, "projects": 1}', true, 56);

-- =============================================================================
-- TRANSACTIONS
-- =============================================================================
INSERT INTO transactions (id, listing_id, buyer_id, seller_id, amount, currency, platform_fee, seller_earnings, payment_method, payment_status, stripe_payment_intent_id, metadata)
VALUES
    ('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 49.99, 'USD', 7.50, 42.49, 'stripe', 'completed', 'pi_3OqXXXXXXXXXXXXXXXXXXXXX', '{"ip_country": "US"}'),
    ('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 49.99, 'USD', 7.50, 42.49, 'stripe', 'completed', 'pi_3OqYYYYYYYYYYYYYYYYYYY', '{"ip_country": "DE"}'),
    ('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 24.99, 'USD', 3.75, 21.24, 'paypal', 'completed', 'pi_3OqZZZZZZZZZZZZZZZZZZZ', '{"ip_country": "GB"}'),
    ('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a55', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 39.99, 'USD', 6.00, 33.99, 'stripe', 'completed', 'pi_3OqWWWWWWWWWWWWWWWWWWW', '{"ip_country": "JP"}'),
    ('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a55', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a66', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 29.99, 'USD', 4.50, 25.49, 'stripe', 'pending', 'pi_3OqVVVVVVVVVVVVVVVVVVV', '{"ip_country": "FR"}'),
    ('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a66', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a77', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 59.99, 'USD', 9.00, 50.99, 'stripe', 'completed', 'pi_3OqUUUUUUUUUUUUUUUUUUU', '{"ip_country": "CA"}'),
    ('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a77', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a88', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 14.99, 'USD', 2.25, 12.74, 'stripe', 'failed', 'pi_3OqTTTTTTTTTTTTTTTTTTT', '{"ip_country": "BR"}'),
    ('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a88', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 19.99, 'USD', 3.00, 16.99, 'stripe', 'refunded', 'pi_3OqSSSSSSSSSSSSSSSSSSS', '{"ip_country": "AU"}');

-- =============================================================================
-- LICENSES
-- =============================================================================
INSERT INTO licenses (id, transaction_id, licensee_id, licensor_id, content_id, license_type, usage_scope, valid_from, valid_until, is_active)
VALUES
    ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'commercial', '{"project_limit": "unlimited", "seat_count": 5}', '2024-10-15 10:30:00+00', NULL, true),
    ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'commercial', '{"project_limit": "unlimited", "seat_count": 10}', '2024-10-20 14:15:00+00', NULL, true),
    ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'commercial', '{"project_limit": "unlimited", "seat_count": 3}', '2024-11-01 09:00:00+00', NULL, true),
    ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'extended', '{"project_limit": "unlimited", "seat_count": 25, "redistribution": true}', '2024-11-10 16:45:00+00', NULL, true),
    ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a55', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a55', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a55', 'commercial', '{"project_limit": "unlimited", "seat_count": 1}', '2024-11-15 11:20:00+00', '2025-11-15 11:20:00+00', true),
    ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a66', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a66', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a66', 'commercial', '{"project_limit": "unlimited", "seat_count": 5}', '2024-11-20 08:30:00+00', NULL, true),
    ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a77', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a88', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a77', 'single', '{"project_limit": 1, "seat_count": 1}', '2024-11-25 13:00:00+00', NULL, false);

-- =============================================================================
-- MODERATION ACTIONS
-- =============================================================================
INSERT INTO moderation_actions (id, content_id, listing_id, moderator_id, action_type, reason, details)
VALUES
    ('f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', NULL, 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'approve', 'Content meets quality standards.', '{"review_time_minutes": 15}'),
    ('f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', NULL, 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'approve', 'High quality tileset.', '{"review_time_minutes": 10}'),
    ('f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a88', NULL, 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'flag', 'Incomplete content - missing preview images.', '{"missing_items": ["preview_1", "preview_2"]}'),
    ('f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', NULL, 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a88', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'warn', 'Listing description needs improvement.', '{"suggestions": ["Add more details", "Include file format info"]}'),
    ('f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a55', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a66', NULL, 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'remove', 'Copyright violation reported.', '{"report_id": "fr_001", "original_source": "https://example.com/original"}');

-- =============================================================================
-- QUALITY SCORES
-- =============================================================================
INSERT INTO quality_scores (id, content_id, overall_score, technical_score, aesthetic_score, engagement_score, originality_score, scoring_model, details)
VALUES
    ('10eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 0.920, 0.950, 0.900, 0.880, 0.940, 'quality-v2.1', '{"texture_quality": "excellent", "rigging": "professional", "optimization": "good"}'),
    ('10eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 0.880, 0.900, 0.850, 0.820, 0.910, 'quality-v2.1', '{"modularity": "excellent", "texture_quality": "very_good"}'),
    ('10eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 0.950, 0.980, 0.960, 0.900, 0.930, 'quality-v2.1', '{"consistency": "perfect", "tile_seamlessness": "excellent"}'),
    ('10eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 0.870, 0.890, 0.920, 0.800, 0.850, 'quality-v2.1', '{"style_consistency": "very_good", "coverage": "comprehensive"}'),
    ('10eebc99-9c0b-4ef8-bb6d-6bb9bd380a55', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a55', 0.840, 0.860, 0.820, 0.780, 0.880, 'quality-v2.1', '{"audio_quality": "professional", "mix_balance": "good"}'),
    ('10eebc99-9c0b-4ef8-bb6d-6bb9bd380a66', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a66', 0.910, 0.930, 0.890, 0.850, 0.920, 'quality-v2.1', '{"composition": "excellent", "dynamics": "very_good"}'),
    ('10eebc99-9c0b-4ef8-bb6d-6bb9bd380a77', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a77', 0.790, 0.820, 0.850, 0.700, 0.760, 'quality-v2.1', '{"animation_smoothness": "good", "customization": "moderate"}');

-- =============================================================================
-- FRAUD REPORTS
-- =============================================================================
INSERT INTO fraud_reports (id, reporter_id, reported_content_id, reported_listing_id, reported_user_id, report_type, description, evidence, status, resolution, resolved_by, resolved_at)
VALUES
    ('20eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a66', NULL, 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'copyright', 'This content appears to be copied from another source.', '{"urls": ["https://example.com/original"], "similarity_score": 0.95}', 'resolved', 'Content confirmed as copyrighted material. Content removed and user warned.', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '2024-11-28 10:00:00+00'),
    ('20eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', NULL, NULL, 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a66', 'impersonation', 'This user is impersonating another creator.', '{"original_creator": "real_creator_name", "evidence_urls": ["https://example.com/evidence1"]}', 'investigating', NULL, NULL, NULL),
    ('20eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a88', NULL, NULL, 'spam', 'Low quality content with misleading description.', '{"flags": ["misleading_title", "low_quality"]}', 'open', NULL, NULL, NULL),
    ('20eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', NULL, 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a88', NULL, 'fraud', 'Seller not delivering purchased content.', '{"transaction_id": "d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a77", "communication_logs": ["msg1", "msg2"]}', 'dismissed', 'Transaction was refunded. No fraud detected.', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '2024-12-01 14:30:00+00');

-- =============================================================================
-- ANALYTICS EVENTS (Partitioned table)
-- =============================================================================
INSERT INTO analytics_events (id, event_type, user_id, content_id, listing_id, session_id, ip_address, user_agent, referrer, event_data, created_at)
VALUES
    ('30eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'page_view', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', NULL, '40eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'https://google.com', '{"page": "/content/fantasy-character-pack", "duration_seconds": 45}', '2024-10-15 10:30:00+00'),
    ('30eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'page_view', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', NULL, '40eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', '192.168.1.101', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', 'https://twitter.com', '{"page": "/content/pixel-art-tileset", "duration_seconds": 120}', '2024-10-20 14:15:00+00'),
    ('30eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'add_to_cart', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '40eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', NULL, '{"price": 49.99, "currency": "USD"}', '2024-10-15 10:35:00+00'),
    ('30eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'purchase_complete', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '40eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', NULL, '{"transaction_id": "d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", "amount": 49.99}', '2024-10-15 10:36:00+00'),
    ('30eebc99-9c0b-4ef8-bb6d-6bb9bd380a55', 'search', NULL, NULL, NULL, '40eebc99-9c0b-4ef8-bb6d-6bb9bd380a55', '10.0.0.50', 'Mozilla/5.0 (X11; Linux x86_64)', 'https://google.com', '{"query": "fantasy character", "results_count": 15}', '2024-11-01 09:00:00+00'),
    ('30eebc99-9c0b-4ef8-bb6d-6bb9bd380a66', 'content_like', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', NULL, '40eebc99-9c0b-4ef8-bb6d-6bb9bd380a66', '172.16.0.25', 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)', NULL, NULL, '2024-11-10 16:45:00+00'),
    ('30eebc99-9c0b-4ef8-bb6d-6bb9bd380a77', 'page_view', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', NULL, '40eebc99-9c0b-4ef8-bb6d-6bb9bd380a77', '192.168.1.105', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'https://facebook.com', '{"page": "/content/ui-icon-pack", "duration_seconds": 89}', '2024-11-15 11:20:00+00'),
    ('30eebc99-9c0b-4ef8-bb6d-6bb9bd380a88', 'purchase_complete', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a55', '40eebc99-9c0b-4ef8-bb6d-6bb9bd380a88', '192.168.1.101', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', NULL, '{"transaction_id": "d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44", "amount": 39.99}', '2024-11-10 16:46:00+00');

-- =============================================================================
-- AUDIT LOG (Sample entries - normally populated by triggers)
-- =============================================================================
INSERT INTO audit_log (id, table_name, record_id, action, old_values, new_values, changed_by, changed_at, ip_address, user_agent)
VALUES
    ('50eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'creators', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'INSERT', NULL, '{"username": "artista", "email": "artista@example.com"}', NULL, '2024-10-01 08:00:00+00', '192.168.1.1', 'Mozilla/5.0'),
    ('50eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'content', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'UPDATE', '{"status": "draft"}', '{"status": "published"}', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '2024-10-10 12:00:00+00', '192.168.1.50', 'Mozilla/5.0'),
    ('50eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'transactions', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'INSERT', NULL, '{"amount": 49.99, "payment_status": "completed"}', NULL, '2024-10-15 10:36:00+00', '10.0.0.1', 'Stripe Webhook'),
    ('50eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'listings', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'UPDATE', '{"sales_count": 44}', '{"sales_count": 45}', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '2024-10-15 10:36:00+00', '10.0.0.1', 'System');
