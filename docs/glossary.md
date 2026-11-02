# Glossary

Every technical word used in this repository, in plain language.

| Term | Meaning |
|---|---|
| **AML** | Anti-money laundering: checks a bank must run to detect suspicious payments. |
| **API (REST)** | A web address that a program calls to get data, here the European Central Bank's exchange rates. |
| **Bronze / Silver / Gold** | The three layers of the medallion architecture: raw data, cleaned data, business-ready data. |
| **CDC (change data capture)** | Copying only the rows that changed in an operational database, instead of the whole table each time. |
| **CI/CD** | Automatic checks (CI) and deployment (CD) run on every code change. |
| **Compute pool** | A group of machines in Snowflake that runs containers (used here by the dashboard). |
| **Container / image (Docker)** | An image is a package of code + runtime + libraries; a container is a running copy of it, identical on every machine. |
| **COPY INTO** | The Snowflake command that loads files from a stage into a table. |
| **Credit** | Snowflake's unit of compute cost (about $3 on this account). |
| **DAG** | Directed acyclic graph: a chain of tasks where each task waits for the ones before it, with no loops. |
| **dbt** | A tool to write transformations as SQL files, with tests and documentation, and run them in the right order. |
| **dbt model / test / source** | A model is one SQL file that builds one table or view; a test checks a rule on the data; a source is a raw table dbt reads but does not build. |
| **Dynamic table** | A Snowflake table defined by a query that Snowflake keeps up to date by itself within a target delay (here 1 minute). |
| **ELT / ETL** | Extract-Load-Transform (load raw data first, transform in the warehouse) vs Extract-Transform-Load. We use ELT. |
| **GitHub Actions** | GitHub's service that runs our code on a schedule or on each change, on temporary machines. |
| **Idempotent** | Running a job twice gives the same result as running it once (no duplicates). |
| **Incremental load** | Loading only what is new since the last run. |
| **Infrastructure as Code (IaC)** | Describing infrastructure (databases, warehouses, permissions) in versioned files instead of clicking in a console. |
| **Key pair authentication** | A program proves who it is with a private key instead of a password; used by GitHub Actions to log in to Snowflake. |
| **Lineage** | Knowing where each piece of data comes from (which source, which file). |
| **Marketplace (Snowflake)** | A catalogue of datasets other companies share; we use free real stock prices and exchange rates. |
| **Masking policy** | A rule that hides a column (for example a name) for some roles and shows it to others. |
| **Medallion architecture** | Organising data in Bronze, Silver and Gold layers. |
| **MERGE** | A SQL command that updates a row if it exists and inserts it if it does not. |
| **Micro-batch** | Sending data in very small groups, very often (here every 10 seconds). |
| **Micro-partition / pruning** | Snowflake splits tables into small blocks; pruning means skipping the blocks that cannot match a query. |
| **OAuth** | A way to let one service access another on your behalf after you approve it (used for the Snowflake ↔ GitHub link). |
| **OLTP / OLAP** | Operational database (many small writes, e.g. the core banking system) vs analytics database (big reads, e.g. Snowflake). |
| **Orchestration** | Running several dependent jobs in the right order, with failure handling and monitoring. |
| **Parquet** | A compressed, column-based file format, faster to query than CSV. |
| **Resource monitor** | A Snowflake budget that sends alerts and suspends warehouses when a credit limit is reached. |
| **Role** | A set of permissions in Snowflake; users get roles, roles get access to objects. |
| **Row access policy** | A rule that filters which rows a user can see (here: a client sees only their own data). |
| **Schema on read / on write** | Structure applied when data is read (flexible, Bronze) vs when it is written (strict, Silver and Gold). |
| **Secure data sharing** | Reading data stored in another Snowflake account without copying it. |
| **Secure view** | A view whose definition is hidden from users, used to expose data to the app safely. |
| **Snowpipe** | Snowflake's serverless service that loads files automatically as soon as they arrive. |
| **Stage** | A landing zone for files inside (or connected to) Snowflake, before they are loaded into tables. |
| **Stream (Snowflake)** | An object that records the changes made to a table since it was last read; the basis of our CDC. |
| **Streamlit** | A Python library to build simple web dashboards; it runs inside Snowflake here. |
| **Task (Snowflake)** | A scheduled SQL statement; tasks can be chained into a DAG. |
| **Terraform** | A tool that creates cloud infrastructure from configuration files and tracks what exists in a state file. |
| **Token (card)** | A replacement value for a card number, so the real number is never stored. |
| **Warehouse (Snowflake)** | The compute that runs queries; it can be started, stopped and resized independently of storage. |
| **Watermark** | The last value already loaded (for example the latest date), used to ask the source only for newer data. |
