This is the playground data source.

> Note: When mounting the playground folder into the docker container, make sure it has the correct permissions. This entrypoint script helped to solve the issue:
`bash -c "chmod 777 /var/lib/playground; ..."`

Here is a sample of a Python data source:

```python
from datetime import datetime, timedelta
from typing import Callable, List

from nexus_extensibility import (CatalogRegistration, NexusDataType,
                                 ReadDataHandler, ReadRequest, Representation,
                                 ResourceBuilder, ResourceCatalog,
                                 ResourceCatalogBuilder, SimpleDataSource)


class MyDataSource(SimpleDataSource):

    async def get_catalog_registrations(self, path: str) -> List[CatalogRegistration]:

        if path == "/":
            return [
                CatalogRegistration("MY_CATALOG", title="This is a sample catalog to show how the Playground works.")
            ]

        else:
            return []

    async def get_catalog(self, catalog_id: str) -> ResourceCatalog:

        # ensure we agree on the requested catalog
        if (catalog_id != "/MY_CATALOG"):
            raise Exception(f"Unknown catalog {catalog_id}.")

        representation = Representation(NexusDataType.FLOAT64, sample_period=timedelta(seconds=1))

        resource = ResourceBuilder(id="T1_squared") \
            .with_unit("°C²") \
            .with_description("This is the resource /SAMPLE/LOCAL/T1 squared.") \
            .with_groups(["my-group"]) \
            .add_representation(representation) \
            .build()

        # README (optional): the readme can be any markdown string
        with open("/var/lib/playground/README.md", "r") as readme_file:
            readme = readme_file.read()

        catalog = ResourceCatalogBuilder(catalog_id) \
            .with_readme(readme) \
            .add_resource(resource) \
            .build()

        return catalog

    async def read(
        self,
        begin: datetime,
        end: datetime,
        requests: list[ReadRequest],
        read_data: ReadDataHandler,
        report_progress: Callable[[float], None]) -> None:
        
        for request in requests:

            # ensure we agree on the requested catalog item
            if (request.catalog_item.resource.id != "T1_squared" and \
                request.catalog_item.representation.sample_period != timedelta(seconds=1)):
                raise Exception(f"Unknown catalog item {request.catalog_item.to_path()}.")

            # read /SAMPLE/LOCAL/T1 data from Nexus
            T1_data = await read_data("/SAMPLE/LOCAL/T1/1_s", begin, end)

            # cast target buffer to double
            data = request.data.cast('d')

            for i in range(0, len(T1_data)):

                # square /SAMPLE/LOCAL/T1 data
                data[i] = T1_data[i]**2

                # set status flag to 1 (= OK)
                request.status[i] = 1

                # report progress for every 10.000th element
                if (i % 10000 == 0):
                    report_progress(i / float(len(T1_data)))

```
