import os
import re


def to_snake_case(name):
    """Convert CamelCase to snake_case"""
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def to_camel_case(name):
    """Convert snake_case to CamelCase"""
    return ''.join(word.title() for word in name.split('_'))


def get_field_type(field_name, field_type):
    """Map field types to Python/Pydantic types"""
    type_mapping = {
        'str': 'str',
        'string': 'str',
        'int': 'int',
        'integer': 'int',
        'float': 'float',
        'bool': 'bool',
        'boolean': 'bool',
        'dt': 'datetime',
        'datetime': 'datetime',
        'email': 'EmailStr',
        'uuid': 'str',
        'ops': 'Optional[str]',
        'lstr': 'List[str]',
        'optstr': 'Optional[str]',
        'optional_string': 'Optional[str]',
        'optint': 'Optional[int]',
        'optional_integer': 'Optional[int]',
        'optfloat': 'Optional[float]',
        'optional_float': 'Optional[float]',
        'optbool': 'Optional[bool]',
        'optional_boolean': 'Optional[bool]',
        'optdt': 'Optional[datetime]',
        'optional_datetime': 'Optional[datetime]'
    }
    return type_mapping.get(field_type, 'str')


def get_field_default(field_name, field_type):
    """Get appropriate default value for field"""
    if field_type.startswith('opt') or field_type.startswith('ops'):
        return "None"
    elif field_type == 'bool' or field_type == 'boolean':
        return "False"
    elif field_type == 'int' or field_type == 'integer':
        return "0"
    elif field_type == 'float':
        return "0.0"
    elif field_type == 'str' or field_type == 'string':
        return '""'
    elif field_type == 'lstr':
        return "[]"
    return None


def create_model_structure():
    print("🚀 Automated Model, Schema & Router Generator")
    print("=" * 50)

    # Model information input
    model_name = input("📝 Enter model name (e.g., User, Product, Category): ").strip()
    if not model_name:
        print("❌ Model name is required!")
        return

    collection_name = input(f"📁 Enter MongoDB collection name (default: {to_snake_case(model_name)}s): ").strip()
    if not collection_name:
        collection_name = f"{to_snake_case(model_name)}s"

    print("\n📋 Now enter field definitions (enter 'done' when finished):")
    print("Available field types (shortcuts):")
    print("  str, int, float, bool, dt, email, uuid, lstr (List[str])")
    print("  ops (optional string), optint (optional int), optfloat (optional float)")
    print("  optbool (optional bool), optdt (optional datetime)")
    print("💡 Field type defaults to 'str' if skipped")
    print("\n💡 Note: ID, created_at, updated_at will be added automatically!")

    fields = []
    while True:
        print(f"\nField #{len(fields) + 1}:")
        field_name = input("  Field name: ").strip()

        if field_name.lower() == 'done':
            break

        if not field_name:
            continue

        field_type = input("  Field type (default: str): ").strip().lower()
        if not field_type:
            field_type = 'str'

        python_type = get_field_type(field_name, field_type)
        default_value = get_field_default(field_name, field_type)

        fields.append({
            'name': field_name,
            'type': python_type,
            'default': default_value,
            'is_optional': field_type.startswith('opt') or field_type.startswith('ops'),
            'original_type': field_type
        })

    # Main folder creation
    main_folder = f"{to_snake_case(model_name)}"
    os.makedirs(main_folder, exist_ok=True)

    # Subfolders creation
    folder_names = ["models", "schemas", "routers"]
    for folder in folder_names:
        folder_path = os.path.join(main_folder, folder)
        os.makedirs(folder_path, exist_ok=True)
        # Create __init__.py in each subfolder
        with open(os.path.join(folder_path, "__init__.py"), "w", encoding='utf-8') as f:
            f.write('')

    # Create __init__.py in main folder
    with open(os.path.join(main_folder, "__init__.py"), "w", encoding='utf-8') as f:
        f.write('')

    # Create files
    create_model_file(main_folder, model_name, collection_name, fields)
    create_schema_files(main_folder, model_name, fields)
    create_router_file(main_folder, model_name, fields)


    print(f"\n✅ Successfully created '{main_folder}' structure!")
    print(f"📁 Folders created: models, schemas, routers")
    print(f"📄 Files created:")
    print(f"   - models/{to_snake_case(model_name)}_model.py")
    print(f"   - schemas/{to_snake_case(model_name)}_schemas.py")
    print(f"   - routers/{to_snake_case(model_name)}_routes.py")
    print(f"   - __init__.py (in all folders)")
    print(f"\n🎉 Your {model_name} API is ready to use!")


def create_model_file(main_folder, model_name, collection_name, fields):
    """Create the model file"""
    snake_name = to_snake_case(model_name)

    imports = {
        'from beanie import Document, before_event, Replace, Save',
        'from pydantic import Field',
        'from typing import Optional',
        'from datetime import datetime, timezone',
        'import uuid'
    }

    field_definitions = []

    # Auto-add ID field
    field_definitions.append('    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")')

    # Add user-defined fields
    for field in fields:
        if field['default']:
            field_definitions.append(f"    {field['name']}: {field['type']} = {field['default']}")
        else:
            field_definitions.append(f"    {field['name']}: {field['type']}")

    # Auto-add timestamp fields
    field_definitions.append('    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))')
    field_definitions.append('    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))')

    # Remove Optional import if not needed
    if not any('Optional' in field['type'] for field in fields):
        imports.discard('from typing import Optional')

    imports_list = sorted(list(imports))

    model_content = f'''{chr(10).join(imports_list)}


class {model_name}Model(Document):
{chr(10).join(field_definitions)}

    # Auto-update "updated_at" on update
    @before_event([Save, Replace])
    def update_timestamp(self):
        self.updated_at = datetime.now(timezone.utc)

    class Settings:
        name = "{collection_name}"
'''

    with open(os.path.join(main_folder, "models", f"{snake_name}_model.py"), "w", encoding='utf-8') as f:
        f.write(model_content)


