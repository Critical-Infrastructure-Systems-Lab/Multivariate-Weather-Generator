"""
The distance calculation, which considers other variables besides 'precipitation' was taken from [1].

[1] A semiparametric multivariate, multisite weather generator with low-frequency variability for use in climate risk assessments,
Scott Steinschneider and Casey Brown (2013)

"""
import numpy as np
import pandas as pd
from random import choices
from utilities import waterday_range, variables_monthly_stats
from constants_ import DATE, SAMPLE_DATE, STATE, STATE_PREV, WDAY

class LagOne:

    """
    Selectes, based on a weighted Euclidean distance, the days which follows the state sequence generated by the first order Markov 
    Chain. Here a multivariate version can be considered if the historic data be so.
    
    Args
    ----------
    training_data: Dataframe sampled from the historic data, with the with the days labeled as 'd' (dry), 'w' (wet) or 'e' (extreme). 

    dfsimu: Dataframe structure where the new timeseries will be stored. Alredy filled with the 'Date', the day of the year and the
        'state' and 'state_prev' sequences.

    weather_variables: a list with the columns names of the weather variables present in the daily historic data.

    weather_mean: a list with of the name of the variables after computed the mean of them. For instance, the IBM WeatherGen accepts 
        the temperature as 't_min' and 't_max', but needs to compute the mean ('temperature') of them to be considered in the weighted Euclidean distance.

    Properties
    ----------
    training_data : pd.DataFrame
        DataFrame with the sampled daily data from the historic data.

    dfsimu : pd.DataFrame
        DataFrame strutcture to be filled with the variables values computed with the weighted Euclidean distance.

    weather_vars : list
        list with the original name of the weather variables.

    weather_mean: list
        list with the name of the weather variables after compute what needs to be computed in order to compute correctly the
        weighted Euclidean distance.

    """
    
    def __init__(self, training_data: pd.DataFrame, 
                dfsimu: pd.DataFrame, 
                weather_variables: list, 
                weather_mean: list) -> None:
        
        self.training_data = training_data
        self.dfsimu = dfsimu 
        self.weather_vars = weather_variables #contains the 'key_variable' (precipitation)
        self.weather_mean = weather_mean 

    def search_first(self, date: pd.Timestamp, state: str) -> int:

        """ Search through a window method for the weather variables for the first day of the state sequence, if it was
            not found considering the day_of_year = 1.

            Returns
            ----------
                A int, being the size of the window where finds the occurence of the state closest to the day of the year = 1.

        """

        length = 0
        window = 7
        while (length == 0):

            days_window = waterday_range(day=date, window=window)

            crt = self.training_data[ (self.training_data[WDAY].isin(days_window)) &
                        (self.training_data[STATE] == state)]

            window = window + 1
            length = len(crt)

        return window
    
    def get_dates(self, date: pd.Timestamp, month: int, state: str, state_prev: str, prev: pd.Series, dates_taken: list)->int:

        """ Get the closest row of the training data where for filling the variables values in the timeseries.

        Returns
        ----------
            A index of the row with the closest values to the previous variables.

        """
                
        days_window = waterday_range(day=date, window=7)

        current = self.training_data[ (self.training_data[WDAY].isin(days_window)) &
                    (self.training_data[STATE] == state) &
                    (self.training_data[STATE_PREV] == state_prev) ]

        #---- conditionals 
        if len(current) == 0:
            days_window = waterday_range(day=date, window=45)
            current = self.training_data[ (self.training_data[WDAY].isin(days_window)) & 
                        (self.training_data[STATE] == state) &
                        (self.training_data[STATE_PREV] == state_prev) ]

        if len(current) == 0:
            days_window = waterday_range(day=date, window=7)
            current = self.training_data[ (self.training_data[WDAY].isin(days_window)) & 
                        (self.training_data[STATE] == state) ]

        if len(current) == 0:
            days_window = waterday_range(day=date, window=45)
            current = self.training_data[ (self.training_data[WDAY].isin(days_window)) & 
                        (self.training_data[STATE] == state) ]

        if len(current) == 0:
            current = self.training_data[ (self.training_data[STATE] == state) ]

        if len(current) == 0:
            current = self.training_data[ (self.training_data[DATE] == date) ]

        #----
        k = np.round( np.sqrt(len(current)) )

        stats = variables_monthly_stats(self.training_data, self.weather_mean)

        dstc = 0
        for weather in self.weather_mean:
            w = ( (current[f'{weather}_prev'] - stats[month-1][f'{weather}_mean']) /stats[month-1][f'{weather}_sd'] )
            dstc += abs(w)*(prev[f'{weather}'] - current[f'{weather}_prev'])**2

        current = current.assign( distance = np.sqrt( dstc ) )

        current.sort_values('distance', inplace=True)
        if k > 10: current = current.head(int(k))

        current = current.assign( prob = ( 1/(current.index+1) ) / sum(1/(current.index+1)) )

        while True:
            std = choices(population=current.index, weights=current['prob'], k=1)[0] 

            if std in dates_taken:
                if len(current) == 1:
                    break
                else:
                    current.drop([std], inplace=True)

            if std not in dates_taken:
                dates_taken.append(std)
                break
        
        if len(dates_taken) > 5: dates_taken.remove(dates_taken[0])
                
        return std, dates_taken

    def get_series(self)->pd.DataFrame:
        
        """ Compute the monthly mean and the standard deviation for each weather variable.

            Returns
            ----------
                A new timeseries with the spatially aggregated daily values simulated, being 'sample_dates' the
                days sampled from the observed data.
        """
        
        dates_taken=[]
        for i, row in self.dfsimu.iterrows():
                
            if (i == 0) and (row[STATE] not in self.training_data[(self.training_data[WDAY] == 1)][STATE].unique()):    
                
                window = self.search_first(date=row[DATE], state=row[STATE])
                
                days_window = waterday_range(day=row[DATE], window=window)
                current = self.training_data[ (self.training_data[WDAY].isin(days_window)) & (self.training_data[STATE] == row[STATE])]
                
                std = choices(population = current.index, k=1)[0]
                
            elif i == 0:

                std = choices(population = self.training_data[ (self.training_data[STATE] == row[STATE]) & 
                                                                (self.training_data[WDAY] == row[WDAY]) ].index, k=1)[0]

            else:
                month = row[DATE].month

                std, dates_taken = self.get_dates(row[DATE], month,
                                    row[STATE],
                                    row[STATE_PREV],
                                    pd.Series(self.dfsimu.loc[i-1][self.weather_mean]),
                                    dates_taken
                                )
            
            self.dfsimu.at[i, SAMPLE_DATE] = self.training_data.at[std, DATE]
            for weather in self.weather_vars:
                self.dfsimu.at[i, f'{weather}'] = self.training_data.at[std, f'{weather}']

            self.dfsimu[SAMPLE_DATE] = self.dfsimu[SAMPLE_DATE].astype('datetime64[ns]')

        return self.dfsimu.drop([STATE, STATE_PREV, WDAY], axis=1)