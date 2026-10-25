-- Single-user prototype profile. The id constraint intentionally allows one row only.
create table public.user_context (
  id smallint primary key default 1 check (id = 1),
  career_goal text not null default '',
  current_focus text not null default '',
  subjects text[] not null default '{}',
  interests text[] not null default '{}',
  current_situation text not null default '',
  projects text[] not null default '{}',
  updated_at timestamptz not null default now()
);

insert into public.user_context (
  id,
  career_goal,
  current_focus,
  subjects,
  interests,
  current_situation,
  projects
)
values (
  1,
  'フルスタックWebエンジニアまたはクラウドインフラエンジニアを目指す',
  '情報を集める不安を減らし、自分のペースで学びや開発を続ける',
  array['情報数学', 'データ構造とアルゴリズム', '情報デザイン基礎', 'Linux演習基礎', '英語', '情報関連法規と情報倫理', 'C++', 'Java', 'Python'],
  array['Next.js', 'TypeScript', 'AIエージェント開発', 'AI駆動開発', 'C# / Unity / Blender', 'AI時代のエンジニアのキャリア', 'UI/UX・情報デザイン', 'クラウド・インフラ'],
  '技術情報を見て不安に飲まれず、事実を受け止めながら自分のペースで前に進みたい',
  array['TechMentor AI（RSS記事の収集・推薦アプリ）', 'Unity自動化エージェント']
)
on conflict (id) do nothing;
