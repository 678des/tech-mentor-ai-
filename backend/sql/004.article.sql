alter table public.articles
  drop constraint articles_save_type_check;

alter table public.articles
  add constraint articles_save_type_check
  check (save_type is null or save_type in ('later', 'important', 'done'));