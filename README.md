# strava-api-function
Python code for the Strava API Cloud Function used in the [Strava API Terraform](https://github.com/maxhabra/strava-api-terraform).

## Function Walkthrough
The Function performsn the following actions:
- Fetches secrets from GCP's Secret Manager
    - `strava_ClientID`
    - `strava_ClientSecret`
    - `strava_RefreshToken`
- Retrieves `access_token` from Strava
- Retrieves Strava Activities
- Loads Activities in Bigquery

## Function Configuration
The function can have the following settings:
- function_name: `name_your_function`
- Region: `closest_location`
- Trigger: `HTTP`
- Authentication: `required`
- Advanced (optional)
    - Memory: `128 mb`
    - Timeout: `60s`
    - Autoscaling: `1`
- Runtime: `python38`
- Entry_point: `run`
- service_account: your function service account
nb: terraform deployment code is included in the [terraform repository](https://github.com/maxhabra/strava-api-terraform).

## Variables
The function requires some variable to be edited in the code prior to deployment:
- `GCP_PROJECT_ID`
- `BQ_DATASET`
- `BQ_TABLE`