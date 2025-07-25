# Custom Node Development Guide

This guide explains how to create custom nodes for the DAAV platform backend.

## Overview

DAAV allows developers to extend the platform by creating custom nodes. The platform supports different types of nodes:
- **Input Nodes**: Read data from sources
- **Transform Nodes**: Process and transform data
- **Output Nodes**: Write data to destinations

All nodes inherit from a base `Node` class, with specialized classes like `InputNode`, `OutputNode`, and `TransformNode`.

## Configuration Access

All nodes access their configuration through the inherited `self.data` property:

```python
# Configuration is stored in self.data (inherited from base Node class)
config = self.data.get('config', {})
operation_type = config.get('operation_type', 'default')

# Example configuration structure
self.data = {
    'config': {
        'operation_type': 'filter',
        'filter_column': 'status',
        'filter_value': 'active'
    },
    'parquetSave': {'value': False}
}
```

## Backend Implementation

### Creating a Custom Transform Node

Create a new file in `app/nodes/transforms` directory, inheriting from `TransformNode` or child:

```python
# filepath: app/nodes/transforms/my_custom_transform.py
from typing import Optional, Any
import pandas as pd
from pydantic import ConfigDict

from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.transforms.transform_node import TransformNode
from app.utils.utils import generate_pandas_schema


class MyCustomTransform(TransformNode):
    """
    Custom transformation node.
    Only implements the required methods inherited from TransformNode.
    """
    
    def __init__(self, id: str, data: Any, revision: Optional[str] = None, 
                 status: Optional[StatusNode] = None):
        # Call parent constructor
        super().__init__(id=id, data=data, revision=revision, status=status)
        
        # Set default configuration if not provided
        if not self.data.get('config'):
            self.data['config'] = {
                'operation_type': 'filter',
                'threshold': 0.5,
                'enabled': True
            }

    def process(self, sample=False) -> StatusNode:
        """
        Main processing method - required by parent class.
        This is the ONLY method you must implement.
        """
        try:
            # Get node configuration from self.data (inherited property)
            config = self.data.get('config', {})
            operation_type = config.get('operation_type', 'filter')
            threshold = config.get('threshold', 0.5)
            enabled = config.get('enabled', True)
            
            if not enabled:
                # Skip processing if disabled
                return StatusNode.Valid
            
            # Process inputs (inherited from parent: self.inputs)
            for input_name, input_node in self.inputs.items():
                node_data = input_node.get_node_data()
                
                if isinstance(node_data, NodeDataPandasDf):
                    df = node_data.dataExample if sample else node_data.data
                    result_df = self._apply_transformation(df, config)
                    
                    # Create output data
                    output_data = NodeDataPandasDf(
                        nodeSchema=generate_pandas_schema(result_df),
                        data=result_df,
                        dataExample=result_df.head(20),
                        name="Custom Transform Result"
                    )
                    
                    # Set output (inherited method: self.outputs)
                    self.outputs.get('out').set_node_data(output_data, self)
            
            return StatusNode.Valid
            
        except Exception as e:
            # Use inherited properties for error handling
            import traceback
            traceback.print_exc()
            # On error you can fill the statusMessage.
            # This information is postponed to the front interface for the user
            self.statusMessage = str(e)
            self.status = StatusNode.Error
            # Also postponed for node with StatusNode.Error to the user Array of string or stacktrace
            self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
            return StatusNode.Error

    def _apply_transformation(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        """Helper method - not inherited, your custom logic."""
        result_df = df.copy()
        
        # Use config from self.data
        operation_type = config.get('operation_type', 'filter')
        
        if operation_type == "filter":
            filter_column = config.get('filter_column')
            filter_value = config.get('filter_value')
            
            if filter_column and filter_column in result_df.columns:
                result_df = result_df[result_df[filter_column] == filter_value]
        
        return result_df

    def _validate_configuration(self) -> bool:
        """Validate that all required configuration parameters are present."""
        config = self.data.get('config', {})
        
        required_params = ['operation_type', 'threshold']
        for param in required_params:
            if param not in config:
                self.statusMessage = f"Missing required parameter: {param}"
                return False
        
        # Validate parameter values
        if config.get('threshold') < 0 or config.get('threshold') > 1:
            self.statusMessage = "Threshold must be between 0 and 1"
            return False
        
        return True

    model_config = ConfigDict(arbitrary_types_allowed=True)
```

