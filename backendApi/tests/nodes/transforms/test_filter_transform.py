import logging
import os
import tempfile
import pandas as pd
import pyarrow.parquet as pq
import pytest
from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.transforms.filter_transform import FilterTransform
from unittest.mock import MagicMock, Mock, patch
import pyarrow as pa

logger = logging.getLogger(__name__)

@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 40, 45],
        'city': ['Paris', 'London', 'New York', 'Tokyo', 'Berlin'],
        'salary': [50000, 60000, 70000, 80000, 90000]
    })

@pytest.fixture
def filter_transform():
    #create a filter transform with basic configuration
    data = {
        'dataSource': 'datasource',
        'filterRules': {
            'condition': 'AND',
            'rules': [
                {
                    'field': 'age',
                    'operator': '=',
                    'value': 30
                }
            ],
        },
        'parquetSave': {'value': False}
    }
    filter_transform = FilterTransform(id="test-filter", data=data)
    filter_transform.inputs = {'datasource': Mock()}
    filter_transform.outputs = {'out': Mock()}
    return filter_transform


@pytest.fixture
def parquet_files(sample_dataframe):
    """Fixture pour créer un fichier parquet d'entrée temporaire"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.parquet', delete=False)
    temp_file.close()
    
    # Écrire les données dans le fichier parquet
    sample_dataframe.to_parquet(temp_file.name, index=False)
    
    yield temp_file.name
    
    # Nettoyer après le test
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)

@pytest.fixture
def input_node_data_parquet(parquet_files):
    """Fixture pour créer un NodeDataParquet d'entrée"""
    file_parquet = pq.ParquetFile(parquet_files)
    return NodeDataParquet(
        data = parquet_files,
        nodeSchema = parquet_files.schema if hasattr(parquet_files, 'schema') else None,
        name = "parquet_input"
    )


def test_filter_transform_basic(filter_transform, sample_dataframe):
    """"Test basic filtering functionality"""
    df = sample_dataframe
    mock_data = NodeDataPandasDf(
        data = df,
        dataExample = df.head(),
        nodeSchema = [],
        name = 'test_data'
    )
    
    filter_transform.inputs['datasource'].get_node_data.return_value = mock_data
    # Execute the transform
    result = filter_transform.process(sample=False)
    # Assert the result
    assert result == StatusNode.Valid

def test_filter_transform_with_sample(filter_transform, sample_dataframe):
    """Test filtering with sample=True"""
    df = sample_dataframe
    mock_data = NodeDataPandasDf(
        data = df,
        dataExample = df.head(),
        nodeSchema = [],
        name = 'test_data'
    )
    
    filter_transform.inputs['datasource'].get_node_data.return_value = mock_data
    # Execute the transform with sample=True
    result = filter_transform.process(sample=True)
    # Assert the result
    assert result == StatusNode.Valid

    
def test_filter_transform_no_data_after_filter(filter_transform, sample_dataframe):
    """Test filtering that results in no data"""
    df = sample_dataframe
    mock_data = NodeDataPandasDf(
        data = df,
        dataExample = df.head(),
        nodeSchema = [],
        name = 'test_data'
    )
    
    filter_transform.inputs['datasource'].get_node_data.return_value = mock_data
    # Update filter rules to filter out all data
    filter_transform.data['filterRules'] = {
        'condition': 'AND',
        'rules': [
            {
                'field': 'age',
                'operator': '=',
                'value': 100  # No one is 100 years old in the sample data
            }
        ],
    }
    # Execute the transform
    result = filter_transform.process(sample=False)
    # Assert the result
    assert result == StatusNode.Error
    assert "No data matches the filter conditions" in filter_transform.statusMessage
    
def test_filter_transform_node_parquet_data(filter_transform, parquet_files):
    """Test filtering when input is NodeDataParquet"""
    
    mock_data = Mock(spec=NodeDataParquet)
    mock_data.data = parquet_files
    mock_data.nodeSchema = None
    mock_data.name = "parquet_input"

    filter_transform.inputs['datasource'].get_node_data.return_value = mock_data
    
    result = filter_transform.process(sample=False)

    assert result == StatusNode.Valid

def test_filter_transform_invalid_input(filter_transform):
    """Test filtering with invalid input data"""
    filter_transform.inputs['datasource'].get_node_data.return_value = "invalid_data"
    
    result = filter_transform.process(sample=False)

    assert result == StatusNode.Error
    assert "Unkown data input" in filter_transform.statusMessage

