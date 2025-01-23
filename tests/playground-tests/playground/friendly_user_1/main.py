from datetime import datetime
from typing import Callable, List

from nexus_extensibility import (CatalogRegistration, ReadDataHandler,
                                 ReadRequest, ResourceCatalog,
                                 SimpleDataSource)


class MyDataSource(SimpleDataSource):
    
    async def get_catalog_registrations(self, path: str) -> List[CatalogRegistration]:

        if path == "/":
            return [
                CatalogRegistration("CATALOG_1", title=None) 
            ]

        else:
            return []

    async def enrich_catalog(self, catalog: ResourceCatalog) -> ResourceCatalog:
        return ResourceCatalog(catalog.id)

    async def read(
        self,
        begin: datetime, 
        end: datetime,
        requests: list[ReadRequest], 
        read_data: ReadDataHandler,
        report_progress: Callable[[float], None]) -> None:
        pass
