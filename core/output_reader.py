import pandas as pd
import xarray as xr
from pathlib import Path


class ForcastOutputReader:
    """
    Flexible FORCAsT output reader.

    Handles:
        - header only
        - header + units
        - metadata + header + units
        - optional level parsing
        - model-aware time axis construction
        - attaching model metadata to xarray Dataset
    """

    def __init__(
        self,
        filepath,
        model=None,
        header_line=0,
        units_line=None,
        metadata_line=None,
        time_column="Time",
        level_column=None,
        delimiter=r"\s+",
        time_unit="s"
    ):
        """
        Parameters
        ----------
        filepath : str or Path
        model : ForcastModel (optional)
            Used to construct time axis and attach metadata
        header_line : int
            Line index containing column names
        units_line : int or None
            Line index containing units
        metadata_line : int or None
            Line index containing metadata
        time_column : int or string
            Index or name of time column
        level_column : int, string, or None
            Index or name of the level column
        delimiter : str or None
            Passed to pandas.read_csv
        time_unit : str
            Unit of time in file ("s", "h", etc.)
        """

        self.filepath = Path(filepath)
        self.model = model
        self.header_line = header_line
        self.units_line = units_line
        self.metadata_line = metadata_line
        self.time_column = time_column
        self.level_column = level_column
        self.delimiter = delimiter
        self.time_unit = time_unit

    # --------------------------------------------------
    # HEADER PARSING
    # --------------------------------------------------

    def _parse_header(self):
        with open(self.filepath, "r") as f:
            # Only read the first three lines
            lines = [next(f) for _ in range(3)]

        header = lines[self.header_line].strip().split()
        units = None
        metadata = None

        if self.units_line is not None:
            units = lines[self.units_line].strip().split()

        if self.metadata_line is not None:
            metadata = lines[self.metadata_line].strip()

        return header, units, metadata

    # --------------------------------------------------
    # TIME CONSTRUCTION
    # --------------------------------------------------

    def _construct_time(self, raw_time):
        """
        Convert raw time column into datetime using model metadata.
        """

        if self.model is None:
            return raw_time

        if not hasattr(self.model, "model_start"):
            return raw_time

        start = pd.to_datetime(self.model.model_start)

        return start + pd.to_timedelta(raw_time, unit=self.time_unit)

    # --------------------------------------------------
    # MAIN READER
    # --------------------------------------------------

    def to_xarray(self):

        header, units, metadata = self._parse_header()

        # Determine first data row safely
        header_indices = [
            i for i in [
                self.header_line,
                self.units_line,
                self.metadata_line
            ] if i is not None
        ]

        first_data_row = max(header_indices) + 1

        df = pd.read_csv(
            self.filepath,
            skiprows=first_data_row,
            names=header,
            sep=self.delimiter,
            engine="python"
        )

        # --------------------------------------------------
        # Identify columns
        # --------------------------------------------------

        time_raw = df[self.time_column]

        # Convert time using model metadata
        time = self._construct_time(time_raw)

        df = df.drop(columns=[self.time_column])

        dataset = xr.Dataset()

        # --------------------------------------------------
        # CASE 1: No vertical level column
        # --------------------------------------------------

        if self.level_column is None:

            dataset.coords["time"] = time

            for col in df.columns:
                dataset[col] = xr.DataArray(
                    df[col].values,
                    dims=("time",),
                    coords={"time": time}
                )

        # --------------------------------------------------
        # CASE 2: Long format with time + level column
        # --------------------------------------------------

        else:

            level_values = df[self.level_column]
            df = df.drop(columns=[self.level_column])

            # Unique sorted coordinates
            unique_times = sorted(pd.unique(time))
            unique_levels = sorted(pd.unique(level_values))

            dataset.coords["time"] = unique_times
            dataset.coords["level"] = unique_levels

            for var in df.columns:

                # Build pivot table
                pivot = pd.DataFrame({
                    "time": time,
                    "level": level_values,
                    "value": df[var]
                })

                pivoted = pivot.pivot(
                    index="time",
                    columns="level",
                    values="value"
                )

                # Ensure correct order
                pivoted = pivoted.reindex(
                    index=unique_times,
                    columns=unique_levels
                )

                dataset[var] = xr.DataArray(
                    pivoted.values,
                    dims=("time", "level"),
                    coords={
                        "time": unique_times,
                        "level": unique_levels
                    }
                )

        # --------------------------------------------------
        # Attach units
        # --------------------------------------------------

        if units is not None:
            for name, unit in zip(header, units):
                if name in dataset:
                    dataset[name].attrs["units"] = unit

        # --------------------------------------------------
        # Attach metadata
        # --------------------------------------------------

        if metadata is not None:
            dataset.attrs["file_metadata"] = metadata

        if self.model is not None:
            dataset.attrs.update({
                "model": "FORCAsT",
                "date_start": str(self.model.model_start)
                if hasattr(self.model, "model_start") else None
            })

        return dataset