### Creating a Custom Input Node

Create a new file in `app/nodes/inputs/` directory, inheriting strictly from `InputNode`:

```python
# filepath: app/nodes/inputs/my_custom_input.py
from typing import Optional, Any
from pydantic import ConfigDict
import pandas as pd

from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf
from app.nodes.inputs.input_node import InputNode
from app.utils.utils import generate_pandas_schema


class MyCustomInput(InputNode):
    """
    Custom input node.
    Only implements the required methods inherited from InputNode.
    """
    
    def __init__(self, id: str, data: Any, revision: Optional[str] = None, 
                 status: Optional[StatusNode] = None):
        # Call parent constructor
        super().__init__(id=id, data=data, revision=revision, status=status)

    def process(self, sample: bool = False) -> StatusNode:
        """
        Main processing method - required by parent class.
        This is the ONLY method you must implement.
        """
        try:
            # Get configuration from self.data (inherited property)
            config = self.data.get('config', {})
            data_source = self.data.get('selectDataSource', {}).get('value')
            
            # Your custom data reading logic here
            df = self._read_custom_data(sample, config)
            
            # Create node data
            node_data = NodeDataPandasDf(
                nodeSchema=generate_pandas_schema(df),
                data=df,
                dataExample=df.head(20),
                name="Custom Input Data"
            )
            
            # Set data to outputs (inherited property: self.outputs)
            for key, output in self.outputs.items():
                output.set_node_data(node_data, self)
            
            return StatusNode.Valid
            
        except Exception as e:
            # Use inherited properties for error handling
            import traceback
            traceback.print_exc()
            self.errorStackTrace = traceback.format_exc()
            self.statusMessage = str(e)
            return StatusNode.Error

    def _read_custom_data(self, sample: bool, config: dict) -> pd.DataFrame:
        """Helper method - not inherited, your custom data reading logic."""
        # Use configuration from self.data
        source_type = config.get('source_type', 'default')
        
        # Example: read from your custom source
        if sample:
            return pd.DataFrame({'sample_col': [1, 2, 3]})
        else:
            return pd.DataFrame({'sample_col': range(100)})

    model_config = ConfigDict(arbitrary_types_allowed=True)
```

### Creating a Custom Output Node

Create a new file in `app/nodes/outputs/` directory, inheriting strictly from `OutputNode`:

```python
# filepath: app/nodes/outputs/my_custom_output.py
from typing import Optional, Any
from pydantic import ConfigDict

from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.outputs.output_node import OutputNode


class MyCustomOutput(OutputNode):
    """
    Custom output node.
    Only implements the required methods inherited from OutputNode.
    """
    
    def __init__(self, id: str, data: Any, revision: Optional[str] = None, 
                 status: Optional[StatusNode] = None):
        # Call parent constructor
        super().__init__(id=id, data=data, revision=revision, status=status)

    def process(self, sample=False) -> StatusNode:
        """
        Main processing method - required by parent class.
        This is the ONLY method you must implement.
        """
        try:
            # Get configuration from self.data (inherited property)
            config = self.data.get('config', {})
            destination = self.data.get('selectDataSource', {}).get('value')
            
            # Process all inputs (inherited property: self.inputs)
            for input_name, input_node in self.inputs.items():
                node_data = input_node.get_node_data()
                
                if isinstance(node_data, NodeDataPandasDf):
                    df = node_data.dataExample if sample else node_data.data
                    self._write_custom_data(df, sample, config)
                
                elif isinstance(node_data, NodeDataParquet):
                    # Handle parquet data
                    import pyarrow.parquet as pq
                    df = pd.read_parquet(node_data.data)
                    if sample:
                        df = df.head(20)
                    self._write_custom_data(df, sample, config)
            
            return StatusNode.Valid
            
        except Exception as e:
            # Use inherited properties for error handling
            import traceback
            traceback.print_exc()
            self.errorStackTrace = traceback.format_exc()
            self.statusMessage = str(e)
            return StatusNode.Error

    def _write_custom_data(self, df, sample: bool, config: dict):
        """Helper method - not inherited, your custom data writing logic."""
        # Use configuration from self.data
        output_format = config.get('output_format', 'csv')
        
        # Example: write to your custom destination
        print(f"Writing {len(df)} rows to custom destination (sample={sample}, format={output_format})")

    model_config = ConfigDict(arbitrary_types_allowed=True)
```

