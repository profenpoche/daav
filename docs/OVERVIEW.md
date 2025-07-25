# DAAV - Data Alignment, Aggregation and Vectorisation Platform

## Overview

DAAV is a comprehensive data processing and analysis platform consisting of two main components: a Python backend API and a frontend application. The platform enables users to create data transformation pipelines through an interconnected node system.

## Architecture

### Backend API (`/backendApi`)
- **Framework**: FastAPI with Python
- **Database**: Support for various data sources
- **Processing**: Pandas and PyArrow for data manipulation
- **Architecture**: Modular node system for data processing

### Frontend (`/frontendApp`)
- User interface for creating and managing data pipelines
- Visualization of analysis results

## Core Components

### 1. Node System (`app/nodes/`)

The platform's core is built on a modular node system:

#### Transform Nodes (`transforms/`)
- **MergeTransform**: Merges columns from different data sources
- **FlattenTransform**: Flattens nested JSON structures
- **TransformNode**: Base class for all transformation nodes

#### Node Features
- **Inputs/Outputs**: Each node can have multiple inputs and outputs
- **State Management**: Execution status tracking (Valid, Error, Processing)
- **Batch Processing**: Support for large Parquet files

### 2. Data Management (`app/models/interface/`)

#### Supported Data Types
- **NodeDataPandasDf**: Pandas DataFrames for in-memory processing
- **NodeDataParquet**: Parquet files for large volume data
- **Schemas**: Automatic schema generation for validation and documentation

#### Data Sources
- Parquet files
- Pandas DataFrames
- External APIs
- Databases

### 3. Specialized Transformations

#### MergeTransform
- **Purpose**: Merge columns from different datasets
- **Configuration**: Flexible mapping between sources and target columns
- **Optimization**: Batch processing for large volumes
- **Use Cases**: Data consolidation from multiple sources

#### FlattenTransform
- **Purpose**: Flatten complex JSON structures
- **Features**:
  - Array explosion into multiple rows
  - Nested structure flattening
  - Parent-child relationship preservation
- **Use Cases**: JSON data normalization for analysis

### 4. Enumerations and States (`app/enums/`)
- **StatusNode**: Node states (Valid, Error, Processing, etc.)
- Consistent state management across the platform

### 5. Utilities (`app/utils/`)
- **Schema Generation**: Automatic Pandas schema creation
- **Validation**: Data integrity checks
- **Optimizations**: Performance helper functions

## Processing Flow

1. **Configuration**: Define nodes and their connections
2. **Validation**: Pipeline consistency verification
3. **Execution**: Sequential node processing
4. **Monitoring**: Real-time execution state tracking
5. **Results**: Data export and visualization

## Technical Features

### Performance
- **Batch Processing**: Large volume optimization with Parquet
- **Memory Management**: Efficient handling with streaming support
- **Parallelization**: Architecture ready for concurrent processing

### Robustness
- **Error Handling**: Detailed exception capture and reporting
- **Validation**: Strict controls with Pydantic
- **Testing**: Comprehensive test suite for all components

### Extensibility
- **Modular Architecture**: Easy addition of new node types
- **Standardized Interface**: Consistent contracts between components
- **Flexible Configuration**: Data structure-based parameterization

## Use Cases

1. **ETL Pipelines**: Extract, Transform, Load for data integration
2. **Data Cleaning**: Dataset cleaning and normalization
3. **Data Integration**: Merging heterogeneous data sources
4. **Analytics Preparation**: Data preparation for analysis
5. **JSON Processing**: Semi-structured data processing

## Technologies Used

### Backend
- **Python 3.10+**
- **FastAPI**: Modern, high-performance web framework
- **Pandas**: Data manipulation
- **PyArrow/Parquet**: High-performance storage and processing
- **Pydantic**: Data validation and serialization
- **Pytest**: Testing framework

### Data Management
- **Apache Arrow**: In-memory data format
- **Parquet**: Columnar storage format
- **JSON**: Flexible data structures

## Project Structure

```
daav/
├── backendApi/          # Backend API
│   ├── app/
│   │   ├── nodes/       # Node system
│   │   ├── models/      # Data models
│   │   ├── enums/       # Enumerations
│   │   └── utils/       # Utilities
│   └── tests/           # Automated tests
├── frontendApp/         # User interface
└── docs/               # Documentation
```

## Key Design Principles

### Modularity
- **Composable Nodes**: Each transformation is a self-contained, reusable component
- **Plug-and-Play**: Easy integration of new transformation types
- **Separation of Concerns**: Clear boundaries between data processing, validation, and presentation

### Scalability
- **Memory Efficiency**: Streaming processing for large datasets
- **Format Optimization**: Parquet for columnar data storage and fast querying
- **Incremental Processing**: Support for processing data in chunks

### Reliability
- **Type Safety**: Pydantic models ensure data integrity
- **Error Recovery**: Graceful handling of processing failures
- **State Tracking**: Comprehensive monitoring of pipeline execution

## Data Flow Architecture

```
Input Sources → Transform Nodes → Output Destinations
     ↓              ↓                    ↓
[Parquet Files] [MergeTransform]    [Processed Data]
[DataFrames]    [FlattenTransform]  [Visualizations]
[JSON APIs]     [Custom Nodes]     [Export Files]
```

## Future Roadmap

- **Visual Pipeline Editor**: Drag-and-drop interface for pipeline creation
- **Enhanced Connectors**: Integration with more data sources (databases, cloud services)
- **Advanced Monitoring**: Performance metrics and pipeline optimization suggestions
- **Cloud Deployment**: Container-based deployment for scalable processing
- **Real-time Processing**: Stream processing capabilities for live data
- **Machine Learning Integration**: Built-in ML model training and inference nodes

## Getting Started

1. **Installation**: Set up the backend API and frontend application
2. **Configuration**: Define your data sources and transformation requirements
3. **Pipeline Creation**: Build your data processing pipeline using available nodes
4. **Execution**: Run the pipeline and monitor progress
5. **Analysis**: Explore and visualize the processed results

DAAV represents a modern, extensible solution for data processing that combines ease of use with high performance to meet contemporary data analysis needs. The platform's modular architecture ensures it can grow and adapt to evolving data processing requirements while maintaining reliability and performance.

## 📖 Navigation

- [← Back to main project](../README.md)
- [Docker deployment guide](../DOCKER_DEPLOYMENT.md)
- [Plugin development guide](PLUGGINS.md)