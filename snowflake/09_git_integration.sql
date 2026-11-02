-- =====================================================================
-- DATABANK · 09 · Link Snowflake to the GitHub repository
-- After this, the repo can be opened as a Snowflake workspace:
--   Projects > Workspaces > workspace menu > Create workspace > From Git repository
--   URL: https://github.com/lhervy/databank-data-platform
--   API integration: GITHUB_DATABANK · Authentication: OAuth (sign in with GitHub)
-- Changes are then pulled / pushed with the Git buttons in the workspace.
-- =====================================================================
USE ROLE ACCOUNTADMIN;

CREATE API INTEGRATION IF NOT EXISTS GITHUB_DATABANK
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/lhervy')
  API_USER_AUTHENTICATION = (TYPE = snowflake_github_app)
  ENABLED = TRUE
  COMMENT = 'Git access to github.com/lhervy/databank-data-platform';

GRANT USAGE ON INTEGRATION GITHUB_DATABANK TO ROLE DATABANK_ENGINEER;

SHOW API INTEGRATIONS LIKE 'GITHUB_DATABANK';