## Configuration Management

### Adding Custom Configuration Parameters

To add custom configuration parameters to your nodes, extend the `data()` method and handle them in the constructor:

```python
class MyCustomTransform(TransformNode):
    def __init__(self, id: str, data: Any, revision: Optional[str] = None, 
                 status: Optional[StatusNode] = None):
        super().__init__(id=id, data=data, revision=revision, status=status)
        
        # Set default configuration if not provided
        if not self.data.get('config'):
            self.data['config'] = {
                'operation_type': 'filter',
                'threshold': 0.5,
                'enabled': True
            }

    def process(self, sample=False) -> StatusNode:
        # Access configuration parameters
        config = self.data.get('config', {})
        operation_type = config.get('operation_type', 'filter')
        threshold = config.get('threshold', 0.5)
        enabled = config.get('enabled', True)
        
        if not enabled:
            # Skip processing if disabled
            return StatusNode.Valid
            
        # Use configuration in your processing logic
        # ... rest of implementation
```

### Configuration Validation

Implement configuration validation to ensure required parameters are present:

```python
def _validate_configuration(self) -> bool:
    """Validate that all required configuration parameters are present."""
    config = self.data.get('config', {})
    
    required_params = ['operation_type', 'threshold']
    for param in required_params:
        if param not in config:
            self.statusMessage = f"Missing required parameter: {param}"
            return False
    
    # Validate parameter values
    if config.get('threshold') < 0 or config.get('threshold') > 1:
        self.statusMessage = "Threshold must be between 0 and 1"
        return False
    
    return True
```

## Node Hierarchy

```
Node (app/nodes/node.py - base class)
├── InputNode (app/nodes/inputs/input_node.py)
│   ├── DataFileBlock (data_file_block.py) - File data input
│   ├── DataHuggingBlock (data_hugging_block.py) - Hugging Face data input
│   ├── DataLrsBlock (data_lrs_block.py) - LRS data input
│   ├── DataMongoBlock (data_mongo_block.py) - MongoDB data input
│   ├── DataMysqlBlock (data_mysql_block.py) - MySQL data input
│   ├── ServiceChainInput (service-chain-input.py) - Service Chain data input
│   └── ExampleInput (example_input.py) - Demo/example data generator
│
├── OutputNode (app/nodes/outputs/output_node.py)
│   ├── ApiOutput (api_output.py) - API endpoint output
│   ├── FileOutput (file_output.py) - File output
│   ├── MongoOutput (mongo_output.py) - MongoDB output
│   ├── MysqlOutput (mysql_output.py) - MySQL output
│   ├── PdcOutput (pdc_output.py) - PDC Chain output
│   ├── ServiceChainOutput (service_chain_output.py) - Service Chain output
│   └── ExampleOutput (example_ouput.py) - Demo/example output
│
└── TransformNode (app/nodes/transforms/transform_node.py)
    ├── MergeTransform (merge_transform.py) - Merge columns from multiple sources
    ├── FlattenTransform (flatten_transform.py) - Flatten nested JSON structures
    ├── FilterTransform (filter-transform.py) - Filter data based on conditions
    └── ExampleTransform (example_transform.py) - Demo/example transform
```

