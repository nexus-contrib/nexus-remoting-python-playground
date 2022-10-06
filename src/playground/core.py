import dataclasses
from gettext import Catalog
import inspect
import sys
from datetime import datetime
from typing import Awaitable, Callable, Dict, List, Tuple, cast
from zoneinfo import available_timezones

from nexus_extensibility import (CatalogRegistration, DataSourceContext,
                                 IDataSource, ILogger, LogLevel,
                                 ReadDataHandler, ReadRequest, ResourceCatalog)

from utils import load_extensions


class PlaygroundDataSource(IDataSource):

    _mount_path: str
    _data_source_map: Dict[IDataSource, str]
    _logger: ILogger

    async def set_context(self, context: DataSourceContext, logger: ILogger) -> None:

        self._logger = logger

        # mount path
        if context.source_configuration is not None and "mount-path" in context.source_configuration:
            self._mount_path = cast(str, context.source_configuration["mount-path"])

        else:
            raise Exception("The mount-path property is not set.")

        # load modules
        self._data_source_map = {}

        if context.source_configuration is not None and "playground-folder" in context.source_configuration:

            playground_folder = cast(str, context.source_configuration["playground-folder"])

            if not playground_folder in sys.path:
                sys.path.append(playground_folder)

            extensions = load_extensions(playground_folder, logger)

            filtered_data_source_types = (data_source_type for data_source_type in extensions \
                if issubclass(data_source_type, IDataSource) and not inspect.isabstract(data_source_type))

            for data_source_type in filtered_data_source_types:
                data_source = data_source_type()
                user_name = data_source.__module__.split('.')[0].upper()
                base_path = f"{self._mount_path}/{user_name}"

                self._data_source_map[data_source] = base_path

        else:
            raise Exception("The playground-folder property is not set.")

        # invoke modules
        for data_source in self._data_source_map:
            await data_source.set_context(context, logger)

    async def get_catalog_registrations(self, path: str) -> List[CatalogRegistration]:

        if path == "/":
            path = self._mount_path + "/"

        registrations = []

        for (data_source, base_path) in self._data_source_map.items():

            try:
                original_path = self._get_original_catalog_id(path)

                for registration in await data_source.get_catalog_registrations(original_path):

                    if registration.path.startswith("/"):
                        registration = dataclasses.replace(registration, path = f"{base_path}{registration.path}")

                    else:
                        registration = dataclasses.replace(registration, path = f"{base_path}{original_path}{registration.path}")

                    registrations.append(registration)

            except Exception as ex:
                self._logger.log(LogLevel.Debug, f"Unable to get catalog registrations from data source {data_source}. Reason: {str(ex)}")

        return registrations

    async def get_catalog(self, catalog_id: str) -> ResourceCatalog:

        data_source = next((current for (current, base_path) in self._data_source_map.items() if catalog_id.startswith(base_path)), None)

        if data_source is None:
            raise Exception(f"The data source for catalog {catalog_id} could not be found.")

        original_catalog_id = self._get_original_catalog_id(catalog_id)
        catalog = await data_source.get_catalog(original_catalog_id)

        if catalog.id != original_catalog_id:
            raise Exception("The returned catalog id does not match the requested catalog id.")

        catalog = dataclasses.replace(catalog, id = self._get_extended_catalog_id(catalog.id))

        return catalog

    async def get_time_range(self, catalog_id: str) -> Tuple[datetime, datetime]:

        data_source = next((current for (current, base_path) in self._data_source_map.items() if catalog_id.startswith(base_path)), None)

        if data_source is None:
            raise Exception(f"The data source for catalog {catalog_id} could not be found.")

        original_catalog_id = self._get_original_catalog_id(catalog_id)
        time_range = await data_source.get_time_range(original_catalog_id)

        return time_range

    async def get_availability(self, catalog_id: str, begin: datetime, end: datetime) -> float:
        
        data_source = next((current for (current, base_path) in self._data_source_map.items() if catalog_id.startswith(base_path)), None)

        if data_source is None:
            raise Exception(f"The data source for catalog {catalog_id} could not be found.")

        original_catalog_id = self._get_original_catalog_id(catalog_id)
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
            data_source = next((current for (current, base_path) in self._data_source_map.items() if catalog_id.startswith(base_path)), None)

            if data_source is None:
                raise Exception(f"The data source for catalog {catalog_id} could not be found.")

            original_catalog_id = self._get_original_catalog_id(catalog_id)
            original_catalog = dataclasses.replace(request.catalog_item.catalog, id=original_catalog_id)
            original_catalog_item = dataclasses.replace(request.catalog_item, catalog=original_catalog)
            original_request = dataclasses.replace(request, catalog_item=original_catalog_item)

            await data_source.read(begin, end, [original_request], read_data, report_progress)

    def _get_extended_catalog_id(self, catalog_id: str) -> str:
        return self._mount_path + catalog_id

    def _get_original_catalog_id(self, catalog_id: str) -> str:
        return catalog_id[len(self._mount_path + catalog_id):]
