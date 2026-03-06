from pathlib import Path
import pandas as pd


class BoundaryConditionProvider:
    """
    Provides FORCAsT boundary condition files from either:

    - A pandas DataFrame
    - A CSV file

    Allows flexible column mapping and file mapping.
    """

    def __init__(
        self,
        data=None,
        csv_path=None,
        column_mapping=None,
        file_mapping=None,
        datetime_column="datetime",
        csv_read_kwargs=None,
        data_timezone="UTC",
        simulation_timezone="UTC",
    ):
        """
        Parameters
        ----------
        data : pandas.DataFrame
            Preloaded dataframe (must include datetime index or datetime column)

        csv_path : str or Path
            Path to CSV file

        column_mapping : dict
            Maps dataframe column names -> FORCAsT variable names

        file_mapping : dict
            Maps FORCAsT variable names -> output filenames

        datetime_column : str
            Name of datetime column if not already index

        csv_read_kwargs : dict
            Arguments to be passed to pandas.read_csv()

        data_timezone : tzinfo
            Timezone of the data array

        simulation_timezone : tzinfo
            Timezone for FORCAsT input
        """

        if data is None and csv_path is None:
            raise ValueError("Provide either `data` or `csv_path`.")

        self.data = data
        self.csv_path = Path(csv_path) if csv_path else None
        self.column_mapping = column_mapping or {}
        self.file_mapping = file_mapping or {}
        self.datetime_column = datetime_column
        self.csv_read_kwargs = csv_read_kwargs or {}
        self.data_timezone = data_timezone
        self.simulation_timezone = simulation_timezone


    # ------------------------------------------------------------------
    # PUBLIC METHOD
    # ------------------------------------------------------------------

    def populate_data_directory(self, model):

        df = self._load_data()

        # Timezone alignment
        df = self._align_timezones(df, model)

        # Restrict to simulation window
        start = model.model_start
        end = model.model_end

        df = df.loc[start:end - pd.Timedelta(minutes=30)]

        if df.empty:
            raise ValueError("No boundary data available for simulation window.")

        self._validate_halfhourly(df)

        # Rename columns to FORCAsT variable names
        df = df.rename(columns=self.column_mapping)

        # Write each variable to its own file
        for variable, filename in self.file_mapping.items():

            if variable not in df.columns:
                raise ValueError(f"Variable '{variable}' not found in dataframe.")

            output_path = model.directory_manager.get_data_dir() / filename

            self._write_single_variable(
                df[variable],
                output_path,
                start
            )


    # ------------------------------------------------------------------
    # INTERNAL METHODS
    # ------------------------------------------------------------------

    def _load_data(self):

        if self.data is not None:
            df = self.data.copy()

        else:
            df = pd.read_csv(
                self.csv_path,
                parse_dates=[self.datetime_column],
                **self.csv_read_kwargs
            )

        if self.datetime_column in df.columns:
            df = df.set_index(self.datetime_column)

        df = df.sort_index()

        return df

    def _align_timezones(self,df,model):
        # Ensure model start has timezone
        if model.model_start.tzinfo is None:
            model.model_start = model.model_start.tz_localize(
                    self.simulation_timezone
            )
            model.model_end = model.model_end.tz_localize(
                    self.simulation_timezone
            )

        # Handle dataframe timezone
        if df.index.tz is None:
            if self.data_timezone is None:
                raise ValueError(
                        "Data has no timezone. Provide 'data_timezone'."
                )
            df.index = df.index.tz_localize(self.data_timezone)

        if df.index.tzinfo is not model.model_start.tzinfo:
            # convert to simulation timezone
            df.index = df.index.tz_convert(model.model_start.tzinfo)

        return df


    def _validate_halfhourly(self, df):

        inferred = pd.infer_freq(df.index)

        if inferred not in ("30T", "30min"):
            raise ValueError(
                f"Boundary data must be half-hourly. Detected frequency: {inferred}"
            )


    def _write_single_variable(self, series, file_path, model_start):

        with open(file_path, "w") as f:

            f.write(f"time_since_start\t{series.name}\n")
            for timestamp, value in series.items():
                seconds_since_start = int(
                        (timestamp - model_start).total_seconds()
                )

                f.write(f"{seconds_since_start}\t{value:.6f}\n")