def create_schema_files(main_folder, model_name, fields):
    """Create schema files"""
    snake_name = to_snake_case(model_name)
    camel_name = to_camel_case(model_name)

    # Create schema (only user-defined fields)
    create_fields = [f"    {field['name']}: {field['type']}" for field in fields]
    create_fields_str = chr(10).join(create_fields)

    # Update schema (all user fields optional)
    update_fields = []
    for field in fields:
        base_type = field['type'].replace('Optional[', '').replace(']', '')
        update_fields.append(f"    {field['name']}: Optional[{base_type}] = None")

    update_fields_str = chr(10).join(update_fields)

    # Response schema (include auto fields + user fields)
    response_fields = [
        '    id: str',
        *[f"    {field['name']}: {field['type']}" for field in fields],
        '    created_at: datetime',
        '    updated_at: datetime'
    ]
    response_fields_str = chr(10).join(response_fields)

    schema_content = f'''from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Schema for creating new {model_name}
class {camel_name}Create(BaseModel):
{create_fields_str}

# Schema for updating {model_name}
class {camel_name}Update(BaseModel):
{update_fields_str}

# Schema for {model_name} response
class {camel_name}Response(BaseModel):
{response_fields_str}

    class Config:
        from_attributes = True
'''

    with open(os.path.join(main_folder, "schemas", f"{snake_name}_schemas.py"), "w", encoding='utf-8') as f:
        f.write(schema_content)


def create_router_file(main_folder, model_name, fields):
    """Create router file with CRUD operations"""
    snake_name = to_snake_case(model_name)
    camel_name = to_camel_case(model_name)

    # Use chr(10) for newlines instead of \n in f-strings
    router_content = f'''from fastapi import APIRouter, HTTPException,status
from typing import List
from models.{snake_name}_model import {model_name}Model
from schemas.{snake_name}_schemas import {camel_name}Create, {camel_name}Update, {camel_name}Response

router = APIRouter(prefix="/{snake_name}s", tags=["{snake_name}s"])

# GET all {snake_name}s
@router.get("/", response_model=List[{camel_name}Response],status_code=status.HTTP_200_OK)
async def get_all_{snake_name}s(skip: int = 0, limit: int = 10):
    {chr(10)}    {chr(34)}{chr(34)}{chr(34)}
    Get all {snake_name}s with pagination
    {chr(34)}{chr(34)}{chr(34)}
    {snake_name}s = await {model_name}Model.find_all().skip(skip).limit(limit).to_list()
    return {snake_name}s

# GET {snake_name} by ID
@router.get("/{{{snake_name}_id}}", response_model={camel_name}Response,status_code=status.HTTP_200_OK)
async def get_{snake_name}({snake_name}_id: str):
    {chr(10)}    {chr(34)}{chr(34)}{chr(34)}
    Get {snake_name} by ID
    {chr(34)}{chr(34)}{chr(34)}
    {snake_name} = await {model_name}Model.get({snake_name}_id)
    if not {snake_name}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{model_name} not found")
    return {snake_name}

# POST create new {snake_name}
@router.post("/", response_model={camel_name}Response,status_code=status.HTTP_201_CREATED)
async def create_{snake_name}({snake_name}_data: {camel_name}Create):
    {chr(10)}    {chr(34)}{chr(34)}{chr(34)}
    Create a new {snake_name}
    {chr(34)}{chr(34)}{chr(34)}
    {snake_name}_dict = {snake_name}_data.model_dump()
    {snake_name} = {model_name}Model(**{snake_name}_dict)
    await {snake_name}.create()
    return {snake_name}

# PATCH update {snake_name}
@router.patch("/{{{snake_name}_id}}", response_model={camel_name}Response,status_code=status.HTTP_200_OK)
async def update_{snake_name}({snake_name}_id: str, {snake_name}_data: {camel_name}Update):
    {chr(10)}    {chr(34)}{chr(34)}{chr(34)}
    Update {snake_name} information
    {chr(34)}{chr(34)}{chr(34)}
    {snake_name} = await {model_name}Model.get({snake_name}_id)
    if not {snake_name}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{model_name} not found")

    update_data = {snake_name}_data.model_dump(exclude_unset=True)
    await {snake_name}.update({{"$set": update_data}})
    return await {model_name}Model.get({snake_name}_id)

# DELETE {snake_name}
@router.delete("/{{{snake_name}_id}}",status_code=status.HTTP_200_OK)
async def delete_{snake_name}({snake_name}_id: str):
    {chr(10)}    {chr(34)}{chr(34)}{chr(34)}
    Delete {snake_name} by ID
    {chr(34)}{chr(34)}{chr(34)}
    {snake_name} = await {model_name}Model.get({snake_name}_id)
    if not {snake_name}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{model_name} not found")

    await {snake_name}.delete()
    return {{"message": "{model_name} deleted successfully"}}
'''

    with open(os.path.join(main_folder, "routers", f"{snake_name}_routes.py"), "w", encoding='utf-8') as f:
        f.write(router_content)





if __name__ == "__main__":
    create_model_structure()