# Description

## Code structure
Python 3.8.2 version was used for development. Code is structured into single python script **webScraper.py**, which is executable from command line. All functionality is occupied in single instance **MovieScrapper**. Object has method for data parsing, data visualization and instance functionality execution.

## Execution
To execute web scraping install requirements and run in terminal **python webScraper.py --path 'your/local/folder/'** command. You have to specify local path, where results will be stored.

## Results
After script execution in given path **result.csv**, **scatter.png** files will be stored and  **app.log** file in repository directory. Also in your web browser interactive plotly chart will be displayed.
