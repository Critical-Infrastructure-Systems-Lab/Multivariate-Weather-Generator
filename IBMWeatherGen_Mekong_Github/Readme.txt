Step 1: Formatting the training data
	
	The merged & re-gridded data (netCDF) should be obtained from Linux with the name "merged_[spatial resolution]_[variable].nc". In Linux, this is done using Climate Data Operators, namely *cdo mergetime* and *cdo remapbil*.

	Process the netCDF files using "Data Processing.ipynb", which can be found in folder "data/raw". The code outputs a flattened version of the 4 netCDF datasets (column bind): precipitation, Tmin, Tmax, and wind. 

	By default, the training file should be placed in the "data" folder with title "Training.csv". 

Step 2: Configure the simulation

	The simuation configuration can be customized using "ibmwg-input.json" The parameters include:
		
		START_YEAR: Starting year for simulations.
		
		NUM_YEARS: Number of years to simulate ahead. If outside training dataset range, the model will use forecaster models e.g., ARIMA.
		
		NUM_SIMULATIONS: Number of simulation sets.
		
		WET_EXTREME: Threshold for extreme events in the Markov Chain.
		
		USE_G2S: Whether to use GeoStatistical Server (G2S), a framework that uses Multiple Point Statistics (MPS) algorithms. This is not necessary and requires separate installation/setup.

Step 3: Running the simulation
	
	To reproduce the result, simply run "Wrapper.ipynb" in folder "src", in which the number of simulations can be changed.

Step 4: Output

	In default setting, the output will be a series of .csv files in the "simulations" folder titled "ibmwg-simulations_" + system time.

Step 5: Plotting & Analysis

	To reproduce the graphs, run "Plotting.ipynb" in the "simulations" folder.

Step 6: Validation

	To quantitatively validate the generated results, run "Validation.ipynb" in the "validation" folder. By default, the simulations should be placed in the folder "1-100". We used a Kolmogorov–Smirnov test, which was performed on the monthly average T_max for January for 100 years of generated data.


