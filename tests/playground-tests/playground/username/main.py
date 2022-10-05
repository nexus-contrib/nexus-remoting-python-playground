from datetime import datetime
from typing import Awaitable, Callable, List

from nexus_extensibility import (CatalogRegistration, ReadDataHandler,
                                 ReadRequest, ResourceCatalog,
                                 SimpleDataSource)


class PlaygroundDataSource(SimpleDataSource):
    
    def get_catalog_registrations(self, path: str) -> Awaitable[List[CatalogRegistration]]:
        raise Exception()

    def get_catalog(self, catalog_id: str) -> Awaitable[ResourceCatalog]:
        raise Exception()

    def read(
        self,
        begin: datetime, 
        end: datetime,
        requests: list[ReadRequest], 
        read_data: ReadDataHandler,
        report_progress: Callable[[float], None]) -> Awaitable[None]:
        raise Exception()