### Existing Input Nodes

#### File-based Inputs
- **DataFileBlock**: Read data from file datasets
- **ExampleInput**: Demo/example data generator

#### Database Inputs  
- **DataMongoBlock**: Read from MongoDB collections
- **DataMysqlBlock**: Read from MySQL databases

#### API/Service Inputs
- **DataApiBlock**: Read from API endpoints
- **DataElasticBlock**: Read from Elasticsearch
- **DataHuggingBlock**: Import from Hugging Face datasets
- **DataLrsBlock**: Read from LRS (Learning Record Store)
- **ServiceChainInput**: Fetch data from Service Chain services

### Existing Output Nodes

Your platform supports these output destinations:

#### File-based Outputs
- **FileOutput**: Write data to files

#### Database Outputs
- **MongoOutput**: Write to MongoDB collections  
- **MysqlOutput**: Write to MySQL databases

#### API/Service Outputs
- **ApiOutput**: Send data to API endpoints
- **PdcOutput**: Send data to PDC Chain service
- **ServiceChainOutput**: Send data to Service Chain services
- **ExampleOutput**: Demo/example output

### Existing Transform Nodes

Your platform includes these data transformation capabilities:

- **MergeTransform**: Combine columns from multiple data sources
- **FlattenTransform**: Flatten nested JSON/object structures into tabular format
- **FilterTransform**: Apply conditional filtering to datasets using SQL-like expressions
- **ExampleTransform**: Demo/example transformation

### Node Factory

Your platform uses a factory pattern (`node_factory.py`) to create and manage node instances dynamically using automatic class scanning.

## Integration with Existing Architecture

### Following Established Patterns

Your custom node should follow the same patterns as `MergeTransform` and `FlattenTransform`:

1. **Inherit from `TransformNode`**
2. **Implement `process()` method** with sample support
3. **Support both pandas and parquet modes**
4. **Use `generate_pandas_schema()` for output schemas**
5. **Handle errors with proper status and stack traces**
6. **Support the same input/output node data types**

### Configuration Structure

Follow the configuration pattern from existing transforms:

```python
# Example configuration structure (similar to MergeTransform)
data = {
    'config': {
        # Your custom configuration here
    },
    'parquetSave': {'value': False}  # Support parquet mode
}
```

### Input/Output Handling

Follow the established pattern for handling multiple inputs and setting outputs:

```python
# Input processing (from existing transforms)
for input_name, input_node in self.inputs.items():
    node_data = input_node.get_node_data()
    # Process based on type...

# Output setting (standard pattern)
self.outputs.get('out').set_node_data(output_data, self)
```

## Best Practices

### 1. Follow Existing Code Style
- Use the same imports and type hints as existing transforms
- Follow the same error handling patterns
- Use the same status management approach

### 2. Support Both Processing Modes
- Implement the `process()` method with support for both pandas DataFrame and parquet data
- Handle sample mode consistently using the `sample` parameter
- Support the same data types as existing transforms (NodeDataPandasDf, NodeDataParquet)

### 3. Comprehensive Testing
- Follow the existing test patterns in `tests/nodes/`
- Test all the same scenarios as existing transform tests
- Include fixtures following the established naming conventions

### 4. Documentation
- Document your transform's purpose and configuration
- Provide examples similar to existing transforms
- Include usage patterns

This guide focuses on the backend extension capabilities based on your existing codebase architecture. The frontend integration would depend on the Angular application structure, which would need to be analyzed separately.

# Frontend Implementation

## Overview

The DAAV frontend uses Rete.js with Angular for visual workflow editing. Nodes are implemented as TypeScript classes that extend base classes and are registered using the `@daavBlock` decorator.
This decorator takes an optional tag string parameter that can be used for filtering and ordering.
To allow automatic registration we need to import the code of the new implementation
by adding a link inside src/app/nodes/index.ts



