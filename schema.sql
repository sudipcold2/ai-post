-- Run this in the Supabase SQL Editor

-- Create the app_config table
CREATE TABLE IF NOT EXISTS public.app_config (
    id TEXT PRIMARY KEY,
    config_data JSONB NOT NULL
);

-- Note: The Python backend will automatically insert the 'main' row combining your current config.json if the database is empty when it first starts.

-- Create the post_history table
CREATE TABLE IF NOT EXISTS public.post_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    timestamp TEXT NOT NULL,
    group_key TEXT,
    group_name TEXT,
    content TEXT NOT NULL
);

-- Enable Row Level Security (RLS) and allow all access for now since you are using the service key / anon key purely from your secured Python backend
ALTER TABLE public.app_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.post_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all access to app_config" ON public.app_config FOR ALL USING (true);
CREATE POLICY "Allow all access to post_history" ON public.post_history FOR ALL USING (true);
