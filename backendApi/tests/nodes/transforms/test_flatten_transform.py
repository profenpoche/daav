import pytest
import pandas as pd
import pyarrow as pq
import pyarrow.parquet as pq_file
from unittest.mock import Mock, patch
import tempfile
import os

from app.nodes.transforms.flatten_transform import FlattenTransform
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.enums.status_node import StatusNode


@pytest.fixture
def flatten_transform():
    """Fixture to create a FlattenTransform instance"""
    transform = FlattenTransform(id="test_flatten", data={})
    transform.inputs = {'datasource': Mock()}
    transform.outputs = {'out': Mock()}
    return transform

@pytest.fixture
def simple_json_data():
    """Simple JSON data with nested objects"""
    return [
        {
            "id": 1,
            "user": {
                "name": "John",
                "email": "john@email.com"
            },
            "metadata": {
                "created": "2023-01-01",
                "source": "api"
            }
        },
        {
            "id": 2,
            "user": {
                "name": "Jane",
                "email": "jane@email.com"
            },
            "metadata": {
                "created": "2023-01-02",
                "source": "web"
            }
        }
    ]

@pytest.fixture
def array_json_data():
    """JSON data with arrays of objects"""
    return [
        {
            "user_id": 123,
            "name": "Alice",
            "orders": [
                {"product": "laptop", "price": 1000, "date": "2023-01-01"},
                {"product": "mouse", "price": 25, "date": "2023-01-02"}
            ]
        },
        {
            "user_id": 456,
            "name": "Bob",
            "orders": [
                {"product": "keyboard", "price": 50, "date": "2023-01-03"}
            ]
        }
    ]


def test_simple_json_flattening(flatten_transform, simple_json_data):
    """Test simple JSON flattening"""
    # Setup
    df = pd.DataFrame(simple_json_data)
    mock_data = NodeDataPandasDf(
        data=df, 
        dataExample=pd.DataFrame(),
        nodeSchema=[],  # Liste vide au lieu de dictionnaire
        name="test_data"
    )
    flatten_transform.inputs['datasource'].get_node_data.return_value = mock_data
    flatten_transform._retreiveColumnsMapping = Mock(return_value=False)
    
    # Execute
    result = flatten_transform.process(sample=False)
    
    # Assert
    assert result == StatusNode.Valid
    flatten_transform.outputs['out'].set_node_data.assert_called_once()
    
    # Verify data structure
    call_args = flatten_transform.outputs['out'].set_node_data.call_args[0][0]
    result_df = call_args.data
    
    # Colonnes attendues avec underscore au lieu de point
    expected_columns = ['id', 'user_name', 'user_email', 'metadata_created', 'metadata_source']
    assert all(col in result_df.columns for col in expected_columns)
    assert len(result_df) == 2
    assert result_df.iloc[0]['user_name'] == 'John'
    assert result_df.iloc[1]['user_name'] == 'Jane'


def test_array_explosion(flatten_transform, array_json_data):
    """Test array explosion into rows"""
    # Setup
    df = pd.DataFrame(array_json_data)
    mock_data = NodeDataPandasDf(
        data=df,
        dataExample=pd.DataFrame(),
        nodeSchema=[],  # Liste vide
        name="test_array_data"
    )
    flatten_transform.inputs['datasource'].get_node_data.return_value = mock_data
    flatten_transform._retreiveColumnsMapping = Mock(return_value=False)
    
    # Execute
    result = flatten_transform.process(sample=False)
    
    # Assert
    assert result == StatusNode.Valid
    
    call_args = flatten_transform.outputs['out'].set_node_data.call_args[0][0]
    result_df = call_args.data
    
    # Verify that rows were duplicated for arrays
    assert len(result_df) == 3  # 2 orders for Alice + 1 order for Bob
    # Colonnes avec underscore
    assert 'orders_product' in result_df.columns
    assert 'orders_price' in result_df.columns
    
    # Verify data
    alice_orders = result_df[result_df['name'] == 'Alice']
    assert len(alice_orders) == 2
    assert set(alice_orders['orders_product']) == {'laptop', 'mouse'}


def test_sample_mode(flatten_transform, simple_json_data):
    """Test sample mode"""
    # Setup
    sample_df = pd.DataFrame(simple_json_data[:1])  # First element only
    mock_data = NodeDataPandasDf(
        data=pd.DataFrame(),
        dataExample=sample_df,
        nodeSchema=[],  # Liste vide
        name="test_sample_data"
    )
    flatten_transform.inputs['datasource'].get_node_data.return_value = mock_data
    flatten_transform._retreiveColumnsMapping = Mock(return_value=False)
    
    # Execute
    result = flatten_transform.process(sample=True)
    
    # Assert
    assert result == StatusNode.Valid
    
    call_args = flatten_transform.outputs['out'].set_node_data.call_args[0][0]
    result_df = call_args.dataExample
    
    assert len(result_df) == 1


def test_parquet_save_error(flatten_transform, simple_json_data):
    """Test error when parquet save is enabled"""
    # Setup
    df = pd.DataFrame(simple_json_data)
    mock_data = NodeDataPandasDf(
        data=df,
        dataExample=pd.DataFrame(),
        nodeSchema=[],  # Liste vide
        name="test_parquet_data"
    )
    flatten_transform.inputs['datasource'].get_node_data.return_value = mock_data
    flatten_transform._retreiveColumnsMapping = Mock(return_value=True)  # Parquet save enabled
    
    # Execute
    result = flatten_transform.process(sample=False)
    
    # Assert
    assert result == StatusNode.Error
    assert "Parquet output no supported" in flatten_transform.statusMessage


def test_invalid_input_format(flatten_transform):
    """Test with invalid input format"""
    # Setup
    flatten_transform.inputs['datasource'].get_node_data.return_value = "invalid_format"
    flatten_transform._retreiveColumnsMapping = Mock(return_value=False)
    
    # Execute
    result = flatten_transform.process(sample=False)
    
    # Assert
    assert result == StatusNode.Error
    assert "Input data is not a handled format" in flatten_transform.statusMessage


def test_empty_dataframe(flatten_transform):
    """Test with empty DataFrame"""
    # Setup
    mock_data = NodeDataPandasDf(
        data=pd.DataFrame(),
        dataExample=pd.DataFrame(),
        nodeSchema=[],  # Liste vide
        name="test_empty_data"
    )
    flatten_transform.inputs['datasource'].get_node_data.return_value = mock_data
    flatten_transform._retreiveColumnsMapping = Mock(return_value=False)
    
    # Execute
    result = flatten_transform.process(sample=False)
    
    # Assert
    assert result == StatusNode.Valid


@patch('traceback.print_exc')
def test_exception_handling(mock_print_exc, flatten_transform):
    """Test exception handling"""
    # Setup
    flatten_transform.inputs['datasource'].get_node_data.side_effect = Exception("Test error")
    flatten_transform._retreiveColumnsMapping = Mock(return_value=False)
    
    # Execute
    result = flatten_transform.process(sample=False)
    
    # Assert
    assert result == StatusNode.Error
    assert flatten_transform.statusMessage == "Test error"
    assert flatten_transform.errorStackTrace is not None
    mock_print_exc.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])