# slate_exports

A utility that will automate query runs in Slate.

Got a list of scheduled export queries that you need to run more frequently than the delivery windows will allow? This tool will help automate that task.

## Setup

1. Clone `sample_config.py`, renaming it to `config.py`
2. Configure a query in your slate environment that will return a list of queries to run. Make sure to include `query.[id]`. `query.[active]` and `query.[name]` in the exports.
3. Add an entry in the `SLATE_ENVS` for the query you just defined, making to sure to define `host` and `endpoint` keys correctly.
4. Store your login credentials as environment variables `SLATE_EXPORTS_USER` and `SLATE_EXPORTS_PASSWORD`. This app is configured to login as an external user. Optionally, set `SLATE_EXPORTS_SLACK_WEBHOOK` to a valid Slack webhook to get messages logged to Slack.

## Usage

Run the script with one or more of the following arguments:

- `--integrations`: will run all of the queries actively scheduled under Peoplesoft Service Account
- `--one-offs`: will run all of the queries configured under `config.ONE_OFF_QUERIES`
- `--imports`: will force pickup/import for any environments configured under `config.IMPORT_HOSTS`

```bash
# run integrations only
python app.py --integrations

# run one-off queries
python app.py --one-offs

# run both
python app.py --integrations --one-offs
```

The script authenticate with your environments and then use requests to retrieve the list of queries to run for each environment defined in your `config.py`. For each query, if the `active` attribute is true, it will run the export job and log the result. Logs will be piped to `stdout` as well as `app.log`.