## Frontend Node Architecture

```
src/app/nodes/
├── node-block.ts              # Base class for all nodes
├── input/
│   └── input-data-block.ts    # Base class for input nodes
├── output/
│   └── output-data-block.ts   # Base class for output nodes  
├── transform/
│   └── transform-block.ts     # Base class for transform nodes
├── inputs/                    # Concrete input node implementations
├── outputs/                   # Concrete output node implementations
├── transforms/                # Concrete transform node implementations
└── index.ts                   # Export all nodes
```

## Node Hierarchy

```
NodeBlock (base class)
├── InputDataBlock (for data sources)
│   ├── DataFileBlock
│   ├── DataApiBlock
│   ├── DataElasticBlock
│   ├── DataMongoBlock
│   ├── DataMysqlBlock
│   ├── DataLrsBlock
│   ├── ServiceChainInput
│   └── ExampleInput
├── OutputDataBlock (for data destinations)
│   ├── FileOutput
│   ├── MongoOutput
│   ├── MysqlOutput
│   ├── ApiOutput
│   ├── PdcOutput
│   ├── ServiceChainOutput
│   └── ExampleOutput
└── TransformBlock (for data transformations)
    ├── MergeTransform
    ├── FlattenTransform
    ├── FilterTransform
    └── ExampleTransform
```

## Creating Custom Frontend Nodes

### Step 1: Create a Custom Transform Node

Create a new file in `src/app/nodes/transforms/`:

```typescript
// filepath: src/app/nodes/transforms/my-custom-transform.ts
import { ClassicPreset } from "rete";
import { AreaPlugin } from "rete-area-plugin";
import { FlatObjectSocket } from "src/app/core/sockets/sockets";
import { Schemes, AreaExtra } from "src/app/core/workflow-editor";
import { StatusNode } from "src/app/enums/status-node";
import { daavBlock } from "../node-block";
import { Node } from "src/app/models/interfaces/node";
import { TransformBlock } from "../transform/transform-block";

@daavBlock('transform')
export class MyCustomTransform extends TransformBlock {
  override width = 350;
  override height = 200;

  constructor(
    label: string,
    area: AreaPlugin<Schemes, AreaExtra>,
    node?: Node
  ) {
    super(label, area, node);
    
    if (!node) {
      // Set initial status
      this.status = StatusNode.Incomplete;
      
      // Add inputs and outputs
      this.addInput(
        "input",
        new ClassicPreset.Input(new FlatObjectSocket(), "Input")
      );
      
      this.addOutput(
        "output", 
        new ClassicPreset.Output(new FlatObjectSocket(), "Output")
      );
    }
    
    // Update node status based on configuration
    this.validateConfiguration();
  }

  override data() {
    // Merge your custom data with parent data
    const customData = {
      config: {
        operation_type: this.getOperationType(),
        filter_column: this.getFilterColumn(),
        filter_value: this.getFilterValue()
      }
    };
    return { ...super.data(), ...customData };
  }

  private validateConfiguration() {
    // Implement your validation logic
    const config = this.data()?.config || {};
    
    if (config.operation_type && config.filter_column) {
      this.updateStatus(StatusNode.Complete);
    } else {
      this.updateStatus(StatusNode.Incomplete);
    }
  }

  private getOperationType(): string {
    // Get from your controls or default value
    return 'filter';
  }

  private getFilterColumn(): string {
    // Get from your controls or default value
    return '';
  }

  private getFilterValue(): string {
    // Get from your controls or default value
    return '';
  }

  override execute() {
    // This method is called when the play button is clicked
    console.log('Executing custom transform with config:', this.data().config);
  }
}
```

### Step 2: Create a Custom Input Node

Create a new file in `src/app/nodes/inputs/`:

