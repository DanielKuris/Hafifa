# Air Quality Index - Building an API

Yan and Sapir were sitting at a bakery in Haifa when they realized that the air surrounding them is very very polluted.
They decided that this is really dangerous and should be monitored. They thought about who could organize all this data and monitor it, and called their friends (and former co-workers) in Optimus team. And luckily, they have the best developers to do it! 

## Your Mission

This exercise is a rolling exercise that will include creating a DB and building an API with error handling, tests and loggers.
Examples for csv files are under the folder `air_quality_files/`

**The API will:**
- Process air quality data from various cities around the country.
- Calculate the AQI (Air Quality Index) for each city using a given function.
- Store the AQI data along with the pollutants (PM2.5, NO2, CO2) in a database for analysis and reporting.
- Allow residents to check the air quality by querying the system, so they can decide if it’s safe to walk in the park or if they should keep their windows shut.

## The API’s Functionality
You will need to implement the following functionalities:

- **Upload Air Quality Data:**
  residents at various cities will upload CSV files containing PM2.5, NO2, CO2 levels.
  Each file will also include a date and the city name.

- **Validate the Data:**
  Implement functionality to validate and clean uploaded data before saving it to the database.
  For example, Rows with missing or corrupted values should be logged and ignored.

- **Calculate the AQI:**
  You will use a function given to you in the file `calculate_aqi.py` to calculate the AQI based on
  the pollution levels.
  This AQI will be stored along with the pollutants.

- **Store Data in a Choosen Database:**
  The database will store the date, city name, PM2.5, NO2, CO2, and the calculated AQI.
  The data will be used for future analysis to track air quality trends across cities.
  If the AQI value is over 300, it will be saved in "alerts" table that will have the fields: date, city and AQI.
  Think about what database is the most compatible

- **Query for Insights:**
  You’ll create endpoints that allow residents to check the air quality in real-time.
  They will be able to query the system to see which city has the best or worst air quality on a given day.

- **Error Handling:**
  Not all data will be clean and valid, so your API should handle issues like missing pollutant data, invalid dates, or corrupt files gracefully.
  It should also return informative error messages to help users fix any problems with their uploads.

- **Logging:**
  The government wants to ensure that everything is logged for transparency and future auditing.
  All actions (like file uploads, data processing, AQI calculations) should be logged into a file.

- **Testing:**
  To ensure everything is ok and check all possible cases, you will need to create tests for every function you think is necessary. Use mock if needed.

### How the AQI Calculation Works
The AQI is a number that reflects how clean or polluted the air is, and it is calculated using the pollutant levels. Here's a simplified version of how it might work:

- PM2.5 is the most critical factor in the AQI calculation.
- NO2 and CO2 are secondary, but still important.

You will calculate it using a given function "calculate_aqi(pm25, no2, co2)" that will take the pollutant values and return an AQI value between 0 (good air quality) and 500 (hazardous air quality), and the AQI level (ranged from "Good" to "Hazardous"). The AQI data (AQI and AQI level) will be saved in the database for each row of data.

## API Endpoints

- **POST upload air quality data**
  - Description: Uploads air quality data from a CSV file to the database.
  - Request Body: A multipart/form-data request containing a CSV file.

- **GET air quality data**
  - Description: Retrieves air quality data for a specific date range.
  - Query Parameters:
    - start_date: The start date in YYYY-MM-DD format.
    - end_date: The end date in YYYY-MM-DD format.

- **GET air quality data by city**
  - Description: Retrieves air quality data for a specific city.
  - Query Parameters:
    - city: The name of the city.

- **GET city aqi history**
  - Description: Retrieves the AQI history for a specific city.
  - Query Parameters:
    - city: The name of the city.

- **GET city aqi average**
  - Description: Retrieves the AQI average for a specific city.
  - Query Parameters:
    - city: The name of the city.

- **GET best cities**
  - Description: Retrieves the 3 cities with the best air quality based on the AQI. The best
    cities will have the lowest AQI values.

- **GET all alerts**
  - Description: Retrieves all alerts.

- **GET all alerts by date**
  - Description: Retrieves all alerts from a specific date.
  - Query Parameters:
    - date: The date in YYYY-MM-DD format.

- **GET all alerts by city**
  - Description: Retrieves all alerts for a specific city.
  - Query Parameters:
    - city: The name of the city.


## Good Luck! (:


## My Implementation 

- **API Routing:** Organized endpoints into separate routers for air quality data and alerts data.
- **Database:** Used PostgreSQL with SQLAlchemy ORM models to define and manage the database tables.
- **Connection Management:** Configured a SQLAlchemy engine with connection pooling and a session factory to manage database sessions.
- **Repository Layer:** Implemented a repository class to centralize database operations and queries.
- **Service Layer:** Separated business logic from API routes and database operations using dedicated service modules.
- **Data Duplications:** Duplicate measurements are intentionally preserved as separate database rows.
- **Data Processing:** Used Pandas to validate, clean, and process CSV data before inserting measurements and generating alerts.