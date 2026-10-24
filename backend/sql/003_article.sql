alter table public.articles
  add column is_read boolean not null default false,
  add column save_type text,
  add column user_note text;

alter table public.articles
  add constraint articles_save_type_check
  check (save_type is null or save_type in ('later', 'important'));