```typescript
// filepath: src/app/nodes/inputs/my-custom-input.ts
import { ClassicPreset } from "rete";
import { AreaPlugin } from "rete-area-plugin";
import { FlatObjectSocket } from "src/app/core/sockets/sockets";
import { Schemes, AreaExtra } from "src/app/core/workflow-editor";
import { StatusNode } from "src/app/enums/status-node";
import { daavBlock } from "../node-block";
import { Node } from "src/app/models/interfaces/node";
import { InputDataBlock } from "../input/input-data-block";

@daavBlock('input')
export class MyCustomInput extends InputDataBlock {
  override width = 350;
  override height = 200;

  constructor(
    label: string,
    area: AreaPlugin<Schemes, AreaExtra>,
    node?: Node
  ) {
    super(label, area, node);
    
    if (!node) {
      // Set initial status
      this.status = StatusNode.Incomplete;
      
      // Add outputs (inputs only have outputs)
      this.addOutput(
        "output",
        new ClassicPreset.Output(new FlatObjectSocket(), "Data")
      );
    }
    
    // Add custom configuration if needed
    this.setupCustomConfiguration(node);
  }

  override getRevision(): string {
    // Return a revision string based on your configuration
    const data = this.data();
    return JSON.stringify({
      dataSource: data.selectDataSource?.value,
      config: data.config
    });
  }

  override data() {
    // Merge your custom data with parent data
    const customData = {
      config: {
        source_type: this.getSourceType(),
        connection_string: this.getConnectionString()
      }
    };
    return { ...super.data(), ...customData };
  }

  private setupCustomConfiguration(node?: Node) {
    // Add custom controls/widgets here if needed
    // Example: this.addCustomControl();
    
    this.validateConfiguration();
  }

  private validateConfiguration() {
    // Implement your validation logic
    const hasDataSource = this.data().selectDataSource?.value;
    
    if (hasDataSource) {
      this.updateStatus(StatusNode.Complete, "Data source configured");
    } else {
      this.updateStatus(StatusNode.Incomplete, "Select a data source");
    }
  }

  private getSourceType(): string {
    // Return your source type
    return 'custom_api';
  }

  private getConnectionString(): string {
    // Return connection configuration
    return '';
  }

  override execute() {
    // This method is called when the play button is clicked
    console.log('Executing custom input with config:', this.data());
  }
}
```

### Step 3: Create a Custom Output Node

Create a new file in `src/app/nodes/outputs/`:

```typescript
// filepath: src/app/nodes/outputs/my-custom-output.ts
import { ClassicPreset } from "rete";
import { AreaPlugin } from "rete-area-plugin";
import { FlatObjectSocket } from "src/app/core/sockets/sockets";
import { Schemes, AreaExtra } from "src/app/core/workflow-editor";
import { StatusNode } from "src/app/enums/status-node";
import { daavBlock } from "../node-block";
import { Node } from "src/app/models/interfaces/node";
import { OutputDataBlock } from "../output/output-data-block";

@daavBlock('output')
export class MyCustomOutput extends OutputDataBlock {
  override width = 350;
  override height = 200;

  constructor(
    label: string,
    area: AreaPlugin<Schemes, AreaExtra>,
    node?: Node
  ) {
    super(label, area, node);
    
    if (!node) {
      // Set initial status
      this.status = StatusNode.Incomplete;
      
      // Add inputs (outputs only have inputs)
      this.addInput(
        "input",
        new ClassicPreset.Input(new FlatObjectSocket(), "Data")
      );
    }
    
    // Add custom configuration if needed
    this.setupCustomConfiguration(node);
  }

  override getRevision(): string {
    // Return a revision string based on your configuration
    const data = this.data();
    return JSON.stringify({
      dataSource: data.selectDataSource?.value,
      config: data.config
    });
  }

  override data() {
    // Merge your custom data with parent data
    const customData = {
      config: {
        output_format: this.getOutputFormat(),
        destination_path: this.getDestinationPath()
      }
    };
    return { ...super.data(), ...customData };
  }

  private setupCustomConfiguration(node?: Node) {
    // Add custom controls/widgets here if needed
    this.validateConfiguration();
  }

  private validateConfiguration() {
    // Implement your validation logic
    const hasDataSource = this.data().selectDataSource?.value;
    
    if (hasDataSource) {
      this.updateStatus(StatusNode.Complete, "Output destination configured");
    } else {
      this.updateStatus(StatusNode.Incomplete, "Select output destination");
    }
  }

  private getOutputFormat(): string {
    // Return your output format
    return 'json';
  }

  private getDestinationPath(): string {
    // Return destination configuration
    return '';
  }

  override execute() {
    // This method is called when the play button is clicked
    console.log('Executing custom output with config:', this.data());
  }
}
```

