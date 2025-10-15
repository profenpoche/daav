import pytest
import pandas as pd
import tempfile
import os
import json
import csv
import yaml
import base64
import math
from unittest.mock import Mock, patch, mock_open, MagicMock
from datetime import datetime, timezone
from fastapi import Request, HTTPException

from app.utils.utils import convert_size, folder, generate_pandas_schema, slice_generator, decodeDictionary, verify_route_access
from app.models.interface.dataset_interface import Pagination, FileContentResponse
from app.models.interface.dataset_schema import PandasColumn, PandasSchema


class TestConvertSize:
    """Test cases for convert_size function"""
    
    def test_zero_size(self):
        """Test with zero size"""
        result = convert_size(0)
        assert result == "0B"
    
    def test_bytes(self):
        """Test bytes conversion"""
        result = convert_size(500)
        assert result == "500.0 B"
    
    def test_kilobytes(self):
        """Test kilobytes conversion"""
        result = convert_size(1024)
        assert result == "1.0 KB"
    
    def test_megabytes(self):
        """Test megabytes conversion"""
        result = convert_size(1024 * 1024)
        assert result == "1.0 MB"
    
    def test_gigabytes(self):
        """Test gigabytes conversion"""
        result = convert_size(1024 * 1024 * 1024)
        assert result == "1.0 GB"


