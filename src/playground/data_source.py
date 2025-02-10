import dataclasses
import inspect
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

import numpy  # required to make it available in user defined playground extensions
import pandas  # required to make it available in user defined playground extensions
from nexus_extensibility import (CatalogRegistration, CatalogTimeRange,
                                 DataSourceContext, IDataSource, ILogger,
                                 LogLevel, ReadDataHandler, ReadRequest,
                                 ResourceCatalog)

from .utils import load_extensions


@dataclass(frozen=True)
class PlaygroundSettings():
    mount_path: str

class Playground(IDataSource[PlaygroundSettings]):

    _data_source_map: dict[IDataSource, str]
    _logger: ILogger

    async def set_context(self, context: DataSourceContext[PlaygroundSettings], logger: ILogger) -> None:

        self._logger = logger

        # load modules
        self._data_source_map = {}

        if (context.resource_locator is None or context.resource_locator.path is None):
            raise Exception(f"No resource locator provided.")

        if (context.resource_locator.scheme != "file"):
            raise Exception(f"Expected 'file' URI scheme, but got '{context.resource_locator.scheme}'.")

        playground_folder = context.resource_locator.path

        if not playground_folder in sys.path:
            sys.path.append(playground_folder)

        extensions = load_extensions(playground_folder, logger)

        filtered_data_source_types = (data_source_type for data_source_type in extensions \
            if issubclass(data_source_type, IDataSource) and not inspect.isabstract(data_source_type))

        mount_path = context.source_configuration.mount_path

        for data_source_type in filtered_data_source_types:
            data_source = data_source_type()
            user_name = data_source.__module__.split('.')[0].upper()
            base_path = f"{mount_path}/{user_name}"

            self._data_source_map[data_source] = base_path

        # invoke modules
        for data_source in self._data_source_map:
            await data_source.set_context(context, logger)

    async def get_catalog_registrations(self, path: str) -> list[CatalogRegistration]:

        registrations = []

        for (data_source, base_path) in self._data_source_map.items():

            actual_path = path

            if actual_path == "/":
                actual_path = base_path + "/"

            try:
                original_path = self._get_original_catalog_id(base_path, actual_path)

                for registration in await data_source.get_catalog_registrations(original_path):

                    if registration.path.startswith("/"):
                        registration = dataclasses.replace(registration, path = f"{base_path}{registration.path}")

                    else:
                        registration = dataclasses.replace(registration, path = f"{base_path}{original_path}{registration.path}")

                    registrations.append(registration)

            except Exception as ex:
                self._logger.log(LogLevel.Debug, f"Unable to get catalog registrations from data source {data_source}. Reason: {str(ex)}")

        return registrations

    async def enrich_catalog(self, catalog: ResourceCatalog) -> ResourceCatalog:

        # TODO merge old and new catalogs (not yet possible)

        (data_source, base_path) = next(((current1, current2) for (current1, current2) in self._data_source_map.items() if catalog.id.startswith(current2)), [None])

        if data_source is None or base_path is None:
            raise Exception(f"The data source for catalog {catalog.id} could not be found.")

        original_catalog_id = self._get_original_catalog_id(base_path, catalog.id)
        catalog = await data_source.enrich_catalog(ResourceCatalog(original_catalog_id))

        if catalog.id != original_catalog_id:
            raise Exception("The returned catalog id does not match the requested catalog id.")

        catalog = dataclasses.replace(catalog, id = self._get_extended_catalog_id(base_path, catalog.id))

        return catalog

    async def get_time_range(self, catalog_id: str) -> CatalogTimeRange:

        (data_source, base_path) = next(((current1, current2) for (current1, current2) in self._data_source_map.items() if catalog_id.startswith(current2)), [None])

        if data_source is None or base_path is None:
            raise Exception(f"The data source for catalog {catalog_id} could not be found.")

        original_catalog_id = self._get_original_catalog_id(base_path, catalog_id)
        time_range = await data_source.get_time_range(original_catalog_id)

        return time_range

    async def get_availability(self, catalog_id: str, begin: datetime, end: datetime) -> float:
        
        (data_source, base_path) = next(((current1, current2) for (current1, current2) in self._data_source_map.items() if catalog_id.startswith(current2)), [None])

        if data_source is None or base_path is None:
            raise Exception(f"The data source for catalog {catalog_id} could not be found.")

        original_catalog_id = self._get_original_catalog_id(base_path, catalog_id)
        availability = await data_source.get_availability(original_catalog_id, begin, end)

        return availability

    async def read(
        self,
        begin: datetime, 
        end: datetime,
        requests: list[ReadRequest], 
        read_data: ReadDataHandler,
        report_progress: Callable[[float], None]) -> None:
        
        for request in requests:

            catalog_id = request.catalog_item.catalog.id
            (data_source, base_path) = next(((current1, current2) for (current1, current2) in self._data_source_map.items() if catalog_id.startswith(current2)), [None])

            if data_source is None or base_path is None:
                raise Exception(f"The data source for catalog {catalog_id} could not be found.")

            original_catalog_id = self._get_original_catalog_id(base_path, catalog_id)
            original_catalog = dataclasses.replace(request.catalog_item.catalog, id=original_catalog_id)
            original_catalog_item = dataclasses.replace(request.catalog_item, catalog=original_catalog)
            original_request = dataclasses.replace(request, catalog_item=original_catalog_item)

            await data_source.read(begin, end, [original_request], read_data, report_progress)

    def _get_extended_catalog_id(self, base_path: str, catalog_id: str) -> str:
        return base_path + catalog_id

    def _get_original_catalog_id(self, base_path: str, catalog_id: str) -> str:
        return catalog_id[len(base_path):]