## Required Files for a Custom Transform Node

**Backend** (`app/nodes/transforms/my_custom_transform.py`):
```python
from app.nodes.transforms.transform_node import TransformNode
from app.enums.status_node import StatusNode

class MyCustomTransform(TransformNode):
    def process(self, sample=False) -> StatusNode:
        # Your implementation here
        return StatusNode.Valid
```

**Frontend** (`src/app/nodes/transforms/my-custom-transform.ts`):
```typescript
import { TransformBlock } from "../transform/transform-block";
import { daavBlock } from "../node-block";

@daavBlock('transform')
export class MyCustomTransform extends TransformBlock {
    override getRevision(): string { return "1.0"; }
    override execute(): void { /* implementation */ }
}
```

**Export** (`src/app/nodes/index.ts`):
```typescript
export * from "./transforms/my-custom-transform";
```

### Common Import Statements

**Backend**:
```python
from typing import Optional, Any
import pandas as pd
from pydantic import ConfigDict
from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.utils.utils import generate_pandas_schema
```

**Frontend**:
```typescript
import { ClassicPreset } from "rete";
import { AreaPlugin } from "rete-area-plugin";
import { StatusNode } from "src/app/enums/status-node";
import { FlatObjectSocket } from "src/app/core/sockets/sockets";
import { Schemes, AreaExtra } from "src/app/core/workflow-editor";
import { Node } from "src/app/models/interfaces/node";
```

### Debugging Tips

1. **Backend Debugging**: Use `print()` statements or Python debugger in the `process()` method
2. **Frontend Debugging**: Use `console.log()` in browser developer tools
3. **Configuration Issues**: Check the `data()` method output in frontend and `self.data` content in backend
4. **Status Problems**: Verify status is set correctly using `StatusNode` enum values
5. **Connection Issues**: Ensure socket types match between connected nodes

## Testing Custom Nodes

### Writing Unit Tests

Create test files in the `tests/nodes/` directory following the existing pattern:

```python
# filepath: tests/nodes/transforms/test_my_custom_transform.py
import pytest
import pandas as pd
from app.nodes.transforms.my_custom_transform import MyCustomTransform
from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf
from app.utils.utils import generate_pandas_schema

class TestMyCustomTransform:
    def test_process_valid_data(self):
        """Test processing with valid input data."""
        # Create test data
        test_data = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35],
            'status': ['active', 'inactive', 'active']
        })
        
        # Create node with test configuration
        node_data = {
            'config': {
                'operation_type': 'filter',
                'filter_column': 'status',
                'filter_value': 'active'
            }
        }
        
        transform = MyCustomTransform(
            id="test_transform",
            data=node_data
        )
        
        # Set up input data
        input_data = NodeDataPandasDf(
            nodeSchema=generate_pandas_schema(test_data),
            data=test_data,
            dataExample=test_data.head(20),
            name="Test Data"
        )
        
        # Mock input connection
        transform.inputs['input'].set_node_data(input_data, transform)
        
        # Execute the transform
        result = transform.process(sample=False)
        
        # Verify results
        assert result == StatusNode.Valid
        output_data = transform.outputs['output'].get_node_data()
        assert len(output_data.data) == 2  # Only 'active' records
        
    def test_process_invalid_config(self):
        """Test processing with invalid configuration."""
        transform = MyCustomTransform(
            id="test_transform",
            data={'config': {}}  # Missing required config
        )
        
        result = transform.process(sample=False)
        assert result == StatusNode.Error
        assert "Missing required parameter" in transform.statusMessage
```

