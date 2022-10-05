from datetime import datetime, timedelta
from typing import Callable, List

from nexus_extensibility import (CatalogRegistration, NexusDataType,
                                 ReadDataHandler, ReadRequest, Representation,
                                 Resource, ResourceCatalog, SimpleDataSource)


class MyDataSource(SimpleDataSource):
    
    async def get_catalog_registrations(self, path: str) -> List[CatalogRegistration]:

        if path == "/":
            return [
                CatalogRegistration("CATALOG_2", title=None) 
            ]

        else:
            return []

    async def get_catalog(self, catalog_id: str) -> ResourceCatalog:

        representation = Representation(NexusDataType.FLOAT64, timedelta(seconds=1))
        resource = Resource(id="resource_1", representations=[representation])
        
        return ResourceCatalog(catalog_id, resources=[resource])

    async def read(
        self,
        begin: datetime, 
        end: datetime,
        requests: list[ReadRequest], 
        read_data: ReadDataHandler,
        report_progress: Callable[[float], None]) -> None:
        pass
