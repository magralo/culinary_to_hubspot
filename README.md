# craiglist_to_hubspot


# preparing the envioronment

1. Create a conda envioronment
2. Install dependencies
3. Define the env variable hs_token with the value of the token to authenticate into HubSpot.
4. Define GOOGLE_APPLICATION_CREDENTIALS as the path to the json to authenticate into bigquery


# Deploy on google cloud run

Use the file cloudbuild -EXAMPLE.yaml and change TOKEN with the actual value of the token... then rename it as cloudbuild.yaml, the last step is to run everything with:

``` bash
gcloud builds submit 
```


# Understanding the API endpoints's logic 

## /upload_city

The logic here is simple
1. We go into craiglist hospitality jobs of a given city (according to the URL in the variable defined as "links")
2. We list of the links on that page
3. We visit each link and get the data from the HTML (if available)
4. At the end we upload the data for the URL that havent been uploaded to bigquery 


## /create_companies

This reads the data from bigquery and uploads the companies that have not been created before. Please take into account that we create one registry per company/location
