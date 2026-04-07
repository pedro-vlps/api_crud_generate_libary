# CRUD Generator Libary

A libary created to Simplify your routine generating a Full CRUD API based on database models and schemas

## Routes

- Get All:
  - Paginated Response(Parameters sent on URL)
  - Joined Response(Parameters configurated on SqlRouter declaration)
  - Sorted Response(Parameters sent on URL)
  - Response example
    ```python
    {
        "data": [
            {
                "id": "39a0b280-c32c-4983-a85d-8e5f42cb021b",
                "name": "Join Teste 1",
                "join_teste": {
                    "id": "798cad10-2aec-4ce6-97be-dc29a5b85074",
                    "name": "Teste 1",
                    "teste": {
                        "id": "798cad10-2aec-4ce6-97be-dc29a5b85073",
                        "name": "Administrador"
                    }
                }
            },
            {
                "id": "29550134-24af-4fd6-b5d8-8dcc7ac15903",
                "name": "Join Teste 2",
                "join_teste": {
                        "id": "63e9fee5-5c3a-4823-ab32-2e9dbc9b049c",
                        "name": "Teste 2",
                        "teste": {
                            "id": "63e9fee5-5c3a-4823-ab32-2e9dbc9b049b",
                            "name": "Supervisor"
                        }
                }
            }
        ],
        "total_count": 3,
        "has_more": true
    }
    ```

- Get By Id:
  - Joined Response(Parameters configurated on SqlRouter declaration)
  - Response example
    ```python
    {
        "data": {
            "id": "39a0b280-c32c-4983-a85d-8e5f42cb021b",
            "name": "Join Teste 1",
            "join_teste": {
                "id": "798cad10-2aec-4ce6-97be-dc29a5b85074",
                "name": "Teste 1",
                "teste": {
                    "id": "798cad10-2aec-4ce6-97be-dc29a5b85073",
                    "name": "Administrador"
                }
            }
        }
    }
    ```
- Post:
    - Standard creation schema based
    - Body validation schema based
    - Integrity, Unique and String Length errors validation
- Patch:
    - Standard update schema based
    - Partial update route schema based
    - Body validation schema based
    - Integrity, Unique and String Length errors validation
- Delete:
    - Standard delete one
    - Integrity and Not Found error validation


## Requirements

- Python: >=3.13
- Schema Format:

  ```python
  from typing import Optional
  from uuid import UUID
  from pydantic import BaseModel as SCBaseModel

  class ExampleSchema(SCBaseModel):
      id: Optional[UUID] = None # Recommended standard format
      name: str

      class Config:
          from_attributes = True
          json_schema_extra = { # Required
              "example": {
                  "id": "550e8400-e29b-41d4-a716-446655440000",
                  "name": "John Doe"
              }
          }

  ```

## Instalation

```bash
poetry add git+
```

## Parameters

```python
SqlRouter(
    model_class=ExampleModel, # Table Model - Required
    standard_schema=ExampleSchema, # Table pattern schema - Required
    db_session=db_callback # Callback to create a connection with database - Required
    auth_callback=true_function, # Validate JWT token function field - Optional
    request_post_schema=ReqExampleSchemaPost, # Request POST Schema - Optional
    request_patch_schema=ReqExampleSchemaUpdate, # Request PUT Schema - Optional
    response_get_schema=ExampleSchemaGet, # Response GET All Schema - Optional
    response_get_id_schema=ExampleSchemaGet, # Response GET by ID Schema - Optional
    response_post_schema=ExampleSchemaPost, # Response POST Schema - Optional
    response_delete_schema= ExampleSchemaDelete, # Response DELETE Schema - Optional
    response_patch_schema=ExampleSchemaUpdate, # Response PUT Schema - Optional
    enable_get=True, # Enable/Disable GET All route - Optional
    use_get_overview=False # Enable/Disable GET ALL route created for overview - Optional
    enable_get_by_id=True # Enable/Disable GET by ID route - Optional
    enable_post=True, # Enable/Disable POST route - Optional
    enable_delete=True, # Enable/Disable DELETE route - Optional
    use_patch=True, # Enable/Disable PUT route - Optional
    join_parameters=[ # Parameters for a simple join on model_class - Optional
        {
            "model": JoinTesteModel, # Model where the ForeignKey belongs
            "column": "join_teste_id", # Column name of the ForeignKey
            "response_parameter": JoinJoinTesteModel.join_teste # relatioship name on model_class
        },
    ],
    second_level_join_parameters=[ # Parameters for a chained join on ForeignKeys of model_class - Optional
        {
            "first_model": JoinTesteModel, # model_class ForeignKey model
            "second_model": TesteModel, # first_model ForeignKey model
            "column": "teste_id", # first_model ForeignKey column name
            "response_parameter": [ # relationship name path from model_class
                JoinJoinTesteModel.join_teste, # model_class relatioship name
                JoinTesteModel.teste # first_model relatioship name
            ]
        }
    ]
)
```
