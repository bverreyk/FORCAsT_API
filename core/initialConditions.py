import os
import sys
pp = os.path.realpath(__file__)
for _ in range(2):
    pp = os.path.dirname(pp)

#Add API root to path
sys.path.append(os.path.join(pp))

from utils.conversions import temperature_Celsius_to_Kelvin

import pandas as pd
import numpy as np

class InitialConditions:
    """
    Container for FORCAsT initial conditions.

    Can update selected parameters from a time-indexed
    dataframe or CSV using ForcastModel.date_start.
    """

    def __init__(
        self,
        grndT0=288.69,
        towT0=290.35,
        lapse=0.0098,
        zs=[-0.05, -0.18, -0.42, -0.76, -1.10],
        eta=[0.097, 0.095, 0.104, 0.174, 0.232],
        temps=[287.0, 286.3, 285.7, 285.0, 284.5],
        bd=1.14,
        sandfc=0.32,
        siltfc=0.35,
        clayfc=0.33
    ):
        self.grndT0 = grndT0
        self.towT0 = towT0
        self.lapse = lapse

        self.zs = list(zs)
        self.eta = list(eta)
        self.temps = list(temps)

        self.bd = bd
        self.sandfc = sandfc
        self.siltfc = siltfc
        self.clayfc = clayfc

        self._validate_profiles()


    # ------------------------------------------------------------------
    # INTERNAL VALIDATION
    # ------------------------------------------------------------------

    def _validate_profiles(self):
        if not (len(self.zs) == len(self.eta) == len(self.temps)):
            raise ValueError(
                "zs, eta and temps must have identical length."
            )


    # ------------------------------------------------------------------
    # UPDATE FROM DATAFRAME
    # ------------------------------------------------------------------

    def update_from_dataframe(
        self,
        data,
        model_date_start,
        soil_temperature_columns,
        soil_moisture_columns,
        grndT0_column,
        towT0_column,
        temperature_data_unit="K",
        model_timezone=None,
        data_timezone=None,
        tolerance="nearest"
    ):
        """
        Update initial condition parameters using a time-indexed dataframe.

        Parameters
        ----------
        data : pandas.DataFrame

        model_date_start : datetime
            ForcastModel.date_start

        soil_temperature_columns : dict
            {depth_value: column_name}

        soil_moisture_columns : dict
            {depth_value: column_name}

        grndT0_column : str
        towT0_column : str

        temperature_data_unit : str
            Units used for temperature in the database

        model_timezone : str, optional
            Used if model_date_start timestamps are naive

        data_timezone : str, optional
            Used if dataframe timestamps are naive

        tolerance : "exact" or "nearest"
        """

        df = data.copy()

        # ----------------------------------------------------------
        # Normalize time axis
        # ----------------------------------------------------------

        if df.index.tz is None:
            if data_timezone is not None:
                df.index = df.index.tz_localize(data_timezone)
        else:
            # already timezone-aware
            pass

        model_time = pd.Timestamp(model_date_start)

        if model_time.tzinfo is None:
            if input_timezone is not None:
                model_time = model_time.tz_localize(model_timezone)

        # Convert both to same timezone
        if df.index.tz is not None:
            model_time = model_time.tz_convert(df.index.tz)

        # ----------------------------------------------------------
        # Find matching row
        # ----------------------------------------------------------

        if tolerance == "exact":
            df_match = df[df.index == model_time]

            if df_match.empty:
                raise ValueError(
                    "No exact timestamp match found for model_date_start."
                )

            row = df_match.iloc[0]

        elif tolerance == "nearest":
            idx = (df.index - model_time).abs().idxmin()
            row = df.loc[idx]

        else:
            raise ValueError("tolerance must be 'exact' or 'nearest'")

        # ----------------------------------------------------------
        # Validate mappings
        # ----------------------------------------------------------

        for col in soil_temperature_columns.values():
            if col not in df.columns:
                raise ValueError(f"Temperature column '{col}' not found.")

        for col in soil_moisture_columns.values():
            if col not in df.columns:
                raise ValueError(f"Moisture column '{col}' not found.")

        if grndT0_column not in df.columns:
            raise ValueError(f"Column '{grndT0_column}' not found.")

        if towT0_column not in df.columns:
            raise ValueError(f"Column '{towT0_column}' not found.")

        # Ensure depth consistency
        if set(soil_temperature_columns.keys()) != set(soil_moisture_columns.keys()):
            raise ValueError(
                "Temperature and moisture depth mappings must match."
            )

        # Sort depths numerically
        sorted_depths = sorted(soil_temperature_columns.keys(),reverse=True)

        # ----------------------------------------------------------
        # Update parameters
        # ----------------------------------------------------------

        self.zs = sorted_depths

        self.temps = [
            float(row[soil_temperature_columns[z]])
            for z in sorted_depths
        ]

        # TODO: CHECK UNITS FOR SOIL MOISTURE
        self.eta = [
            float(row[soil_moisture_columns[z]])*1.e-2
            for z in sorted_depths
        ]

        self.grndT0 = float(row[grndT0_column])
        self.towT0 = float(row[towT0_column])

        if temperature_data_unit in ("Celsius", "C"):
            self.temps = list(temperature_Celsius_to_Kelvin(np.array(self.temps)))
            self.grndT0 = temperature_Celsius_to_Kelvin(self.grndT0)
            self.towT0 = temperature_Celsius_to_Kelvin(self.towT0)
        elif temperature_data_unit is ("Kelvin", "K"):
            pass
        else:
            raise ValueError(f"temperature_data_unit ({temperature_data_unit}) not supported")

        self._validate_profiles()


    # ------------------------------------------------------------------
    # UPDATE FROM CSV
    # ------------------------------------------------------------------

    def update_from_csv(
        self,
        csv_path,
        model_date_start,
        time_column,
        csv_read_kwargs=None,
        **kwargs
    ):
        """
        Wrapper for CSV-based update.
        """

        csv_read_kwargs = csv_read_kwargs or {}

        df = pd.read_csv(csv_path,
                         parse_dates=[time_column],
                         **csv_read_kwargs)

        self.update_from_dataframe(
            data=df,
            model_date_start=model_date_start,
            **kwargs
        )

