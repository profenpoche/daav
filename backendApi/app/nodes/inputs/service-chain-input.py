import asyncio
import pyarrow.parquet as pq
from typing import List, Optional, Any
import pandas as pd
import traceback
from pydantic import ConfigDict
from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import PTXDataset
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.models.interface.pdc_chain_interface import PdcChainRequestData
from app.nodes.inputs.input_node import InputNode
from app.services.dataset_service import DatasetService
from app.utils.utils import generate_pandas_schema
from sqlalchemy import create_engine
import pyarrow as pa
from pyarrow.parquet import ParquetSchema


class ServiceChainInput(InputNode):
    """
    DataPdcChainBlock is responsible for retrieving data from a PDC Chain service  and processing it into a pandas DataFrame.
    """
    datasetService: Optional[DatasetService] = None

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new DataPdcChainBlock instance.

        Args:
            id (str): Unique identifier for the node
            data (Any): Data associated with the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)    
        self.datasetService = DatasetService()

    async def process(self, sample: bool = False) -> StatusNode:
        """Process the data from the MySQL database.

        Args:
            sample (bool): If True, retrieve a sample of the data (default is False).

        Returns:
            StatusNode: The status of the node after processing.
        """
        try:
            dataset,parquetSave,inputDataSourceExample = await self._retreiveDatabase()
            

            try:
                if(sample):
                    datasets = inputDataSourceExample

                else :
                    self.datasetService.pdcChainData
                    datasets = []
                    if ( isinstance(self.datasetService.pdcChainData,PdcChainRequestData)):
                        datasets.append(self.datasetService.pdcChainData.origin)
                        for additionalData in self.datasetService.pdcChainData.additionalData:
                            datasets.append(additionalData.data)
                    else :
                        datasets.append(self.datasetService.pdcChainData)
                chainHeaders = self.datasetService.pdcChainHeaders
                for index, dataset in enumerate(datasets):

                    df = pd.DataFrame(dataset)
                    schema = generate_pandas_schema(df)
                    if parquetSave and not sample:
                        parquetPath = f"{dataset.id}_{index}.parquet"                    
                        print(f"Saving data to {parquetPath}")
                        table = pa.Table.from_pandas(df)
                        parquet_writer = pq.ParquetWriter(parquetPath, table.schema)
                        parquet_writer.write_table(table)

                        if parquet_writer:
                            parquet_writer.close()

                        parquet_file = pq.ParquetFile(parquetPath)
                        schema = parquet_file.schema 

                    output = self.outputs.get(f"pdc-{index}")

                    if output.get_node_data():
                        # Update existing node data
                        # should resolve when output.get_node_data() is not the same type as the new node data
                        if parquetSave and not sample:
                            if isinstance(output.get_node_data, NodeDataParquet):
                                output.get_node_data().parquetPath = parquetPath
                                output.get_node_data().nodeSchema = schema
                            else:
                                raise ValueError("Output node data is not of type NodeDataParquet")

                        else:
                            if isinstance(output.get_node_data, NodeDataPandasDf):
                                output.get_node_data().nodeSchema = schema
                                if sample:
                                    output.get_node_data().dataExample = df
                                else:
                                    output.get_node_data().data = df
                            else:
                                raise ValueError("Output node data is not of type NodeDataPandasDf")
                    else:
                        # Create new node data
                        if parquetSave:
                            if isinstance(schema, ParquetSchema):
                                node_data = NodeDataParquet(
                                    type = 'parquet',
                                    data = parquetPath,
                                    nodeSchema=schema,
                                    name=f"{'Example' if sample else chainHeaders.x_ptx_service_chain_id} {index}"
                                )
                            else: 
                                raise ValueError("Schema is not a ParquetSchema")
                        else:
                            node_data = NodeDataPandasDf(
                                nodeSchema=schema,
                                name=f"{'Example' if sample else chainHeaders.x_ptx_service_chain_id} {index}"
                            )
                            if sample:
                                node_data.dataExample = df
                            else :
                                node_data.data = df    
                        output.set_node_data(node_data, self)
                return StatusNode.Valid
            except Exception as e:
                traceback.print_exc()
                self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
                self.statusMessage = e.__str__()
                return StatusNode.Error
        except ValueError as e:
            traceback.print_exc()
            self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
            self.statusMessage = e.__str__()
            return StatusNode.Error

    async def _retreiveDatabase(self) -> tuple[PTXDataset, bool, List]:
        """Retrieve the database configuration.

        Returns:
            tuple[MysqlDataset, str, str]: A tuple containing the dataset, database name, and table name.

        Raises:
            ValueError: If no data source, database, or table is selected.
        """
        datasetId : str 
        if self.data.get('selectDataSource') and self.data['selectDataSource']['value']:
            datasetId = self.data['selectDataSource']['value']
        else:
            raise ValueError("No data source selected")
        dataset : PTXDataset  = await self.datasetService.get_dataset(datasetId)
        if self.data.get('inputsDatasource'):
             inputDataSourceExample = self.data.get('inputsDatasource')
        else:
            raise ValueError("No datasource example")
        parquetSave = self.data['parquetSave']['value'] if self.data.get('parquetSave') else False
        return dataset, parquetSave , inputDataSourceExample


    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