### Integration Testing

Test your nodes in the context of a complete workflow:

```python
def test_transform_in_workflow():
    """Test the transform as part of a complete workflow."""
    from app.core.workflow import Workflow
    from app.models.interface.workflow_interface import IProject
    
    # Create a simple workflow with your custom transform
    project_data = {
        "schema": {
            "nodes": [
                {
                    "id": "input_1",
                    "type": "ExampleInput",
                    "data": {}
                },
                {
                    "id": "transform_1", 
                    "type": "MyCustomTransform",
                    "data": {
                        "config": {
                            "operation_type": "filter",
                            "filter_column": "age",
                            "filter_value": 30
                        }
                    }
                }
            ],
            "connections": [
                {
                    "id": "conn_1",
                    "sourceNode": "input_1",
                    "sourcePort": "output",
                    "targetNode": "transform_1", 
                    "targetPort": "input"
                }
            ]
        }
    }
    
    # Execute the workflow
    workflow = Workflow()
    workflow.import_project(IProject(**project_data))
    result = workflow.execute()
    
    # Verify the workflow executed successfully
    assert result == StatusNode.Valid
```

## Best Practices

### 1. Follow Existing Architecture
- Always extend the appropriate base class (`InputDataBlock`, `OutputDataBlock`, `TransformBlock`)
- Use the `@daavBlock` decorator with the correct type
- Implement required abstract methods (`getRevision()`, `execute()`)

### 2. Configuration Management
- Store configuration in the `data()` method return object
- Support node restoration from existing configuration
- Validate configuration and update status accordingly

### 3. Status Management
- Set initial status in constructor (`StatusNode.Incomplete` for new nodes)
- Update status when configuration changes
- Provide meaningful status messages

### 4. Socket Usage
- Use appropriate socket types from `src/app/core/sockets/sockets`
- Follow input/output patterns from existing nodes
- Ensure socket compatibility between connected nodes

## Frontend/Backend Integration

### Synchronizing Node Types

When you create a custom node, you need to ensure both frontend and backend implementations use the same class names:

**Backend**: `MyCustomTransform` in `app/nodes/transforms/my_custom_transform.py`
**Frontend**: `MyCustomTransform` in `src/app/nodes/transforms/my-custom-transform.ts`

### Data Flow Between Frontend and Backend

The frontend node sends its configuration to the backend through the `data()` method:

```typescript
// Frontend - data() method returns configuration
override data() {
  return {
    config: {
      operation_type: this.operationType,
      filter_column: this.filterColumn
    },
    parquetSave: this.parquetCheckbox
  };
}
```

```python
# Backend - receives configuration through self.data
def process(self, sample=False) -> StatusNode:
    config = self.data.get('config', {})
    operation_type = config.get('operation_type')
    filter_column = config.get('filter_column')
    # ... process using configuration
```

### Status Synchronization

The backend node status is automatically synchronized to the frontend:

```python
# Backend - set status and messages
self.status = StatusNode.Error
self.statusMessage = "Configuration error"
self.errorStackTrace = ["Error details..."]
```

```typescript
// Frontend - status is automatically updated
this.updateStatus(StatusNode.Error, "Configuration error", ["Error details..."]);
```

This guide provides the information needed to create custom nodes for the DAAV platform, covering both backend and frontend implementations, configuration management, and best practices for development and testing.

## 📖 Navigation

- [← Back to main project](../README.md)
- [Docker deployment guide](../DOCKER_DEPLOYMENT.md)
- [Technical overview](OVERVIEW.md)
