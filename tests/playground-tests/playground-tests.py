import math
from datetime import datetime
from gettext import Catalog

import pytest
from core import PlaygroundDataSource
from nexus_extensibility import (CatalogItem, DataSourceContext,
                                 ExtensibilityUtilities, ILogger, LogLevel,
                                 ReadRequest)


class _NullLogger(ILogger):
    def log(self, log_level: LogLevel, message: str):
        pass

@pytest.mark.asyncio
async def playground_test():

    # arrange
    data_source = PlaygroundDataSource()

    source_configuration = { 
        "mount-path": "/MY/PATH",
        "playground-folder": "tests/playground-tests/playground" 
    }

    logger = _NullLogger()
    context = DataSourceContext(None, None, source_configuration, None)

    begin = datetime(2020, 1, 1)
    end = datetime(2020, 1, 2)

    # act
    await data_source.set_context(context, logger)
    registrations = await data_source.get_catalog_registrations("/")
    catalog = await data_source.get_catalog(registrations[1].path)
    time_range = await data_source.get_time_range(registrations[1].path)
    availability = await data_source.get_availability(registrations[1].path, begin, end)

    resource = catalog.resources[0]
    representation = resource.representations[0]
    catalog_item = CatalogItem(catalog, resource, representation)
    (data, status) = ExtensibilityUtilities.create_buffers(catalog_item.representation, begin, end)
    request = ReadRequest(catalog_item, data, status)

    await data_source.read(
        begin=datetime(2020, 1, 1), 
        end=datetime(2020, 1, 1), 
        requests=[request],
        read_data=None,
        report_progress=None)

    # 
    assert len(registrations) == 2
    assert registrations[0].path == "/MY/PATH/FRIENDLY_USER_1/CATALOG_1"
    assert registrations[1].path == "/MY/PATH/FRIENDLY_USER_2/CATALOG_2"
    assert catalog.id == "/MY/PATH/FRIENDLY_USER_2/CATALOG_2"
    assert time_range == (datetime.min, datetime.max)
    assert math.isnan(availability)
