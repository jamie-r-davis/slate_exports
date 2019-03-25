# slate_exports

A utility that will automate query runs in Slate.

Got a list of scheduled export queries that you need to run more frequently than the delivery windows will allow? This tool will help automate that task.

## Setup

1. Clone `sample_config.py`, ranaming it to `config.py`
2. Add your SSO login credentials
3. Configure a query in your slate environment that will return a list of queries to run. Make sure to include `query.[id]` and `query.[name]` in the exports.
4. Add an entry in the `SLATE_ENVS` for the query you just defined, making to sure to define `host` and `endpoint` keys correctly.

## Usage

Run the script with:
```python
python app.py
```

The script will use a headless chrome driver to authenticate. Then it will use requests to retrieve the list of queries to run for each environment defined in your `config.py`. For each query, it will run the export job and log the result. Logs will be piped to `stdout` as well as `app.log`.
