// --- LIVE CV DATABASE SCHEMA V5 (Cloud-Native Product) ---

// Base Mixin Fields (Applied to all tables mentally)
// - created_at: timestamp
// - updated_at: timestamp

Table profile {
  id integer [primary key]
  full_name varchar
  headline jsonb [note: '{"en": "Dev", "pt": "Dev"}'] 
  about_text jsonb
  summary_text jsonb
    
  cv_english varchar
  cv_spanish varchar
  cv_portuguese varchar
  social_links jsonb [note: '{"linkedin": "url", "github": "url"}']
  terminal_theme varchar [default: "green_matrix"]
  
  created_at timestamp
  updated_at timestamp
}

Table experiences {
  id integer [primary key]
  company_name varchar
  role jsonb
  start_date date
  end_date date
  is_current boolean
  description jsonb
  display_order integer
  created_at timestamp
  updated_at timestamp
}

Table projects {
  id integer [primary key]
  slug varchar [unique]
  title jsonb
  short_description jsonb
  long_description jsonb
  
  repo_url varchar
  live_url varchar
  featured boolean
  
  created_at timestamp
  updated_at timestamp
}

// NEW: Dedicated Gallery Table (Replaces gallery jsonb)
Table project_images {
  id integer [primary key]
  project_id integer [ref: > projects.id]
  image_url varchar [note: 'Cloudflare R2 CDN link']
  is_cover boolean [default: false]
  is_video boolean [default: false]
  display_order integer [note: '1, 2, 3, 4']
  
  created_at timestamp
  updated_at timestamp
}

Table skills {
  id integer [primary key]
  name varchar
  icon_css_class varchar
  category varchar [note: 'Backend, Frontend, DevOps']
  created_at timestamp
  updated_at timestamp
}

// THE BRIDGE (Many-to-Many)
Table project_skills {
  project_id integer [ref: > projects.id]
  skill_id integer [ref: > skills.id]
}

Table spoken_languages {
  id integer [primary key]
  language_name jsonb [note: '{"en": "Portuguese", "pt": "Português"}']
  proficiency_level jsonb
  icon_code varchar [note: 'br, us, es']
  created_at timestamp
  updated_at timestamp
}

Table contact_messages {
  id integer [primary key]
  name varchar
  email varchar
  message text
  is_read boolean [default: false]
  created_at timestamp
}

Table rag_documents {
  id integer [primary key]
  source varchar [note: 'cv_pt.pdf - Page 1']
  content text [note: 'Raw text chunk']
  language varchar [note: 'pt, en, es']
  embedding vector [note: '1536 dim (pgvector)']
  active boolean
  created_at timestamp
}

Table users {
  id integer [primary key]
  username varchar [unique]
  password varchar
  email varchar [unique]
  created_at timestamp
  updated_at timestamp
}

Table chat_logs {
  id integer [primary key]
  user_message text 
  bot_reply text
  language varchar [note: 'pt, en, es']
  created_at timestamp
}

Table uploaded_documents {
  id integer [primary key]
  filename varchar 
  file_path varchar
  language varchar [note: 'pt, en, es']
  created_at timestamp
}

Ref: "skills"."id" < "skills"."category"