class TestFolder:
    """Test cases for folder function"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory with test files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            json_file = os.path.join(temp_dir, "test.json")
            with open(json_file, 'w') as f:
                json.dump({"name": "test", "value": 123}, f)
            
            csv_file = os.path.join(temp_dir, "test.csv")
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['name', 'age'])
                writer.writerow(['John', '30'])
            
            txt_file = os.path.join(temp_dir, "test.txt")
            with open(txt_file, 'w') as f:
                f.write("Hello World")
            
            yaml_file = os.path.join(temp_dir, "test.yaml")
            with open(yaml_file, 'w') as f:
                yaml.dump({'config': {'debug': True, 'port': 8080}}, f)
            
            # Create subdirectory
            sub_dir = os.path.join(temp_dir, "subdir")
            os.makedirs(sub_dir)
            sub_file = os.path.join(sub_dir, "sub.txt")
            with open(sub_file, 'w') as f:
                f.write("Sub content")
            
            yield temp_dir
    
    @patch('magic.from_file')
    @patch('os.stat')
    def test_folder_without_pagination(self, mock_stat, mock_magic, temp_dir):
        """Test folder function without pagination"""
        # Mock file stats and mime types
        mock_stat.return_value = MagicMock()
        mock_stat.return_value.st_size = 1024
        mock_stat.return_value.st_ctime = 1640995200.0  # 2022-01-01 00:00:00
        mock_stat.return_value.st_mtime = 1640995200.0
        
        def mime_side_effect(path, **kwargs):  # Accept **kwargs to handle mime=True
            if path.endswith('.json'):
                return 'application/json'
            elif path.endswith('.csv'):
                return 'text/csv'
            elif path.endswith('.txt'):
                return 'text/plain'
            elif path.endswith('.yaml'):
                return 'application/x-yaml'
            return 'application/octet-stream'
        
        mock_magic.side_effect = mime_side_effect
        
        result = folder(temp_dir)
        
        assert isinstance(result, list)
        assert len(result) == 5  # 4 files in root + 1 in subdirectory
        
        # Check if all files are present
        file_names = [item['file'] for item in result]
        assert 'test.json' in file_names
        assert 'test.csv' in file_names
        assert 'test.txt' in file_names
        assert 'test.yaml' in file_names
        assert 'sub.txt' in file_names
    
    @patch('magic.from_file')
    @patch('os.stat')
    def test_folder_with_pagination(self, mock_stat, mock_magic, temp_dir):
        """Test folder function with pagination"""
        # Mock file stats and mime types
        mock_stat.return_value = MagicMock()
        mock_stat.return_value.st_size = 1024
        mock_stat.return_value.st_ctime = 1640995200.0
        mock_stat.return_value.st_mtime = 1640995200.0
        
        def mock_magic_side_effect(path, **kwargs):
            return 'text/plain'
        
        mock_magic.side_effect = mock_magic_side_effect
        
        pagination = Pagination(page=1, perPage=2)
        result = folder(temp_dir, pagination)
        
        assert isinstance(result, FileContentResponse)
        assert len(result.data) == 2
        assert result.total_rows == 5
        assert result.current_page == 1
        assert result.limit == 2
    
    @patch('magic.from_file')
    @patch('os.stat')
    def test_folder_json_content(self, mock_stat, mock_magic, temp_dir):
        """Test JSON file content parsing"""
        mock_stat.return_value = MagicMock()
        mock_stat.return_value.st_size = 1024
        mock_stat.return_value.st_ctime = 1640995200.0
        mock_stat.return_value.st_mtime = 1640995200.0
        
        def mock_magic_side_effect(path, **kwargs):
            return 'application/json'
        
        mock_magic.side_effect = mock_magic_side_effect
        
        result = folder(temp_dir)
        json_file = next(item for item in result if item['file'] == 'test.json')
        
        assert json_file['content'] == {"name": "test", "value": 123}
        assert json_file['mime_type'] == 'application/json'
    
    @patch('magic.from_file')
    @patch('os.stat')
    def test_folder_csv_content(self, mock_stat, mock_magic, temp_dir):
        """Test CSV file content parsing"""
        mock_stat.return_value = MagicMock()
        mock_stat.return_value.st_size = 1024
        mock_stat.return_value.st_ctime = 1640995200.0
        mock_stat.return_value.st_mtime = 1640995200.0
        mock_magic.return_value = 'text/csv'
        
        result = folder(temp_dir)
        csv_file = next(item for item in result if item['file'] == 'test.csv')
        
        assert isinstance(csv_file['content'], list)
        assert len(csv_file['content']) == 1  # Only data rows, not header
        assert csv_file['content'][0] == {'name': 'John', 'age': '30'}
    
    @patch('magic.from_file')
    @patch('os.stat')
    def test_folder_text_content(self, mock_stat, mock_magic, temp_dir):
        """Test text file content parsing"""
        mock_stat.return_value = MagicMock()
        mock_stat.return_value.st_size = 1024
        mock_stat.return_value.st_ctime = 1640995200.0
        mock_stat.return_value.st_mtime = 1640995200.0
        mock_magic.return_value = 'text/plain'
        
        result = folder(temp_dir)
        txt_file = next(item for item in result if item['file'] == 'test.txt')
        
        assert txt_file['content'] == "Hello World"
    
    @patch('magic.from_file')
    @patch('os.stat')
    def test_folder_yaml_content(self, mock_stat, mock_magic, temp_dir):
        """Test YAML file content parsing"""
        mock_stat.return_value = MagicMock()
        mock_stat.return_value.st_size = 1024
        mock_stat.return_value.st_ctime = 1640995200.0
        mock_stat.return_value.st_mtime = 1640995200.0
        mock_magic.return_value = 'application/x-yaml'
        
        result = folder(temp_dir)
        yaml_file = next(item for item in result if item['file'] == 'test.yaml')
        
        assert yaml_file['content'] == {'config': {'debug': True, 'port': 8080}}
    
    @patch('os.scandir')
    def test_folder_permission_error(self, mock_scandir):
        """Test folder function with permission error"""
        mock_scandir.side_effect = PermissionError("Access denied")
        
        result = folder("/nonexistent")
        assert result == []
    
    @patch('magic.from_file')
    def test_folder_media_file_too_large(self, mock_magic, temp_dir):
        """Test media file size limit"""
        # Create a large dummy file
        large_file = os.path.join(temp_dir, "large.jpg")
        # Create a file larger than 1000MB to trigger the size limit
        with open(large_file, 'wb') as f:
            f.write(b'0' * (1001 * 1024 * 1024))  # 1001MB file
        
        mock_magic.return_value = 'image/jpeg'
        
        result = folder(temp_dir)
        large_file_result = next(item for item in result if item['file'] == 'large.jpg')
        
        assert large_file_result['media'] is None


class TestGeneratePandasSchema:
    """Test cases for generate_pandas_schema function"""
    
    @pytest.fixture
    def sample_dataframe(self):
        """Sample DataFrame for testing"""
        return pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['John', 'Jane', 'Bob'],
            'age': [25, 30, 35],
            'active': [True, False, True]
        })
    
    @pytest.fixture
    def nested_dataframe(self):
        """DataFrame with nested structures"""
        return pd.DataFrame({
            'user': [
                {'name': 'John', 'email': 'john@test.com'},
                {'name': 'Jane', 'email': 'jane@test.com'}
            ],
            'metadata': [
                {'created': '2023-01-01', 'source': 'api'},
                {'created': '2023-01-02', 'source': 'web'}
            ]
        })
    
    def test_dataframe_schema_generation(self, sample_dataframe):
        """Test schema generation for DataFrame"""
        schema = generate_pandas_schema(sample_dataframe)
        
        assert isinstance(schema, PandasSchema)
        assert len(schema.root) == 4
        
        # Check column names
        column_names = [col.name for col in schema.root]
        assert 'id' in column_names
        assert 'name' in column_names
        assert 'age' in column_names
        assert 'active' in column_names
        
        # Check data types
        id_col = next(col for col in schema.root if col.name == 'id')
        assert id_col.dtype == 'int'
        assert id_col.count == 3
        assert not id_col.nullable
    
    def test_series_schema_generation(self):
        """Test schema generation for Series"""
        series = pd.Series([1, 2, 3, 4, 5], name='numbers')
        schema = generate_pandas_schema(series)
        
        assert isinstance(schema, PandasSchema)
        assert len(schema.root) == 1
        assert schema.root[0].name == "#array_item#"
        assert schema.root[0].dtype == 'int'
        assert schema.root[0].count == 5
    
    def test_empty_series_schema(self):
        """Test schema generation for empty Series"""
        empty_series = pd.Series([], dtype='object')
        schema = generate_pandas_schema(empty_series)
        
        assert isinstance(schema, PandasSchema)
        assert len(schema.root) == 0
    
    def test_dictionary_schema_generation(self):
        """Test schema generation for dictionary"""
        test_dict = {
            'name': 'John',
            'age': 30,
            'active': True,
            'metadata': {'created': '2023-01-01'}
        }
        
        schema = generate_pandas_schema(test_dict)
        
        assert isinstance(schema, PandasSchema)
        assert len(schema.root) == 4
        
        # Check nested structure
        metadata_col = next(col for col in schema.root if col.name == 'metadata')
        assert metadata_col.nested is not None
        assert len(metadata_col.nested) == 1
        assert metadata_col.nested[0].name == 'created'
    
    def test_series_with_null_values(self):
        """Test Series with null values"""
        series = pd.Series([1, None, 3, None, 5])
        schema = generate_pandas_schema(series)
        
        assert schema.root[0].nullable is True
        assert schema.root[0].count == 5
    
    def test_nested_dataframe_schema(self, nested_dataframe):
        """Test schema generation for DataFrame with nested data"""
        schema = generate_pandas_schema(nested_dataframe)
        
        assert len(schema.root) == 2
        
        # Check if nested structures are detected
        user_col = next(col for col in schema.root if col.name == 'user')
        assert user_col.nested is not None


class TestSliceGenerator:
    """Test cases for slice_generator function"""
    
    @pytest.fixture
    def large_dataframe(self):
        """Large DataFrame for testing"""
        return pd.DataFrame({
            'id': range(1000),
            'value': [f'value_{i}' for i in range(1000)]
        })
    
    def test_slice_generator_default_chunk(self, large_dataframe):
        """Test slice generator with default chunk size"""
        slices = list(slice_generator(large_dataframe))
        
        assert len(slices) == 1  # 1000 rows with default 1000 chunk size
        assert len(slices[0]) == 1000
    
    def test_slice_generator_custom_chunk(self, large_dataframe):
        """Test slice generator with custom chunk size"""
        slices = list(slice_generator(large_dataframe, chunk_size=250))
        
        assert len(slices) == 4  # 1000 rows with 250 chunk size
        for slice_df in slices:
            assert len(slice_df) == 250
    
    def test_slice_generator_small_dataframe(self):
        """Test slice generator with small DataFrame"""
        small_df = pd.DataFrame({'id': [1, 2, 3]})
        slices = list(slice_generator(small_df, chunk_size=10))
        
        assert len(slices) == 1
        assert len(slices[0]) == 3
    
    def test_slice_generator_empty_dataframe(self):
        """Test slice generator with empty DataFrame"""
        empty_df = pd.DataFrame()
        slices = list(slice_generator(empty_df))
        
        assert len(slices) == 0


class TestDecodeDictionary:
    """Test cases for decodeDictionary function"""
    
    def test_decode_simple_dictionary(self):
        """Test decoding simple dictionary"""
        test_dict = {
            'key1': 'value1',
            'key2': 'value2'
        }
        result = decodeDictionary(test_dict)
        
        assert result == test_dict
    
    def test_decode_bytes_values(self):
        """Test decoding dictionary with bytes values"""
        test_dict = {
            'key1': b'Hello',
            'key2': b'World'
        }
        result = decodeDictionary(test_dict)
        
        assert result['key1'] == 'Hello'
        assert result['key2'] == 'World'
    
    def test_decode_nested_dictionary(self):
        """Test decoding nested dictionary"""
        test_dict = {
            'level1': {
                'level2': {
                    'key': b'nested_value'
                }
            }
        }
        result = decodeDictionary(test_dict)
        
        assert result['level1']['level2']['key'] == 'nested_value'
    
    def test_decode_mixed_types(self):
        """Test decoding dictionary with mixed types"""
        test_dict = {
            'string': 'normal_string',
            'bytes': b'bytes_string',
            'number': 123,
            'nested': {
                'inner_bytes': b'inner_value'
            }
        }
        result = decodeDictionary(test_dict)
        
        assert result['string'] == 'normal_string'
        assert result['bytes'] == 'bytes_string'
        assert result['number'] == 123
        assert result['nested']['inner_bytes'] == 'inner_value'
    
    def test_decode_non_dictionary(self):
        """Test decoding non-dictionary input"""
        # Test with bytes
        result = decodeDictionary(b'test_bytes')
        assert result == 'test_bytes'
        
        # Test with string
        result = decodeDictionary('normal_string')
        assert result == 'normal_string'
        
        # Test with number
        result = decodeDictionary(123)
        assert result == 123


class TestRouteAccessControl:
    """Test suite for route access control"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_request = Mock(spec=Request)
        self.mock_request.client = Mock()
        self.mock_request.client.host = "192.168.1.1"
        self.mock_request.headers = {}
    
    @patch('app.utils.utils.settings')
    def test_domain_whitelist_with_origin_header(self, mock_settings):
        """Test access granted via domain whitelist using Origin header"""
        mock_settings.domain_whitelist = ["example.com", "api.example.com"]
        
        self.mock_request.headers = {"origin": "https://example.com"}
        
        result = verify_route_access(self.mock_request)
        assert result is True
    
    @patch('app.utils.utils.settings')
    def test_domain_whitelist_with_referer_header(self, mock_settings):
        """Test access granted via domain whitelist using Referer header"""
        mock_settings.domain_whitelist = ["example.com"]
        
        self.mock_request.headers = {"referer": "https://example.com/page"}
        
        result = verify_route_access(self.mock_request)
        assert result is True
    
    @patch('app.utils.utils.settings')
    def test_domain_whitelist_subdomain(self, mock_settings):
        """Test access granted for subdomain of whitelisted domain"""
        mock_settings.domain_whitelist = ["example.com"]
        
        self.mock_request.headers = {"origin": "https://api.example.com"}
        
        result = verify_route_access(self.mock_request)
        assert result is True
    
    @patch('app.utils.utils.settings')
    def test_domain_not_in_whitelist_no_api_keys(self, mock_settings):
        """Test access denied when domain not in whitelist and no api_keys"""
        mock_settings.domain_whitelist = ["example.com"]
        
        self.mock_request.headers = {"origin": "https://unauthorized.com"}
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request)
        
        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail
    
    @patch('app.utils.utils.settings')
    def test_bearer_token_valid_list(self, mock_settings):
        """Test access granted with valid Bearer token from list"""
        mock_settings.domain_whitelist = []
        
        api_keys = ["secret-token-123", "another-token"]
        authorization = "Bearer secret-token-123"
        
        result = verify_route_access(self.mock_request, authorization=authorization, api_keys=api_keys)
        assert result is True
    
    @patch('app.utils.utils.settings')
    def test_bearer_token_invalid_list(self, mock_settings):
        """Test access denied with invalid Bearer token"""
        mock_settings.domain_whitelist = []
        
        api_keys = ["secret-token-123"]
        authorization = "Bearer wrong-token"
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request, authorization=authorization, api_keys=api_keys)
        
        assert exc_info.value.status_code == 403
    
    @patch('app.utils.utils.settings')
    def test_bearer_token_missing_bearer_prefix(self, mock_settings):
        """Test access denied when Bearer prefix is missing"""
        mock_settings.domain_whitelist = []
        
        api_keys = ["secret-token-123"]
        authorization = "secret-token-123"  # Missing "Bearer "
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request, authorization=authorization, api_keys=api_keys)
        
        assert exc_info.value.status_code == 403
    
    @patch('app.utils.utils.settings')
    def test_custom_header_valid_dict(self, mock_settings):
        """Test access granted with valid custom header from dict"""
        mock_settings.domain_whitelist = []
        
        api_keys = [{"X-API-Key": "my-secret-key"}, {"X-Auth": "token123"}]
        self.mock_request.headers = {"X-API-Key": "my-secret-key"}
        
        result = verify_route_access(self.mock_request, api_keys=api_keys)
        assert result is True
    
    @patch('app.utils.utils.settings')
    def test_custom_header_invalid_value(self, mock_settings):
        """Test access denied with invalid custom header value"""
        mock_settings.domain_whitelist = []
        
        api_keys = [{"X-API-Key": "my-secret-key"}]
        self.mock_request.headers = {"X-API-Key": "wrong-value"}
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request, api_keys=api_keys)
        
        assert exc_info.value.status_code == 403
    
    @patch('app.utils.utils.settings')
    def test_custom_header_missing(self, mock_settings):
        """Test access denied when custom header is missing"""
        mock_settings.domain_whitelist = []
        
        api_keys = [{"X-API-Key": "my-secret-key"}]
        self.mock_request.headers = {}  # No headers
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request, api_keys=api_keys)
        
        assert exc_info.value.status_code == 403
    
    @patch('app.utils.utils.settings')
    def test_multiple_custom_headers_one_valid(self, mock_settings):
        """Test access granted with one of multiple custom headers"""
        mock_settings.domain_whitelist = []
        
        api_keys = [
            {"X-API-Key": "secret1"},
            {"X-Custom-Auth": "secret2"},
            {"X-Service-Token": "secret3"}
        ]
        
        self.mock_request.headers = {
            "X-API-Key": "wrong",
            "X-Custom-Auth": "secret2"  # This one is valid
        }
        
        result = verify_route_access(self.mock_request, api_keys=api_keys)
        assert result is True
    
    @patch('app.utils.utils.settings')
    def test_mixed_api_keys_bearer_and_custom(self, mock_settings):
        """Test access with mixed Bearer tokens and custom headers"""
        mock_settings.domain_whitelist = []
        
        # Mixed list: strings (Bearer) + dicts (custom headers)
        api_keys = [
            "bearer-token-123",
            {"X-API-Key": "custom-key-456"},
            "another-bearer-789",
            {"X-Service-Token": "service-xyz"}
        ]
        
        # Test with Bearer token
        authorization = "Bearer bearer-token-123"
        result = verify_route_access(self.mock_request, authorization=authorization, api_keys=api_keys)
        assert result is True
    
    @patch('app.utils.utils.settings')
    def test_mixed_api_keys_custom_header_success(self, mock_settings):
        """Test access with custom header in mixed list"""
        mock_settings.domain_whitelist = []
        
        api_keys = [
            "bearer-token-123",
            {"X-API-Key": "custom-key-456"}
        ]
        
        self.mock_request.headers = {"X-API-Key": "custom-key-456"}
        result = verify_route_access(self.mock_request, api_keys=api_keys)
        assert result is True
    
    @patch('app.utils.utils.settings')
    def test_priority_domain_over_token(self, mock_settings):
        """Test that domain whitelist is checked before tokens"""
        mock_settings.domain_whitelist = ["example.com"]
        
        self.mock_request.headers = {"origin": "https://example.com"}
        # Don't provide api_keys - should still pass via domain
        
        result = verify_route_access(self.mock_request)
        assert result is True
    
    @patch('app.utils.utils.settings')
    def test_no_whitelist_and_no_api_keys(self, mock_settings):
        """Test access denied when no whitelist and no api_keys"""
        mock_settings.domain_whitelist = []
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request)
        
        assert exc_info.value.status_code == 403
    
    @patch('app.utils.utils.settings')
    def test_domain_fails_but_token_succeeds(self, mock_settings):
        """Test access via token when domain not whitelisted"""
        mock_settings.domain_whitelist = ["other-domain.com"]
        
        self.mock_request.headers = {"origin": "https://example.com"}
        api_keys = ["valid-token"]
        authorization = "Bearer valid-token"
        
        result = verify_route_access(self.mock_request, authorization=authorization, api_keys=api_keys)
        assert result is True
    
    @patch('app.utils.utils.settings')
    def test_empty_authorization_header_with_list(self, mock_settings):
        """Test access denied with empty authorization header"""
        mock_settings.domain_whitelist = []
        
        api_keys = ["valid-token"]
        authorization = ""
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request, authorization=authorization, api_keys=api_keys)
        
        assert exc_info.value.status_code == 403
    
    @patch('app.utils.utils.settings')
    def test_bearer_token_with_extra_spaces(self, mock_settings):
        """Test Bearer token validation handles extra spaces"""
        mock_settings.domain_whitelist = []
        
        api_keys = ["secret-token"]
        authorization = "Bearer   secret-token   "  # Extra spaces
        
        result = verify_route_access(self.mock_request, authorization=authorization, api_keys=api_keys)
        assert result is True
    
    @patch('app.utils.utils.settings')
    def test_request_without_client(self, mock_settings):
        """Test handling when request.client is None"""
        mock_settings.domain_whitelist = []
        
        self.mock_request.client = None
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request)
        
        assert exc_info.value.status_code == 403
    
    @patch('app.utils.utils.settings')
    def test_whitelist_only_no_origin(self, mock_settings):
        """Test access denied with whitelist but no origin header"""
        mock_settings.domain_whitelist = ["example.com"]
        
        self.mock_request.headers = {}  # No origin or referer
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request)
        
        assert exc_info.value.status_code == 403
    
    @patch('app.utils.utils.settings')
    def test_api_keys_none_explicit(self, mock_settings):
        """Test with api_keys=None explicitly passed"""
        mock_settings.domain_whitelist = []
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request, api_keys=None)
        
        assert exc_info.value.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__])