def test_filter_transform_with_no_rules(filter_transform, sample_dataframe):
    """Test filtering with no rules provided"""
    mock_data = NodeDataPandasDf(
        data = sample_dataframe,
        dataExample = sample_dataframe.head(),
        nodeSchema = [],
        name = 'test_data'
    )
    
    filter_transform.inputs['datasource'].get_node_data.return_value = mock_data
    # Remove filter rules
    filter_transform.data['filterRules'] = {}
    
    result = filter_transform.process(sample=False)

    assert result == StatusNode.Error
    assert "Input required" in filter_transform.statusMessage

@patch('app.nodes.transforms.filter_transform.NodeDataParquet')
@patch('app.nodes.transforms.filter_transform.pq.ParquetFile')
@patch('app.nodes.transforms.filter_transform.os.path.getsize')
@patch('app.nodes.transforms.filter_transform.duckdb.connect')
def test_filter_transform_if_parquet_process(mock_duckdb_connect, mock_getsize, mock_parquet_file, mock_node_data_parquet, filter_transform, sample_dataframe):
    """Test filtering with parquet processing mode"""
    
    # Configuration du transform pour utiliser parquet
    filter_transform.data['parquetSave'] = {'value': True}
    
    # Mock des données d'entrée
    mock_data = NodeDataPandasDf(
        data=sample_dataframe,
        dataExample=sample_dataframe.head(),
        nodeSchema=[],
        name='test_data'
    )
    filter_transform.inputs['datasource'].get_node_data.return_value = mock_data
    
    # Mock de la connexion DuckDB
    mock_conn = MagicMock()
    mock_duckdb_connect.return_value = mock_conn
    
    # Mock que le fichier parquet généré a une taille > 0 (pas vide)
    mock_getsize.return_value = 1000  # fichier non vide
    
    # Mock ParquetFile pour la lecture du résultat
    mock_file = Mock()
    mock_file.schema = pa.Schema.from_pandas(sample_dataframe)
    mock_parquet_file.return_value = mock_file
    
    # Mock NodeDataParquet creation
    mock_node_data_instance = Mock()
    mock_node_data_parquet.return_value = mock_node_data_instance
    
    # Exécution du test
    result = filter_transform.process(sample=False)
    
    # Vérifications
    assert result == StatusNode.Valid
    
    # Vérifier que DuckDB connect a été appelé
    mock_duckdb_connect.assert_called()
    
    # Vérifier que register et execute ont été appelés sur la connexion
    mock_conn.register.assert_called_with('data', sample_dataframe)
    mock_conn.execute.assert_called()
    mock_conn.close.assert_called()
    
    # Vérifier que la requête SQL COPY a été exécutée
    call_args = mock_conn.execute.call_args[0][0]  # Premier argument de execute()
    assert "COPY" in call_args
    assert "FORMAT PARQUET" in call_args
    assert "WHERE" in call_args
    
    # Vérifier que le fichier de sortie a été vérifié (pas vide)
    mock_getsize.assert_called()
    
    # Vérifier que ParquetFile a été utilisé pour lire le schéma
    mock_parquet_file.assert_called()
    
    # Vérifier que NodeDataParquet a été créé
    mock_node_data_parquet.assert_called()


@patch('app.nodes.transforms.filter_transform.os.path.getsize')
@patch('app.nodes.transforms.filter_transform.duckdb.connect')
def test_filter_transform_parquet_empty_result(mock_duckdb_connect, mock_getsize, filter_transform, sample_dataframe):
    """Test filtering with parquet mode when result is empty"""
    
    # Configuration
    filter_transform.data['parquetSave'] = {'value': True}
    
    # Mock des données d'entrée
    mock_data = NodeDataPandasDf(
        data=sample_dataframe,
        dataExample=sample_dataframe.head(),
        nodeSchema=[],
        name='test_data'
    )
    filter_transform.inputs['datasource'].get_node_data.return_value = mock_data
    
    # Mock de la connexion DuckDB
    mock_conn = MagicMock()
    mock_duckdb_connect.return_value = mock_conn
    
    # Mock que le fichier parquet généré est vide (taille = 0)
    mock_getsize.return_value = 0
    
    # Exécution
    result = filter_transform.process(sample=False)
    
    # Vérifications
    assert result == StatusNode.Error
    assert "No data matches the filter conditions" in filter_transform.statusMessage

