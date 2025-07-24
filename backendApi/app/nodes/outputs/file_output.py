import asyncio
import traceback
from typing import Optional, Any
import pandas as pd
import pyarrow.parquet as pq
from pydantic import ConfigDict
from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import FileDataset
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.outputs.output_node import OutputNode
from app.services.dataset_service import DatasetService
import os
import logging
from app.utils.utils import resolve_file_name

from app.utils.security import PathSecurityValidator
from app.config.settings import settings
from app.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)


class FileOutput(OutputNode):
    
    datasetService: Optional[DatasetService] = None
    workflowService: Optional[WorkflowService] = None

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new FileOutput instance.

        Args:
            id (str): Unique identifier for the node
            data (Any): Data associated with the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)
        self.datasetService = DatasetService()
        self.workflowService = WorkflowService() 

    async def process(self, sample=False) -> StatusNode:
        """Process the data and export it to a CSV file.

        Args:
            sample (bool): Flag to indicate if process on sample should be done. Defaults to False.

        Returns:
            StatusNode: The status of the node after processing.
        """
        try:
            dataset, delimiter, encoding, fileType, fileName, fileExist = await self._retrieveFileConfig()
            

            if dataset is not None and dataset.filePath:
                data_file_type = dataset.metadata.fileType
                if data_file_type != fileType:
                    self.statusMessage = f"Output type '{fileType}' does not match dataset type '{data_file_type}'"
                    raise ValueError("File type mismatch between dataset and output node")
                
            # Determine output file path
            if dataset is not None:
                output_file = PathSecurityValidator.validate_file_path(dataset.filePath)
            elif fileName:
                resolved_filename = resolve_file_name(fileName, fileType)
                output_file = os.path.join(settings.upload_dir, resolved_filename)
            else:
                raise ValueError("No output file specified")
            for input in self.inputs.values():
                data = input.get_node_data()
                if input.get_connected_node():
                    if isinstance(data, NodeDataPandasDf):
                        if sample:
                            df = data.dataExample
                        else:
                            df = data.data
                        if not isinstance(df, pd.DataFrame):
                            raise ValueError("Input data is not a pandas DataFrame")

                        print(f"Exporting data to {output_file}")
                        
                        if fileType == 'csv':
                            if fileExist == 'append' and os.path.exists(output_file):
                                df.to_csv(output_file, sep=delimiter, encoding=encoding, index=False, mode='a', header=False)
                            else:
                                df.to_csv(output_file, sep=delimiter, encoding=encoding, index=False)
                        elif fileType == 'json':
                            self._write_json_data(df, output_file, fileExist)
                        elif fileType == 'xml':
                            self._write_xml_data(df, output_file, encoding, fileExist)
                        elif fileType == 'parquet':
                            if fileExist == 'append':
                                # fileType == "append"
                                old_data = pd.read_parquet(output_file)
                                df = pd.concat([old_data, df], ignore_index=True)
                                df.to_parquet(output_file)
                            else:
                                df.to_parquet(output_file)
                        else:
                            raise ValueError(f"Unsupported file type: {fileType}")
                        
                        print(f"Successfully exported to {output_file}")
                        
                        # Create and save new dataset AFTER the file has been created successfully
                        if dataset is None and fileName:
                            new_dataset = self._create_file_dataset(output_file, fileType, delimiter, encoding)
                            await self.datasetService.add_connection(new_dataset)
                            print(f"Created new dataset: {new_dataset.name}")
                            self.data['selectDataSource']["value"] =  new_dataset.id
                            self.data['selectDataSource']["list"].append({
                                "value": new_dataset.id,
                                "label": new_dataset.name
                            })
                            self.data['fileName']["value"] = None
                            self.data['fileName']["label"] = None
                        break
                        
                    elif isinstance(data, NodeDataParquet):
                        # Process in chunks to handle large files
                        chunkSize = 100
                        firstChunk = True
                        parquetFilePath = PathSecurityValidator.validate_file_path(data.data)
                        parquetFile = pq.ParquetFile(parquetFilePath)
                        
                        if fileType == 'csv':
                            mode = 'w' if fileExist == 'replace' or not os.path.exists(output_file) else 'a'
                            with open(output_file, mode, encoding=encoding) as csvfile:
                                for batch in parquetFile.iter_batches(batch_size=chunkSize):
                                    chunk_df = batch.to_pandas()
                                    
                                    if sample and firstChunk:
                                        chunk_df = chunk_df.head(20)
                                        chunk_df.to_csv(csvfile, sep=delimiter, index=False)
                                        break
                                    
                                    write_header = firstChunk and (fileExist == 'replace' or not os.path.exists(output_file))
                                    chunk_df.to_csv(csvfile, sep=delimiter, index=False, header=write_header)
                                    firstChunk = False
                        
                        elif fileType == 'json':
                            self._write_json_parquet_data(parquetFile, output_file, sample, chunkSize, fileExist)
                        
                        elif fileType == 'xml':
                            self._write_xml_parquet_data(parquetFile, output_file, encoding, sample, chunkSize, fileExist)
                        elif fileType == 'parquet':
                            if fileExist == 'append':
                                # fileType == "append"
                                old_data = pd.read_parquet(output_file)
                                new_data = parquetFile.read().to_pandas()
                                combined_data = pd.concat([old_data, new_data], ignore_index=True)
                                combined_data.to_parquet(output_file)
                            else:
                                parquetFile.write(output_file)
                        print(f"Successfully exported to {output_file}")
                        
                        # Create and save new dataset AFTER the file has been created successfully
                        if dataset is None and fileName:
                            new_dataset = self._create_file_dataset(output_file, fileType, delimiter, encoding)
                            await self.datasetService.add_connection(new_dataset)
                            print(f"Created new dataset: {new_dataset.name}")
                            self.data['selectDataSource']["value"] =  new_dataset.id
                            self.data['selectDataSource']["list"].append({
                                "value": new_dataset.id,
                                "label": new_dataset.name
                            })
                            self.data['fileName']["value"] = None
                            self.data['fileName']["label"] = None
                        break
                    else:
                        raise TypeError("Unsupported data type: {}".format(type(data)))
        except Exception as e:
            traceback.print_exc()
            self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
            self.statusMessage = e.__str__()
            return StatusNode.Error
        return StatusNode.Valid

    async def _retrieveFileConfig(self):
        """Retrieve the file configuration.

        Returns:
            tuple[FileDataset, str, str]: A tuple containing the dataset, delimiter, and encoding.

        Raises:
            ValueError: If no data source is selected.
        """
        dataset = None
        datasetId: str = None
        select_data_source = self.data.get('selectDataSource')
        if select_data_source and select_data_source.get('value'):
            datasetId = select_data_source['value']
        
        if datasetId:
            try:  
                dataset: FileDataset = await self.datasetService.get_dataset(datasetId)
            except Exception as e:
                dataset= None
        delimiter = self.data.get('delimiter')['value'] if self.data.get('delimiter') and self.data.get('delimiter').get('value') else ','
        encoding = self.data.get('encoding')['value'] if self.data.get('encoding') and self.data.get('encoding').get('value') else 'utf-8'
        fileType = self.data.get('fileType')['value'] if self.data.get('fileType') and self.data.get('fileType').get('value') else None
        fileName = self.data.get('fileName')['value'] if self.data.get('fileName') and self.data.get('fileName').get('value') else None
        
        if fileName:
            secure_file_name = PathSecurityValidator.validate_filename(fileName)
        else:
            secure_file_name = None
        
        fileExist = self.data.get('fileExist')['value'] if self.data.get('fileExist') and self.data.get('fileExist').get('value') else None
        
        if dataset is None and not fileName:
            raise ValueError("Either a data source must be selected or a filename must be provided")

        return dataset, delimiter, encoding , fileType, secure_file_name, fileExist

    def _write_json_data(self, df: pd.DataFrame, output_file: str, fileExist: str):
        """Write DataFrame to JSON file with proper array handling."""
        import json
        import os
        
        if fileExist == 'append' and os.path.exists(output_file):
            # Load existing data and append
            records = df.to_dict(orient='records')
            existing_records = []
            with open(output_file, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                    if isinstance(existing_data, list):
                        existing_records = existing_data
                except json.JSONDecodeError:
                    pass
        
            # Combine existing and new records
            all_records = existing_records + records
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_records, f, ensure_ascii=False, indent=2)
        else:
            # Replace or create new file using pandas to_json
            df.to_json(output_file, orient='records', force_ascii=False, indent=2)

    def _write_xml_data(self, df: pd.DataFrame, output_file: str, encoding: str, fileExist: str):
        """Write DataFrame to XML file with proper array handling."""
        import xml.etree.ElementTree as ET
        import os
        
        if fileExist == 'append' and os.path.exists(output_file):
            # Parse existing XML and append
            try:
                tree = ET.parse(output_file)
                root = tree.getroot()
            except ET.ParseError:
                root = ET.Element("data")
                tree = ET.ElementTree(root)
            
            # Convert DataFrame to XML elements and append
            for _, row in df.iterrows():
                item = ET.SubElement(root, "item")
                for col, value in row.items():
                    elem = ET.SubElement(item, str(col))
                    elem.text = str(value)
            
            tree.write(output_file, encoding=encoding, xml_declaration=True)
        else:
            # Replace or create new file
            df.to_xml(output_file, index=False, encoding=encoding)

    def _write_json_parquet_data(self, parquetFile, output_file: str, sample: bool, chunkSize: int, fileExist: str):
        """Write parquet data to JSON file in chunks with proper array handling."""
        import json
        import os
        
        all_records = []
        firstChunk = True
        
        # Read existing data if appending
        if fileExist == 'append' and os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                    if isinstance(existing_data, list):
                        all_records.extend(existing_data)
                except json.JSONDecodeError:
                    pass
        
        # Process chunks
        for batch in parquetFile.iter_batches(batch_size=chunkSize):
            chunk_df = batch.to_pandas()
            
            if sample and firstChunk:
                chunk_df = chunk_df.head(20)
            
            records = chunk_df.to_dict(orient='records')
            all_records.extend(records)
            
            if sample and firstChunk:
                break
            firstChunk = False
        
        # Write all data as JSON array
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_records, f, ensure_ascii=False, indent=2)

    def _write_xml_parquet_data(self, parquetFile, output_file: str, encoding: str, sample: bool, chunkSize: int, fileExist: str):
        """Write parquet data to XML file in chunks with proper array handling."""
        import xml.etree.ElementTree as ET
        import os
        
        # Initialize or load existing XML structure
        if fileExist == 'append' and os.path.exists(output_file):
            try:
                tree = ET.parse(output_file)
                root = tree.getroot()
            except ET.ParseError:
                root = ET.Element("data")
                tree = ET.ElementTree(root)
        else:
            root = ET.Element("data")
            tree = ET.ElementTree(root)
        
        firstChunk = True
        for batch in parquetFile.iter_batches(batch_size=chunkSize):
            chunk_df = batch.to_pandas()
            
            if sample and firstChunk:
                chunk_df = chunk_df.head(20)
            
            # Add chunk data to XML
            for _, row in chunk_df.iterrows():
                item = ET.SubElement(root, "item")
                for col, value in row.items():
                    elem = ET.SubElement(item, str(col))
                    elem.text = str(value)
            
            if sample and firstChunk:
                break
            firstChunk = False
        
        tree.write(output_file, encoding=encoding, xml_declaration=True)

    def _create_file_dataset(self, filePath: str, fileType: str, delimiter: str, encoding: str) -> FileDataset:
        """Create a new FileDataset for the output file.
        
        Args:
            filePath (str): The complete file path
            fileType (str): The type of file (csv, json, xml, parquet)
            delimiter (str): The delimiter for CSV files
            encoding (str): The file encoding
            
        Returns:
            FileDataset: A new FileDataset instance
        """
        # Generate a name for the dataset based on the filename
        dataset_name = os.path.splitext(os.path.basename(filePath))[0]
        
        # Create the FileDataset with the actual file path
        new_dataset = FileDataset(
            name=dataset_name,
            filePath=filePath,
            type="file",
            csvDelimiter=delimiter if fileType == 'csv' else None,
            encoding=encoding,
            inputType = "file",
            metadata= {
                "fileType": fileType,
            }
        )
        
        return new_dataset

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
